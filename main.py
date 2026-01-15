import os, time
import asyncio
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import DocumentAttributeVideo
from database import init_db, is_duplicate, save_history
# 👇 Tambahin generate_thumbnail di sini
from utils import get_video_info, download_file, generate_thumbnail 
from api_handler import get_drama_data

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))

# Start client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def gas_download(platform, drama_id):
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
        r = await client(functions.channels.GetForumTopicsRequest(
            channel=GROUP_ID, offset_date=0, offset_id=0, offset_topic=0, limit=100
        ))
        for t in r.topics:
            if hasattr(t, 'title') and t.title.strip().lower() == title.strip().lower():
                topic_id = t.id
                print(f"♻️ Lanjut di folder: {title}")
                break
    except Exception as e:
        print(f"⚠️ Warning cari topic: {e}")

    # 2. BIKIN FOLDER BARU JIKA TIDAK ADA
    if not topic_id:
        try:
            result = await client(functions.channels.CreateForumTopicRequest(channel=GROUP_ID, title=title))
            topic_id = result.updates[0].id
            is_new_topic = True
            print(f"📁 Folder baru dibuat: {title} (ID: {topic_id})")
        except Exception as e:
            print(f"❌ Gagal bikin folder: {e}")
            return

    # 3. KIRIM PESAN PEMBUKA
    if is_new_topic:
        caption_pembuka = (
            f"🎬 **{title}**\n\n"
            f"📝 **Sinopsis:**\n{data['desc'][:900]}...\n\n"
            f"📊 **Total: {data.get('total_eps', len(data['episodes']))} Episode**\n"
            f"🚀 #Platform_{platform.upper()}"
        )
        
        msg = None
        if data.get('poster'):
            print("🖼️ Mengirim Poster...")
            poster_path = f"poster_{drama_id}.jpg"
            try:
                download_file(data['poster'], poster_path)
                msg = await client.send_file(
                    GROUP_ID, poster_path, 
                    caption=caption_pembuka, 
                    reply_to=topic_id
                )
            except Exception as e:
                print(f"⚠️ Gagal kirim poster: {e}")
                msg = await client.send_message(GROUP_ID, caption_pembuka, reply_to=topic_id)
            finally:
                if os.path.exists(poster_path): os.remove(poster_path)
        else:
            msg = await client.send_message(GROUP_ID, caption_pembuka, reply_to=topic_id)
            
        if msg:
            try:
                await client.pin_message(GROUP_ID, msg.id, notify=False)
            except: pass

    # 4. PROSES UPLOAD VIDEO
    for ep in data['episodes']:
        ep_name = ep.get('name') or ep.get('title') or f"Eps {data['episodes'].index(ep)+1}"
        
        if is_duplicate(platform, drama_id, ep_name):
            print(f"⏭️ SKIP: {ep_name} (Sudah ada)")
            continue

        v_url = (ep.get('raw') or {}).get('videoUrl') or ep.get('videoUrl')
        if not v_url: continue

        # NAMA FILE UNTUK VIDEO DAN THUMBNAIL
        v_file = f"temp_{drama_id}_{data['episodes'].index(ep)}.mp4"
        thumb_path = f"thumb_{drama_id}_{data['episodes'].index(ep)}.jpg" 
        
        print(f"📥 Download {ep_name}...")
        try:
            download_file(v_url, v_file)
            w, h, dur = get_video_info(v_file)
            
            # 👇 GENERATE THUMBNAIL (Uncomment kalau di utils.py ada fungsinya)
            try:
                generate_thumbnail(v_file, thumb_path)
            except:
                print("⚠️ Gagal generate thumbnail, skip.")

            print(f"📤 Uploading {ep_name}...")
            
            async with client.action(GROUP_ID, 'video', reply_to=topic_id):
                await client.send_file(
                    GROUP_ID, 
                    v_file,
                    # 👇 PASANG THUMB DISINI
                    thumb=thumb_path if os.path.exists(thumb_path) else None,
                    caption=f"🎬 **{title}**\n📌 {ep_name}", 
                    reply_to=topic_id, 
                    supports_streaming=True, 
                    attributes=[
                        DocumentAttributeVideo(
                            duration=int(dur), 
                            w=int(w), 
                            h=int(h), 
                            supports_streaming=True
                        )
                    ]
                )
            
            save_history(platform, drama_id, ep_name)
            print(f"✅ Selesai: {ep_name}")
            
        except Exception as e:
            print(f"⚠️ Gagal upload {ep_name}: {e}")
        finally:
            # 👇 BERSIH-BERSIH FILE
            if os.path.exists(v_file): os.remove(v_file)
            if os.path.exists(thumb_path): os.remove(thumb_path)
        
        time.sleep(1) 

if __name__ == "__main__":
    init_db()
    p = input("Platform: "); i = input("ID: ")
    if p and i:
        client.loop.run_until_complete(gas_download(p, i))
