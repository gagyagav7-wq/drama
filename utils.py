import os
import requests
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

def get_video_info(file_path):
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata:
            return int(metadata.get('width')), int(metadata.get('height')), int(metadata.get('duration').seconds)
    except: pass
    return 720, 1280, 0 

def download_file(url, file_path):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for c in r.iter_content(1024*1024): f.write(c)
              
