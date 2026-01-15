import os, time
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import DocumentAttributeVideo
from database import init_db, is_duplicate, save_history
from utils import get_video_info, download_file, generate_thumbnail # Asumsi lu bikin fungsi generate thumbnail
from api_handler import get_drama_data

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))

# Start client sync
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def gas_download(platform, drama_id):
    data = get_drama_data(platform, drama_id)
    if not data or not data['episodes']:
        print("❌ Data tidak ditemukan!")
        return

    title = data['title'] or f"Drama_{drama_id}"
    print(f"🎬 MEMPROSES: {title}")

    # 1. CARI FOLDER (TOPIC) LAMA
    topic_id = None
    is_new_topic = False

    try:
        # Note: Limit 100 mungkin kurang kalau grup lu rame banget, tapi oke buat start
        r = client(functions.channels.GetForumTopicsRequest(
            channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100
        ))
        for t in r.topics:
            # Pake strip() dan lower() biar pencarian lebih akurat
            if hasattr(t, 'title') and t.title.strip().lower() == title.strip().lower():
                topic_id = t.id
                print(f"♻️ Lanjut di folder: {title}")
                break
    except Exception as e:
        print(f"⚠️ Warning cari topic: {e}")

    # 2. BIKIN FOLDER BARU JIKA TIDAK ADA
    if not topic_id:
        try:
            result = client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
            print(f"📁 Folder baru dibuat: {title} (ID: {topic_id})")
        except Exception as e:
            print(f"❌ Gagal bikin folder: {e}")
            return

    # 3. KIRIM PESAN PEMBUKA (ESTETIK + AUTO PIN)
    if is_new_topic:
        caption_pembuka = (
            f"🎬 **{title}**\n\n"
            f"📝 **Sinopsis:**\n{data['desc'][:900]}...\n\n" # Limit text biar gak kepanjangan
            f"📊 **Total: {data.get('total_eps', len(data['episodes']))} Episode**\n"
            f"🚀 #Platform_{platform.upper()}"
        )
        
        msg = None
        # Handle Poster
        if data.get('poster'):
            print("🖼️ Mengirim Poster...")
            poster_path = f"poster_{drama_id}.jpg"
            try:
                # Download poster dulu biar aman dari link mati
                download_file(data['poster'], poster_path)
                msg = client.send_file(
                    GROUP_ID, poster_path, 
                    caption=caption_pembuka, 
                    reply_to=topic_id
                )
            except Exception as e:
                print(f"⚠️ Gagal kirim poster (fallback text): {e}")
                msg = client.send_message(GROUP_ID, caption_pembuka, reply_to=topic_id)
            finally:
                if os.path.exists(poster_path): os.remove(poster_path)
        else:
            msg = client.send_message(GROUP_ID, caption_pembuka, reply_to=topic_id)
            
        # Pin pesan
        if msg:
            try:
                client.pin_message(GROUP_ID, msg.id, notify=False)
            except: pass

    # 4. PROSES UPLOAD VIDEO
    for ep in data['episodes']:
        ep_name = ep.get('name') or ep.get('title') or f"Eps {data['episodes'].index(ep)+1}"
        
        if is_duplicate(platform, drama_id, ep_name):
            print(f"⏭️ SKIP: {ep_name} (Sudah ada)")
            continue

        v_url = (ep.get('raw') or {}).get('videoUrl') or ep.get('videoUrl')
        if not v_url: continue

        v_file = f"temp_{drama_id}_{data['episodes'].index(ep)}.mp4"
        thumb_file = f"thumb_{drama_id}_{data['episodes'].index(ep)}.jpg" # Buat thumbnail
        
        print(f"📥 Download {ep_name}...")
        try:
            download_file(v_url, v_file)
            w, h, dur = get_video_info(v_file)
            
            # Generate thumbnail kalau bisa (optional, implementasi di utils)
            # generate_thumbnail(v_file, thumb_file) 
            
            print(f"📤 Uploading {ep_name}...")
            
            # Kirim status "uploading video" ke telegram biar keren
            async with client.action(GROUP_ID, 'video', reply_to=topic_id):
                client.send_file(
                    GROUP_ID, 
                    v_file, 
                    # thumb=thumb_file if os.path.exists(thumb_file) else None, # Pake ini kalo ada fungsi thumb
                    caption=f"🎬 **{title}**\n📌 {ep_name}", 
                    reply_to=topic_id, 
                    supports_streaming=True, 
                    attributes=[
                        DocumentAttributeVideo(
                            duration=int(dur), # WAJIB INT
                            w=int(w),         # WAJIB INT
                            h=int(h),         # WAJIB INT
                            supports_streaming=True
                        )
                    ]
                )
            
            save_history(platform, drama_id, ep_name)
            print(f"✅ Selesai: {ep_name}")
            
        except Exception as e:
            print(f"⚠️ Gagal upload {ep_name}: {e}")
        finally:
            if os.path.exists(v_file): os.remove(v_file)
            if os.path.exists(thumb_file): os.remove(thumb_file)
        
        # Jeda dikit biar gak kena floodwait parah
        time.sleep(2)

if __name__ == "__main__":
    init_db()
    p = input("Platform: "); i = input("ID: ")
    if p and i: gas_download(p, i)
