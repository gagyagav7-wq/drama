import os
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
        output = subprocess.check_output(cmd).decode().strip().split("\n")
        
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

def download_file(url, file_path):
    """
    Download file dengan Mode Streaming + ANTI SSL ERROR.
    """
    try:
        # verify=False <--- INI KUNCINYA BIAR GAK ERROR SSL
        with requests.get(url, stream=True, timeout=60, verify=False) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                # Download per 1MB biar kenceng
                for chunk in r.iter_content(chunk_size=1024*1024): 
                    if chunk: f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Gagal Download: {e}")
        # Hapus file sampah kalau gagal
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
        
