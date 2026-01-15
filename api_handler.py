import requests
import json

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    platform = platform.lower()
    
    print(f"🔄 Fetching data for {platform.upper()} ID: {drama_id}...")
    
    drama_info = {} # Buat nampung Judul, Poster, Sinopsis
    episodes = []   # Buat nampung Video

    try:
        # ==========================================
        # 1. KHUSUS DRAMABOX (JURUS DOUBLE HIT)
        # ==========================================
        if platform == 'dramabox':
            # STEP A: Ambil Metadata (Judul, Poster, Sinopsis) dari endpoint /detail
            # Kita pake try-except biar kalau ini gagal, download tetep jalan
            try:
                meta_url = f"{BASE_URL}/dramabox/detail?bookId={drama_id}"
                print(f"✨ Mengambil Metadata: {meta_url}")
                meta_res = requests.get(meta_url, headers=headers, timeout=10)
                if meta_res.status_code == 200:
                    meta_data = meta_res.json()
                    # Simpan info gantengnya
                    drama_info['title'] = meta_data.get('bookName') or meta_data.get('data', {}).get('bookName')
                    drama_info['poster'] = meta_data.get('cover') or meta_data.get('data', {}).get('cover')
                    drama_info['desc'] = meta_data.get('introduction') or meta_data.get('data', {}).get('introduction')
            except Exception as e:
                print(f"⚠️ Gagal ambil metadata (Judul mungkin raw): {e}")

            # STEP B: Ambil Video (Wajib) dari endpoint /allepisode
            video_url = f"{BASE_URL}/dramabox/allepisode?bookId={drama_id}"
            print(f"👉 Mengambil Video: {video_url}")
            res = requests.get(video_url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                # Dramabox allepisode isinya langsung List
                if isinstance(data, list):
                    episodes = data
                elif isinstance(data, dict):
                    episodes = data.get('data') or []

        # ==========================================
        # 2. NETSHORT & FLICKREELS (NORMAL)
        # ==========================================
        else:
            # Tentukan URL
            url = ""
            if platform == 'netshort':
                url = f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"
            elif platform == 'flickreels':
                url = f"{BASE_URL}/flickreels/{drama_id}"
            else:
                url = f"{BASE_URL}/{platform}/{drama_id}"

            print(f"👉 Request ke: {url}")
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data_json = res.json()
                
                # Parsing Netshort
                if platform == 'netshort':
                    if isinstance(data_json, list):
                        episodes = data_json
                    else:
                        episodes = data_json.get('data') or data_json.get('episodeList') or []
                    
                    if episodes:
                        first = episodes[0]
                        drama_info['title'] = first.get('dramaTitle') or first.get('shortPlayName')
                        drama_info['poster'] = first.get('cover') or first.get('shortPlayCover')
                        drama_info['desc'] = first.get('desc')

                # Parsing Flickreels/Lainnya
                else:
                    root = data_json.get('data', data_json)
                    episodes = root.get('episodes') or root.get('episode_list') or root.get('chapters') or []
                    
                    drama_info['title'] = root.get('title') or root.get('name')
                    drama_info['poster'] = root.get('poster') or root.get('cover') or root.get('vertical_cover')
                    drama_info['desc'] = root.get('desc') or root.get('description')

        # ==========================================
        # 3. FINALISASI & MERGING DATA
        # ==========================================
        if not episodes:
            print("❌ GAGAL: Episode tidak ditemukan.")
            return None

        # Gabungkan Metadata (kalau ada) dengan Default
        final_title = (
            drama_info.get('title') or 
            f"{platform.upper()}_{drama_id}" # Fallback kalau judul gagal
        )
        
        final_poster = (
            drama_info.get('poster') or 
            drama_info.get('cover') or # Coba cari di key lain
            "https://i.ibb.co/GtpCNh6/default-poster.jpg" # Gambar default biar gak error
        )
        
        final_desc = (
            drama_info.get('desc') or 
            "Sinopsis belum tersedia."
        )

        print(f"✅ SUKSES: {final_title} | Total: {len(episodes)} Eps")

        return {
            'title': final_title,
            'poster': final_poster,
            'desc': final_desc,
            'episodes': episodes,
            'total_eps': len(episodes)
        }
        
    except Exception as e:
        print(f"❌ Error System ({platform}): {e}")
        return None
        
