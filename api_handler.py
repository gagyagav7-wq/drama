import requests

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    platform = platform.lower()
    
    try:
        # 1. AMBIL DATA MENTAH DARI API
        if platform == 'netshort':
            info = requests.get(f"{BASE_URL}/netshort/detail?shortPlayId={drama_id}", headers=headers).json()
            eps_res = requests.get(f"{BASE_URL}/netshort/allEpisode?shortPlayId={drama_id}", headers=headers).json()
            drama_data = info
            episodes = eps_res if isinstance(eps_res, list) else eps_res.get('episodeList', [])
        elif platform == 'dramabox':
            res = requests.get(f"{BASE_URL}/dramabox/detailAndAllEpisode?bookId={drama_id}", headers=headers).json()
            drama_data = res.get('drama') or res.get('data') or {}
            episodes = res.get('episodes') or res.get('episodeList', [])
        else:
            # Jalur Flickreels, Shortmax, dll
            res = requests.get(f"{BASE_URL}/{platform}/detailAndAllEpisode?id={drama_id}", headers=headers).json()
            drama_data = res.get('drama') or res.get('data') or {}
            episodes = res.get('episodes') or res.get('episodeList', [])

        # 2. MASTER RADAR POSTER (Terapkan ke semua)
        # Bot bakal nyari dari yang paling umum sampe yang paling spesifik
        poster = (
            drama_data.get('poster') or 
            drama_data.get('shortPlayCover') or 
            drama_data.get('horizontal_cover') or 
            drama_data.get('vertical_cover') or 
            drama_data.get('cover') or
            drama_data.get('horizontalCover') or
            drama_data.get('verticalCover')
        )

        # 3. MASTER RADAR JUDUL & SINOPSIS
        title = (
            drama_data.get('title') or 
            drama_data.get('shortPlayName') or 
            drama_data.get('name') or 
            f"{platform.upper()}_{drama_id}"
        )
        
        desc = (
            drama_data.get('description') or 
            drama_data.get('shotIntroduce') or 
            drama_data.get('intro') or 
            "Tidak ada sinopsis."
        )

        # Di dalam api_handler.py, bagian return diubah dikit:
        return {
            'title': title,
            'poster': poster,
            'desc': desc,
            'episodes': episodes,
            'total_eps': len(episodes) # Tambahin ini biar main.py tau jumlahnya
        }
        
    except Exception as e:
        print(f"❌ API Error ({platform}): {e}")
        return None
