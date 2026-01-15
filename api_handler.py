import requests
import json

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    platform = platform.lower()
    
    print(f"🔄 Fetching data for {platform} ID: {drama_id}...")

    try:
        drama_data = {}
        episodes = []

        # ---------------- NETSHORT (FIXED DARI SCREENSHOT) ----------------
        if platform == 'netshort':
            # Endpoint: /netshort/allepisode (huruf kecil semua)
            # Parameter: shortPlayId (sesuai dokumentasi)
            url = f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"
            
            print(f"🕵️ Trying URL: {url}") 
            
            res = requests.get(url, headers=headers)
            
            if res.status_code != 200:
                print(f"❌ Error Status: {res.status_code}")
                # Print error dari server (biasanya HTML kalo 404/500)
                print(f"📄 Response: {res.text[:200]}") 
                return None
            
            # Ambil data JSON
            data_json = res.json()
            
            # Karena endpoint ini khusus "Semua Episode", biasanya return:
            # 1. Langsung List []
            # 2. Atau Dict {"data": [...]}
            if isinstance(data_json, list):
                episodes = data_json
            else:
                 # Coba berbagai kemungkinan key
                 episodes = data_json.get('data') or data_json.get('episodeList') or []
            
            # Handle Data Drama (Judul/Poster)
            # Karena endpoint ini fokus ke episode, kita ambil info drama dari episode pertama
            if episodes:
                first_ep = episodes[0]
                drama_data = {
                    'title': first_ep.get('dramaTitle') or first_ep.get('shortPlayName') or f"Drama {drama_id}",
                    'poster': first_ep.get('cover') or first_ep.get('shortPlayCover'),
                    'desc': first_ep.get('desc') or "Sinopsis tidak tersedia."
                }
            else:
                print("⚠️ Tidak ada episode ditemukan (List kosong).")
                # Coba print respon aslinya buat debug
                # print(f"DEBUG JSON: {data_json}") 
                return None

        # ---------------- DRAMABOX ----------------
        elif platform == 'dramabox':
            url = f"{BASE_URL}/dramabox/detailAndAllEpisode?bookId={drama_id}"
            res = requests.get(url, headers=headers).json()
            drama_data = res.get('drama') or res.get('data') or {}
            episodes = res.get('episodes') or res.get('episodeList', [])

        # ---------------- LAINNYA (Generic) ----------------
        else:
            url = f"{BASE_URL}/{platform}/detailAndAllEpisode?id={drama_id}"
            res = requests.get(url, headers=headers).json()
            drama_data = res.get('drama') or res.get('data') or {}
            episodes = res.get('episodes') or res.get('episodeList', [])

        # ---------------- VALIDASI DATA ----------------
        if not episodes:
            print(f"⚠️ Episode kosong untuk {platform} ID {drama_id}")
            # Cek struktur data kalau kosong, print keys-nya buat debug
            # print(f"Debug Data keys: {drama_data.keys()}")
            return None

        # 2. MASTER RADAR POSTER
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

        print(f"✅ Data OK: {title} ({len(episodes)} Eps)")

        return {
            'title': title,
            'poster': poster,
            'desc': desc,
            'episodes': episodes,
            'total_eps': len(episodes)
        }
        
    except json.JSONDecodeError:
        print(f"❌ API Error: Response bukan JSON valid. Server mungkin error atau ID salah.")
        return None
    except Exception as e:
        print(f"❌ API Error System ({platform}): {e}")
        return None
