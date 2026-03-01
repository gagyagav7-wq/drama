import os
import time
import requests
import subprocess
import urllib3

# 🔥 MATIIN WARNING SSL (Biar terminal lu bersih)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_video_info(file_path):
    """
    Ambil resolusi & durasi video pake FFprobe (Lebih akurat dari hachoir).
    Gak perlu install library tambahan karena lu udah punya FFmpeg.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        # Jalanin perintah di terminal background
        output = subprocess.check_output(cmd, text=True).strip().split("\n")
        
        if len(output) >= 2:
            width = int(output[0])
            height = int(output[1])
            # Ambil durasi (kalau ada)
            duration = int(float(output[2])) if len(output) > 2 else 0
            return width, height, duration
            
    except Exception as e:
        print(f"⚠️ Gagal Info Video: {e}")
        pass
        
    # Default kalau gagal detect (misal file korup dikit)
    return 720, 1280, 0 

def download_file(url, file_path, retries=3):
    """
    Download file dengan Mode Streaming + ANTI SSL ERROR + PENYAMARAN + AUTO RETRY.
    """
    # Penyamaran (Spoofing) biar ga disangka bot dan lolos dari 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/'
    }

    for attempt in range(retries):
        try:
            # verify=False <--- INI KUNCINYA BIAR GAK ERROR SSL
            with requests.get(url, headers=headers, stream=True, timeout=60, verify=False) as r:
                r.raise_for_status() # Langsung trigger error kalau dapet 403/404
                with open(file_path, "wb") as f:
                    # Download per 1MB biar kenceng
                    for chunk in r.iter_content(chunk_size=1024*1024): 
                        if chunk: f.write(chunk)
            return True # Kalau sukses sampai sini, langsung keluar fungsi
            
        except requests.exceptions.HTTPError as e:
            print(f"⚠️ Percobaan {attempt + 1}/{retries} Gagal (HTTP Error): {e}")
            if e.response.status_code == 403:
                print("   👉 Server nge-blokir. Coba ganti IP atau tunggu jeda bentar.")
            time.sleep(3) # Jeda 3 detik sebelum nyoba lagi
            
        except Exception as e:
            print(f"⚠️ Percobaan {attempt + 1}/{retries} Gagal (Koneksi): {e}")
            time.sleep(3)

    # Kalau udah nyoba berkali-kali tetep gagal, hapus file sampahnya
    print("❌ Gagal Download total setelah beberapa kali percobaan.")
    if os.path.exists(file_path):
        try: os.remove(file_path)
        except: pass
    return False

def generate_thumbnail(video_path, thumb_path):
    """
    Bikin thumbnail otomatis dari detik ke-1 video
    """
    try:
        # Pake FFmpeg buat ambil frame
        cmd = f"ffmpeg -y -i \"{video_path}\" -ss 00:00:01 -vframes 1 \"{thumb_path}\" -loglevel panic"
        subprocess.call(cmd, shell=True)
        return True
    except Exception as e:
        print(f"⚠️ Gagal Generate Thumbnail: {e}")
        return False
        
