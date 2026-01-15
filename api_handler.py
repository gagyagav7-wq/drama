import requests
import json

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    platform = platform.lower()
    
    print(f"🔄 Fetching data for {platform.upper()} ID: {drama_id}...")

    try:
        url = ""
        # ==========================================
        # 1. BAGIAN MENENTUKAN URL
        # ==========================================
        if platform == 'netshort':
            url = f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"
            
        elif platform == 'dramabox':
            url = f"{BASE_URL}/dramabox/{drama_id}"
            
        elif platform == 'flickreels':
            url = f"{BASE_URL}/flickreels/{drama_id}"
            
        else:
            # Kalau lu iseng masukin 'shortmax' atau 'topshort', bakal lari kesini
            # Dan kemungkinan besar bakal error 404 karena API-nya ga ada
            url = f"{BASE_URL}/{platform}/{drama_id}"

        print(f"📡 Request ke: {url}")

        # ==========================================
        # 2. EKSEKUSI REQUEST
        # ==========================================
        res = requests.get(url, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"❌ Server Error! Status: {res.status_code}")
            # Kalau 404 berarti endpoint ga ada
            if res.status_code == 404:
                print("⚠️ Kemungkinan Platform tidak disupport atau ID salah.")
            else:
                print(f"📄 Respon Server: {res.text[:200]}...") 
            return None

        try:
            data_json = res.json()
        except:
            print("❌ Gagal baca JSON! Respon server bukan data valid.")
            return None

        # ==========================================
        # 3. PARSING DATA (Cuma 3 Jenis)
        # ==========================================
        
        drama_data = {}
        episodes = []

        # --- A. NETSHORT (Format List/Data Beda) ---
        if platform == 'netshort':
            if isinstance(data_json, list):
                episodes = data_json
            else:
                episodes = data_json.get('data') or data_json.get('episodeList') or []
            
            if episodes:
                first = episodes[0]
                drama_data = {
                    'title': first.get('dramaTitle') or first.get('shortPlayName'),
                    'poster': first.get('cover') or first.get('shortPlayCover'),
                    'desc': first.get('desc') or "No Synopsis"
                }

        # --- B. DRAMABOX & FLICKREELS (Format Object Standard) ---
        else:
            # Masuk ke key 'data' kalau ada
            if 'data' in data_json:
                root_data = data_json['data']
            else:
                root_data = data_json 

            episodes = (
                root_data.get('episodes') or 
                root_data.get('episode_list') or 
                root_data.get('chapters') or 
                []
            )
            drama_data = root_data

        # ==========================================
        # 4. FINALISASI
        # ==========================================
        
        if not episodes:
            print(f"⚠️ Data ditemukan tapi Episode Kosong! Cek ID lagi.")
            return None

        # Master Radar (Cari Poster/Judul)
        poster = (
            drama_data.get('poster') or 
            drama_data.get('cover') or 
            drama_data.get('vertical_cover') or 
            drama_data.get('bookCover') 
        )

        title = (
            drama_data.get('title') or 
            drama_data.get('name') or 
            drama_data.get('bookName') or 
            f"{platform.upper()}_{drama_id}"
        )
        
        desc = (
            drama_data.get('desc') or 
            drama_data.get('description') or 
            drama_data.get('intro') or 
            drama_data.get('introduction') or 
            "-"
        )

        print(f"✅ SUKSES: {title} | Dapet {len(episodes)} Episode")

        return {
            'title': title,
            'poster': poster,
            'desc': desc,
            'episodes': episodes,
            'total_eps': len(episodes)
        }
        
    except Exception as e:
        print(f"❌ Error System ({platform}): {e}")
        return None
        
