import os, time
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import DocumentAttributeVideo
from database import init_db, is_duplicate, save_history
from utils import get_video_info, download_file
from api_handler import get_drama_data

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def cleanup_files(files):
    """Fungsi bersih-bersih file sampah"""
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def gas_download(platform, drama_id):
    # Ambil Data dari API (Sekarang udah pinter, ada Metadata)
    data = get_drama_data(platform, drama_id)
    if not data or not data['episodes']:
        print("❌ Data tidak ditemukan atau Episode kosong!")
        return

    # Ambil Info Drama
    title = data['title']
    poster = data['poster']
    desc = data['desc']
    total_eps = data.get('total_eps', len(data['episodes']))
    
    # Bersihin Judul dari karakter aneh buat nama file
    safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip()
    
    print(f"\n🎬 MEMPROSES: {title}")
    print(f"📊 Total: {total_eps} Episode")

    # ======================================================
    # 1. SETUP FOLDER TOPIC (Biar Rapi per Drama)
    # ======================================================
    topic_id = None
    is_new_topic = False
    
    try:
        # Cari topik lama dulu
        r = client(functions.channels.GetForumTopicsRequest(channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100))
        for t in r.topics:
            if hasattr(t, 'title') and t.title.strip() == title.strip():
                topic_id = t.id
                print(f"📂 Masuk ke Folder Lama: {title}")
                break
    except: pass

    if not topic_id:
        try:
            # Bikin topik baru
            result = client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
            print(f"📂 Bikin Folder Baru: {title}")
        except Exception as e:
            print(f"❌ Gagal bikin folder: {e}"); return

    # ======================================================
    # 2. KIRIM POSTER UTAMA (PINNED MESSAGE)
    # ======================================================
    if is_new_topic:
        # Template Caption Sultan
        caption_poster = (
            f"📽️ **{title}**\n"
            f"──────────────────\n\n"
            f"📚 **SINOPSIS**\n"
            f"_{desc}_\n\n"
            f"🏷️ **Genre:** Drama, Romance\n"
            f"🆔 **ID:** `{drama_id}`\n"
            f"📊 **Total:** {total_eps} Episode\n"
            f"🚀 **Platform:** #{platform.upper()}"
        )
        try:
            if poster and "http" in poster:
                # Download poster dulu biar bisa dikirim sebagai foto
                poster_file = "poster.jpg"
                download_file(poster, poster_file)
                msg = client.send_file(GROUP_ID, poster_file, caption=caption_poster, reply_to=topic_id)
                os.remove(poster_file)
            else:
                msg = client.send_message(GROUP_ID, caption_poster, reply_to=topic_id)
            
            # Pin pesan ini biar user gampang baca sinopsis
            client.pin_message(GROUP_ID, msg.id, notify=True)
        except Exception as e:
            print(f"⚠️ Gagal kirim poster: {e}")

    # ======================================================
    # 3. PROSES BATCH DOWNLOAD & MERGE
    # ======================================================
    batch_size = 10
    all_eps = data['episodes']
    
    for i in range(0, len(all_eps), batch_size):
        batch = all_eps[i:i + batch_size]
        start_num = i + 1
        end_num = i + len(batch)
        
        # Label Batch: "Eps 01-10"
        batch_label = f"Eps {start_num:02d}-{end_num:02d}"
        history_key = f"{title} {batch_label}"
        
        # Cek Database biar gak re-upload
        if is_duplicate(platform, drama_id, history_key):
            print(f"⏭️ SKIP: {batch_label} (Udah ada)")
            continue

        print(f"📦 Mengolah {batch_label}...")
        temp_files = []
        
        # Nama file output yang GANTENG
        # Contoh: Guru Surgawi - Eps 01-10.mp4
        output_file = f"{safe_title} - {batch_label}.mp4"
        
        try:
            # --- STEP A: DOWNLOAD ---
            for idx, ep in enumerate(batch, start=start_num):
                v_url = None
                
                # Logika Pencari Link (CDN Hunter)
                cdn_data = ep.get('cdnList')
                if cdn_data and isinstance(cdn_data, list) and len(cdn_data) > 0:
                    provider = cdn_data[0]
                    v_list = provider.get('videoPathList')
                    if v_list and isinstance(v_list, list):
                        for vid in v_list:
                            if vid.get('quality') == 720: # Cari 720p
                                v_url = vid.get('videoPath')
                                break
                        if not v_url and len(v_list) > 0: v_url = v_list[0].get('videoPath')

                if not v_url: # Cadangan
                    v_url = (ep.get('url') or ep.get('videoUrl') or ep.get('playUrl') or ep.get('link') or ep.get('downloadUrl'))

                if v_url:
                    fn = f"temp_{idx}.mp4"
                    print(f"   ⬇️ Download Part {idx}...")
                    download_file(v_url, fn)
                    temp_files.append(fn)

            if not temp_files:
                print("   ❌ Gagal download batch ini (Kosong).")
                continue

            # --- STEP B: MERGE (FFMPEG) ---
            with open("list.txt", "w") as f:
                for tf in temp_files: f.write(f"file '{tf}'\n")
            
            print(f"   🔗 Menggabungkan {len(temp_files)} video...")
            # Quiet mode (-v quiet) biar terminal gak berisik, stats biar tetep ada progress
            os.system(f"ffmpeg -f concat -safe 0 -i list.txt -c copy -v quiet -stats \"{output_file}\" -y")

            # --- STEP C: UPLOAD KE TELEGRAM ---
            if os.path.exists(output_file):
                print(f"   🚀 Uploading {output_file}...")
                
                # Ambil info durasi & resolusi buat thumbnail bar
                w, h, dur = get_video_info(output_file)
                
                # Caption Video Estetik
                caption_video = (
                    f"🎬 **{title}**\n"
                    f"📼 **{batch_label}**\n"
                    f"──────────────────\n"
                    f"⚙️ **Res:** {w}x{h} px\n"
                    f"⏱️ **Dur:** {dur // 60} Menit\n"
                    f"✨ *Selamat Menonton!*"
                )

                # Kirim Video
                client.send_file(
                    GROUP_ID, 
                    output_file, 
                    caption=caption_video,
                    reply_to=topic_id,
                    supports_streaming=True,
                    # Pake poster drama sebagai thumbnail video (biar cakep di list chat)
                    thumb=poster_file if os.path.exists("poster.jpg") else None, 
                    attributes=[DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)]
                )
                
                save_history(platform, drama_id, history_key)
                print(f"   ✅ Selesai: {batch_label}")

        except Exception as e:
            print(f"   ⚠️ Error Batch {batch_label}: {e}")
        
        finally:
            # Bersih-bersih
            cleanup_files(temp_files + ["list.txt", output_file])
            
        time.sleep(2)

if __name__ == "__main__":
    init_db()
    p = input("\n📡 Platform (dramabox/netshort): ")
    i = input("🆔 ID Drama: ")
    if p and i: gas_download(p, i)
