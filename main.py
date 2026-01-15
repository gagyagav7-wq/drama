import os, time
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import DocumentAttributeVideo
from database import init_db, is_duplicate, save_history
from utils import get_video_info, download_file
from api_handler import get_drama_data

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def gas_download(platform, drama_id):
    data = get_drama_data(platform, drama_id)
    if not data or not data['episodes']:
        print("❌ Data tidak ditemukan!")
        return

    title = data['title'] or f"Drama_{drama_id}"
    print(f"🎬 MEMPROSES: {title}")

    # 1. CARI/BIKIN FOLDER (TOPIC)
    topic_id = None
    is_new_topic = False
    try:
        r = client(functions.channels.GetForumTopicsRequest(channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100))
        for t in r.topics:
            if hasattr(t, 'title') and t.title.strip() == title.strip():
                topic_id = t.id
                break
    except: pass

    if not topic_id:
        try:
            result = client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
        except Exception as e:
            print(f"❌ Gagal bikin folder: {e}"); return

    # 2. KIRIM POSTER & SINOPSIS (AUTO PIN)
    if is_new_topic:
        cap = f"🎬 **{title}**\n\n📝 **Sinopsis:**\n{data['desc']}\n\n📊 **Total: {data.get('total_eps', len(data['episodes']))} Episode**\n🚀 #Platform_{platform.upper()}"
        try:
            if data['poster']:
                msg = client.send_file(GROUP_ID, data['poster'], caption=cap, reply_to=topic_id)
            else:
                msg = client.send_message(GROUP_ID, cap, reply_to=topic_id)
            client.pin_message(GROUP_ID, msg.id)
        except: pass

    # 3. PROSES BATCH UPLOAD (Setiap 10 Episode)
    batch_size = 10
    all_eps = data['episodes']
    
    for i in range(0, len(all_eps), batch_size):
        batch = all_eps[i:i + batch_size]
        start_num = i + 1
        end_num = i + len(batch)
        batch_label = f"Eps {start_num:02d}-{end_num:02d}"
        
        if is_duplicate(platform, drama_id, f"{title} {batch_label}"):
            print(f"⏭️ SKIP: {batch_label}")
            continue

        print(f"📦 Mengolah {batch_label}...")
        temp_files = []
        output_file = f"result_{drama_id}_{start_num}.mp4"
        
        try:
            # Step A: Download semua episode dalam batch ini
            for idx, ep in enumerate(batch, start=start_num):
                # --- RADAR PENCARI LINK VIDEO ---
                # Kita cek semua kemungkinan nama kunci
                v_url = (
                    ep.get('url') or 
                    ep.get('videoUrl') or 
                    ep.get('playUrl') or 
                    ep.get('link') or 
                    ep.get('video_url') or
                    ep.get('downloadUrl') or
                    (ep.get('raw') or {}).get('videoUrl')
                )
                
                # --- MODE MATA-MATA (DEBUG) ---
                # Kalau link gak ketemu di episode pertama batch, kasih tau kita isinya apa!
                if not v_url and idx == start_num:
                    print(f"⚠️ ZONK! Gak nemu link video di Eps {idx}.")
                    print(f"🔍 ISI DATA EPISODE: {list(ep.keys())}") # Intip nama kuncinya
                    # print(ep) # Uncomment kalo mau liat isi fullnya (bisa panjang banget)

                if not v_url: continue
                
                v_file = f"temp_{idx}.mp4"
                print(f"📥 Download Eps {idx}...") # Kasih visual biar tau dia kerja
                download_file(v_url, v_file)
                temp_files.append(v_file)

            if not temp_files: 
                print(f"❌ Batch {batch_label} Kosong (Gagal download semua).")
                continue


            # Gabungkan dengan FFmpeg
            with open("list.txt", "w") as f:
                for tf in temp_files: f.write(f"file '{tf}'\n")
            
            print(f"🔗 Merging {batch_label}...")
            os.system(f"ffmpeg -f concat -safe 0 -i list.txt -c copy {output_file} -y")

            # Upload hasil gabungan
            if os.path.exists(output_file):
                w, h, dur = get_video_info(output_file)
                client.send_file(
                    GROUP_ID, output_file, 
                    caption=f"🎬 **{title}**\n📌 **{batch_label}**\n✅ Gabungan 10 Episode",
                    reply_to=topic_id,
                    supports_streaming=True,
                    attributes=[DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)]
                )
                save_history(platform, drama_id, f"{title} {batch_label}")
                print(f"✅ Berhasil Upload: {batch_label}")

        except Exception as e:
            print(f"⚠️ Error di {batch_label}: {e}")
        finally:
            # Bersih-bersih file
            for tf in temp_files: 
                if os.path.exists(tf): os.remove(tf)
            if os.path.exists("list.txt"): os.remove("list.txt")
            if os.path.exists(output_file): os.remove(output_file)
            
        time.sleep(2)

if __name__ == "__main__":
    init_db()
    p = input("Platform: "); i = input("ID: ")
    if p and i: gas_download(p, i)
        
