import requests
import json
import urllib3

# Matiin warning SSL biar terminal bersih
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    platform = platform.lower()
    
    print(f"🔄 Fetching data for {platform.upper()} ID: {drama_id}...")
    
    drama_info = {} 
    episodes = []   

    try:
        # ==========================================
        # 1. KHUSUS DRAMABOX (AMAN)
        # ==========================================
        if platform == 'dramabox':
            try:
                meta_url = f"{BASE_URL}/dramabox/detail?bookId={drama_id}"
                print(f"✨ Mengintip Metadata: {meta_url}")
                meta_res = requests.get(meta_url, headers=headers, timeout=10, verify=False)
                if meta_res.status_code == 200:
                    meta_data = meta_res.json()
                    data_inner = meta_data.get('data') or {}
                    drama_info['title'] = (meta_data.get('bookName') or data_inner.get('bookName'))
                    drama_info['poster'] = (meta_data.get('coverWap') or meta_data.get('cover') or data_inner.get('coverWap'))
                    drama_info['desc'] = (meta_data.get('introduction') or meta_data.get('desc') or data_inner.get('introduction'))
                    tags_raw = meta_data.get('tagList') or data_inner.get('tagList')
                    genre_list = []
                    if tags_raw and isinstance(tags_raw, list):
                        for t in tags_raw:
                            name = t.get('tagName') or t.get('name')
                            if name: genre_list.append(name)
                    drama_info['tags'] = ", ".join(genre_list) if genre_list else "Drama"
            except: pass

            video_url = f"{BASE_URL}/dramabox/allepisode?bookId={drama_id}"
            print(f"👉 Mengambil Video: {video_url}")
            res = requests.get(video_url, headers=headers, timeout=30, verify=False)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list): episodes = data
                elif isinstance(data, dict): episodes = data.get('data') or []

        # ==========================================
        # 2. KHUSUS NETSHORT (AMAN)
        # ==========================================
        elif platform == 'netshort':
            url = f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"
            print(f"👉 Request ke: {url}")
            res = requests.get(url, headers=headers, timeout=30, verify=False)
            
            if res.status_code == 200:
                data_json = res.json()
                if isinstance(data_json, dict) and 'shortPlayEpisodeInfos' in data_json:
                    episodes = data_json['shortPlayEpisodeInfos']
                    drama_info['title'] = data_json.get('shortPlayName')
                    drama_info['poster'] = data_json.get('shortPlayCover')
                    drama_info['desc'] = data_json.get('shotIntroduce')
                    labels = data_json.get('shortPlayLabels') or []
                    drama_info['tags'] = ", ".join(labels) if isinstance(labels, list) else str(labels)
                    for ep in episodes:
                        if 'playVoucher' in ep: ep['videoUrl'] = ep['playVoucher']
                elif isinstance(data_json, dict):
                    d = data_json.get('data')
                    if d:
                        if isinstance(d, list): episodes = d
                        elif isinstance(d, dict): episodes = d.get('episodes') or []
                        if episodes:
                            first = episodes[0]
                            drama_info['title'] = first.get('dramaTitle')
                            drama_info['tags'] = first.get('dramaType')

        # ==========================================
        # 3. KHUSUS FLICKREELS (FIXED! 🛠️)
        # ==========================================
        elif platform == 'flickreels':
            # URL Khusus Flickreels
            url = f"{BASE_URL}/flickreels/detailAndAllEpisode?id={drama_id}"
            print(f"👉 Request ke: {url}")
            
            res = requests.get(url, headers=headers, timeout=30, verify=False)
            
            if res.status_code == 200:
                data_json = res.json()
                
                # Cek apakah kunci 'episodes' ada?
                if 'episodes' in data_json:
                    print("✅ Struktur Flickreels Ditemukan!")
                    
                    # 1. Ambil Metadata
                    d = data_json.get('drama') or {}
                    drama_info['title'] = d.get('title')
                    drama_info['poster'] = d.get('cover')
                    drama_info['desc'] = d.get('description')
                    drama_info['tags'] = "Drama, Romance" # Default, kadang API kosong

                    # 2. Ambil Episodes & Buka Kulit 'raw'
                    raw_eps = data_json['episodes']
                    for item in raw_eps:
                        # Video URL ngumpet di dalam 'raw'
                        raw_data = item.get('raw') or {}
                        vid_url = raw_data.get('videoUrl')
                        
                        if vid_url:
                            # Kita bikin format baru biar dibaca main.py
                            episodes.append({
                                'videoUrl': vid_url,
                                'title': item.get('name')
                            })
                else:
                    print(f"⚠️ Struktur Flickreels Aneh: {list(data_json.keys())}")

        # ==========================================
        # 4. FINALISASI
        # ==========================================
        if not episodes:
            print("❌ GAGAL: Episode tidak ditemukan (List Kosong).")
            return None

        final_title = drama_info.get('title') or f"{platform.upper()}_{drama_id}"
        final_poster = drama_info.get('poster') or "https://i.ibb.co/GtpCNh6/default-poster.jpg"
        final_desc = drama_info.get('desc') or "Sinopsis belum tersedia."
        final_tags = drama_info.get('tags') or "Drama"

        print(f"✅ SUKSES: {final_title} | Total: {len(episodes)} Eps")

        return {
            'title': final_title,
            'poster': final_poster,
            'desc': final_desc,
            'tags': final_tags,
            'episodes': episodes,
            'total_eps': len(episodes)
        }
        
    except Exception as e:
        print(f"❌ Error System ({platform}): {e}")
        return None
                            
