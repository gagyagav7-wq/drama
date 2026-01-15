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

    # --- SMART TOPIC (FOLDER MATCHING) ---
    topic_id = None
    is_new_topic = False

    # 1. Coba cari folder yang sudah ada dulu secara teliti
    try:
        # Ambil 100 topik terbaru
        r = client(functions.channels.GetForumTopicsRequest(
            channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100
        ))
        for t in r.topics:
            if hasattr(t, 'title') and t.title.strip() == title.strip():
                topic_id = t.id
                print(f"♻️ Menemukan folder lama (ID: {topic_id}), melanjutkan...")
                break
    except Exception as e:
        print(f"⚠️ Gagal scanning folder: {e}")

    # 2. Kalau beneran nggak nemu, baru bikin baru
    if not topic_id:
        try:
            result = client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
            print(f"📁 Folder baru dibuat: {title}")
        except Exception as e:
            print(f"❌ Gagal total bikin folder: {e}")
            return

    # 3. Kirim Poster & Sinopsis HANYA jika foldernya beneran baru
    if is_new_topic:
        cap = f"🎬 **{title}**\n\n📝 **Sinopsis:**\n{data['desc']}\n\n#Platform_{platform.upper()}"
        try:
            if data['poster']:
                client.send_file(GROUP_ID, data['poster'], caption=cap, reply_to=topic_id)
            else:
                client.send_message(GROUP_ID, cap, reply_to=topic_id)
        except:
            client.send_message(GROUP_ID, cap, reply_to=topic_id)

    # --- UPLOAD VIDEO ---
    for ep in data['episodes']:
        ep_name = ep.get('name') or ep.get('title') or f"Eps {data['episodes'].index(ep)+1}"
        
        # Cek database history (Biar nggak dobel upload)
        if is_duplicate(platform, drama_id, ep_name):
            print(f"⏭️ SKIP: {ep_name}")
            continue

        v_url = (ep.get('raw') or {}).get('videoUrl') or ep.get('videoUrl')
        if not v_url: continue

        v_file = f"temp_{drama_id}_{data['episodes'].index(ep)}.mp4"
        print(f"📥 Download {ep_name}...")
        try:
            download_file(v_url, v_file)
            w, h, dur = get_video_info(v_file)
            print(f"📤 Uploading {ep_name} to Topic {topic_id}...")
            client.send_file(
                GROUP_ID, v_file, 
                caption=f"🎬 **{title}**\n📌 {ep_name}", 
                reply_to=topic_id, 
                supports_streaming=True, 
                attributes=[DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)]
            )
            save_history(platform, drama_id, ep_name)
        except Exception as e:
            print(f"⚠️ Gagal upload {ep_name}: {e}")
        finally:
            if os.path.exists(v_file): os.remove(v_file)
        
        time.sleep(1.2)

if __name__ == "__main__":
    init_db()
    p = input("Platform: "); i = input("ID: ")
    if p and i: gas_download(p, i)
