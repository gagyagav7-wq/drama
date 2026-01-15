import requests

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    platform = platform.lower()
    
    try:
        # 1. LOGIKA UNTUK NETSHORT
        if platform == 'netshort':
            # Ambil info (Judul & Poster)
            info = requests.get(f"{BASE_URL}/netshort/detail?shortPlayId={drama_id}", headers=headers).json()
            # Ambil list episode
            eps = requests.get(f"{BASE_URL}/netshort/allEpisode?shortPlayId={drama_id}", headers=headers).json()
            
            return {
                'title': info.get('shortPlayName') or info.get('title'),
                'poster': info.get('shortPlayCover') or info.get('poster'),
                'desc': info.get('shotIntroduce') or info.get('description'),
                'episodes': eps if isinstance(eps, list) else eps.get('episodeList', [])
            }
        
        # 2. LOGIKA UNTUK DRAMABOX
        elif platform == 'dramabox':
            url = f"{BASE_URL}/dramabox/detailAndAllEpisode?bookId={drama_id}"
            
        # 3. LOGIKA UNTUK FLICKREELS (DAN LAINNYA)
        else:
            url = f"{BASE_URL}/{platform}/detailAndAllEpisode?id={drama_id}"
            
        res = requests.get(url, headers=headers).json()
        drama_data = res.get('drama', {})
        
        return {
            'title': drama_data.get('title'),
            'poster': drama_data.get('poster'),
            'desc': drama_data.get('description'),
            'episodes': res.get('episodes', [])
        }
        
    except Exception as e:
        print(f"❌ API Error di platform {platform}: {e}")
        return None
