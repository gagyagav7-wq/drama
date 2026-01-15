import os
import requests
import subprocess # <--- Wajib ada buat jalanin FFmpeg
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

def get_video_info(file_path):
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata:
            # Note: duration di hachoir kadang formatnya object, kita ambil seconds
            return int(metadata.get('width')), int(metadata.get('height')), int(metadata.get('duration').seconds)
    except Exception as e:
        print(f"⚠️ Warning Metadata: {e}")
        pass
    # Default kalau gagal detect
    return 720, 1280, 0 

def download_file(url, file_path):
    try:
        with requests.get(url, stream=True, timeout=60) as r: # Timeout dinaikin dikit biar aman
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for c in r.iter_content(1024*1024): 
                    f.write(c)
        return True
    except Exception as e:
        print(f"❌ Gagal Download: {e}")
        return False

# 👇 FUNGSI BARU BUAT BIKIN THUMBNAIL 👇
def generate_thumbnail(video_path, thumb_path):
    try:
        # Pake FFmpeg buat ambil frame di detik ke-1
        cmd = f"ffmpeg -y -i {video_path} -ss 00:00:01 -vframes 1 {thumb_path} -loglevel panic"
        subprocess.call(cmd, shell=True)
        return True
    except Exception as e:
        print(f"⚠️ Gagal Generate Thumbnail: {e}")
        return False
