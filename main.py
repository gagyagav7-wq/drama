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
    """Bersih-bersih file sementara"""
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def gas_download(platform, drama_id):
    # 1. AMBIL DATA
    data = get_drama_data(platform, drama_id)
    if not data or not data['episodes']:
        print("❌ Data error atau Episode kosong!")
        return

    # Ambil Info Lengkap
    title = data['title']
    poster_url = data['poster'] # URL Poster
    desc = data['desc']
    tags = data['tags'] # Genre
    total_eps = data.get('total_eps', len(data['episodes']))
    
    # Nama aman buat file
    safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip()
    
    print(f"\n🎬 MEMPROSES: {title}")
    print(f"🏷️ Genre: {tags}")
    print(f"📊 Total: {total_eps} Episode")

    # 2. DOWNLOAD POSTER (Sekali di awal, dipake terus)
    poster_path = "poster.jpg"
    has_poster = False
    if poster_url and "http" in poster_url:
        try:
            download_file(poster_url, poster_path)
            has_poster = True
        except:
            print("⚠️ Gagal download poster (lanjut tanpa thumbnail)")

    # 3. SETUP FOLDER TOPIC
    topic_id = None
    is_new_topic = False
    
    try:
        r = client(functions.channels.GetForumTopicsRequest(channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100))
        for t in r.topics:
            if hasattr(t, 'title') and t.title.strip() == title.strip():
                topic_id = t.id
                print(f"📂 Masuk ke Folder Lama: {title}")
                break
    except: pass

    if not topic_id:
        try:
            result = client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
            print(f"📂 Bikin Folder Baru: {title}")
        except Exception as e:
            print(f"❌ Gagal bikin folder: {e}"); return

    # 4. KIRIM PINNED MESSAGE (Cuma kalau folder baru)
    if is_new_topic:
        caption_poster = (
            f"📽️ **{title}**\n"
            f"──────────────────\n\n"
            f"📚 **SINOPSIS**\n"
            f"_{desc}_\n\n"
            f"🏷️ **Genre:** {tags}\n"
            f"📊 **Total:** {total_eps} Episode\n"
            f"🚀 **Platform:** #{platform.upper()}"
        )
        try:
            if has_poster:
                msg = client.send_file(GROUP_ID, poster_path, caption=caption_poster, reply_to=topic_id)
            else:
                msg = client.send_message(GROUP_ID, caption_poster, reply_to=topic_id)
            
            client.pin_message(GROUP_ID, msg.id, notify=True)
        except Exception as e: 
            print(f"⚠️ Gagal kirim pinned message: {e}")

    # 5. PROSES BATCH DOWNLOAD (50 EPS)
    all_eps = data['episodes']
    batch_size = len(all_eps) 
    
    try:
        for i in range(0, len(all_eps), batch_size):
            batch = all_eps[i:i + batch_size]
            start_num = i + 1
            end_num = i + len(batch)
            
            batch_label = f"Eps {start_num:02d}-{end_num:02d}"
            history_key = f"{title} {batch_label}"
            
            if is_duplicate(platform, drama_id, history_key):
                print(f"⏭️ SKIP: {batch_label} (Udah ada)")
                continue

            print(f"📦 Mengolah {batch_label}...")
            temp_files = []
            output_file = f"{safe_title} - {batch_label}.mp4"
            
            try:
                # --- STEP A: DOWNLOAD PER PART ---
                for idx, ep in enumerate(batch, start=start_num):
                    v_url = None
                    # Logika CDN Hunter (Dramabox)
                    cdn_data = ep.get('cdnList')
                    if cdn_data and isinstance(cdn_data, list) and len(cdn_data) > 0:
                        provider = cdn_data[0]
                        v_list = provider.get('videoPathList')
                        if v_list and isinstance(v_list, list):
                            for vid in v_list:
                                if vid.get('quality') == 720: 
                                    v_url = vid.get('videoPath'); break
                            if not v_url and len(v_list) > 0: v_url = v_list[0].get('videoPath')

                    # Logika Umum
                    if not v_url: 
                        v_url = (ep.get('url') or ep.get('videoUrl') or ep.get('playUrl') or ep.get('link') or ep.get('downloadUrl'))

                    if v_url:
                        fn = f"temp_{idx}.mp4"
                        print(f"   ⬇️ Part {idx}...")
                        download_file(v_url, fn)
                        temp_files.append(fn)

                if not temp_files:
                    print("   ❌ Gagal download batch ini.")
                    continue

                # --- STEP B: MERGE ---
                with open("list.txt", "w") as f:
                    for tf in temp_files: f.write(f"file '{tf}'\n")
                
                print(f"   🔗 Menggabungkan {len(temp_files)} video...")
                os.system(f"ffmpeg -f concat -safe 0 -i list.txt -c copy -v quiet -stats \"{output_file}\" -y")

                # --- STEP C: UPLOAD ---
                if os.path.exists(output_file):
                    print(f"   🚀 Uploading {output_file}...")
                    w, h, dur = get_video_info(output_file)
                    
                    caption_video = (
                        f"🎬 **{title}**\n"
                        f"📼 **{batch_label}**\n"
                        f"──────────────────\n"
                        f"⚙️ **Res:** {w}x{h} px\n"
                        f"⏱️ **Dur:** {dur // 60} Menit\n"
                        f"✨ *Selamat Menonton!*"
                    )

                    # Kunci Fix Thumbnail: Pake poster_path yang udah didownload di awal
                    thumb_to_use = poster_path if has_poster and os.path.exists(poster_path) else None

                    client.send_file(
                        GROUP_ID, 
                        output_file, 
                        caption=caption_video,
                        reply_to=topic_id,
                        supports_streaming=True,
                        thumb=thumb_to_use, 
                        attributes=[DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)]
                    )
                    
                    save_history(platform, drama_id, history_key)
                    print(f"   ✅ Selesai: {batch_label}")

            except Exception as e:
                print(f"   ⚠️ Error Batch {batch_label}: {e}")
            
            finally:
                # Hapus file video sementara, TAPI JANGAN hapus poster.jpg dulu
                cleanup_files(temp_files + ["list.txt", output_file])
                time.sleep(2)
    
    finally:
        # Hapus poster pas SEMUA batch udah kelar
        if has_poster and os.path.exists(poster_path):
            os.remove(poster_path)

if __name__ == "__main__":
    init_db()
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "═"*35)
    print("   🔥 DRAMA DOWNLOADER BOT V2 🔥")
    print("═"*35)
    print("  [1] 📦 DRAMABOX")
    print("  [2] 🎬 NETSHORT")
    print("  [3] 🎞️ FLICKREELS")
    print("═"*35)
    
    choice = input("👉 Pilih Nomor (1-3): ").strip()
    platform_map = {'1': 'dramabox', '2': 'netshort', '3': 'flickreels'}
    selected_platform = platform_map.get(choice)
    
    if not selected_platform:
        print("\n❌ Salah pilih Cok!"); exit()
        
    print(f"✅ Mode: {selected_platform.upper()}")
    print("-" * 35)
    drama_id = input("🆔 Masukkan ID / Slug Drama: ").strip()
    
    if drama_id: gas_download(selected_platform, drama_id)
    else: print("❌ ID kosong!")
    
