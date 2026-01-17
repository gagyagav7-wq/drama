import requests
import json

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
        # 1. KHUSUS DRAMABOX
        # ==========================================
        if platform == 'dramabox':
            try:
                meta_url = f"{BASE_URL}/dramabox/detail?bookId={drama_id}"
                print(f"✨ Mengintip Metadata: {meta_url}")
                meta_res = requests.get(meta_url, headers=headers, timeout=10)
                
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

            except Exception as e:
                print(f"⚠️ Gagal ambil metadata Dramabox: {e}")

            video_url = f"{BASE_URL}/dramabox/allepisode?bookId={drama_id}"
            print(f"👉 Mengambil Video: {video_url}")
            res = requests.get(video_url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list): episodes = data
                elif isinstance(data, dict): episodes = data.get('data') or []

        # ==========================================
        # 2. NETSHORT (UPDATE STRUKTUR BARU) 🛠️
        # ==========================================
        elif platform == 'netshort':
            url = f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"
            print(f"👉 Request ke: {url}")
            
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data_json = res.json()
                
                # --- LOGIKA BARU: Cek Struktur 'shortPlayEpisodeInfos' ---
                if isinstance(data_json, dict) and 'shortPlayEpisodeInfos' in data_json:
                    print("✅ Terdeteksi Struktur Baru Netshort (shortPlayEpisodeInfos)")
                    episodes = data_json['shortPlayEpisodeInfos']
                    
                    # Ambil Metadata dari Root
                    drama_info['title'] = data_json.get('shortPlayName')
                    drama_info['poster'] = data_json.get('shortPlayCover')
                    drama_info['desc'] = data_json.get('shotIntroduce')
                    
                    # Ambil Genre (Array Strings)
                    labels = data_json.get('shortPlayLabels') or []
                    if isinstance(labels, list):
                        drama_info['tags'] = ", ".join(labels)
                    else:
                        drama_info['tags'] = str(labels)

                    # 🔥 FIX LINK VIDEO: playVoucher -> videoUrl 🔥
                    # Biar main.py bisa baca tanpa perlu diubah
                    for ep in episodes:
                        if 'playVoucher' in ep:
                            ep['videoUrl'] = ep['playVoucher']

                # --- LOGIKA LAMA (Fallback buat jaga-jaga) ---
                elif isinstance(data_json, dict) and 'data' in data_json:
                    episodes = data_json.get('data') or []
                    if episodes and len(episodes) > 0:
                        first = episodes[0]
                        drama_info['title'] = first.get('dramaTitle')
                        drama_info['poster'] = first.get('cover')
                        drama_info['desc'] = first.get('desc')
                        drama_info['tags'] = first.get('dramaType')

        # ==========================================
        # 3. FLICKREELS / LAINNYA
        # ==========================================
        else:
            url = f"{BASE_URL}/{platform}/{drama_id}"
            if platform == 'flickreels':
                url = f"{BASE_URL}/flickreels/{drama_id}"

            print(f"👉 Request ke: {url}")
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data_json = res.json()
                root = data_json.get('data', data_json) if isinstance(data_json, dict) else data_json
                
                if root:
                    episodes = root.get('episodes') or root.get('episode_list') or root.get('chapters') or []
                    drama_info['title'] = root.get('title') or root.get('name')
                    drama_info['poster'] = root.get('poster') or root.get('cover') or root.get('vertical_cover')
                    drama_info['desc'] = root.get('desc') or root.get('description')
                    drama_info['tags'] = root.get('tags') or "Drama"

        # ==========================================
        # 4. FINALISASI DATA
        # ==========================================
        if not episodes:
            print("❌ GAGAL: Episode tidak ditemukan (List Kosong).")
            return None

        # Fallback Metadata
        final_title = drama_info.get('title') or f"{platform.upper()}_{drama_id}"
        final_poster = drama_info.get('poster') or "https://i.ibb.co/GtpCNh6/default-poster.jpg"
        final_desc = drama_info.get('desc') or "Sinopsis belum tersedia."
        final_tags = drama_info.get('tags') or "Drama, Romance"

        print(f"✅ SUKSES: {final_title} | Genre: {final_tags} | Total: {len(episodes)} Eps")

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
        
