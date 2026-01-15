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

        # ---------------- NETSHORT ----------------
        if platform == 'netshort':
            # FIX: Ganti parameter jadi shortPlayLibraryId sesuai input user
            # Kalau nanti masih error, coba ganti param jadi 'bookId' atau 'id'
            url_detail = f"{BASE_URL}/netshort/detail?shortPlayLibraryId={drama_id}"
            url_eps = f"{BASE_URL}/netshort/allEpisode?shortPlayLibraryId={drama_id}"

            # Debug Request Detail
            res_info = requests.get(url_detail, headers=headers)
            if res_info.status_code != 200:
                print(f"❌ Error Detail Status: {res_info.status_code}")
                print(f"📄 Response: {res_info.text[:200]}") # Print isi error
                return None
            
            info = res_info.json()
            
            # Debug Request Episodes
            res_eps = requests.get(url_eps, headers=headers)
            if res_eps.status_code != 200:
                print(f"❌ Error Episode Status: {res_eps.status_code}")
                return None
                
            eps_data = res_eps.json()

            # Mapping Data Netshort
            drama_data = info.get('data', info) # Jaga-jaga kalau dibungkus key 'data'
            # Netshort kadang return list langsung, kadang dict
            if isinstance(eps_data, list):
                episodes = eps_data
            else:
                episodes = eps_data.get('data', []) or eps_data.get('episodeList', [])

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
