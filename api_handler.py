import requests
import json

BASE_URL = "https://api.sansekai.my.id/api"

def get_drama_data(platform, drama_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    platform = platform.lower()
    
    print(f"🔄 Fetching data for {platform.upper()} ID: {drama_id}...")

    # ==========================================
    # 1. STRATEGI URL (PRIORITAS LINK)
    # ==========================================
    urls_to_try = []

    if platform == 'dramabox':
        # INI LINK TEMUAN LU (PRIORITAS NO.1)
        urls_to_try = [
            f"{BASE_URL}/dramabox/allepisode?bookId={drama_id}",       # <--- TARGET UTAMA
            f"{BASE_URL}/dramabox/detailAndAllEpisode?bookId={drama_id}", # Cadangan 1
            f"{BASE_URL}/dramabox/episode?bookId={drama_id}"             # Cadangan 2
        ]
    elif platform == 'netshort':
        urls_to_try = [f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"]
    elif platform == 'flickreels':
        urls_to_try = [f"{BASE_URL}/flickreels/{drama_id}"]
    else:
        # Fallback (Generic)
        urls_to_try = [f"{BASE_URL}/{platform}/{drama_id}"]

    # ==========================================
    # 2. EKSEKUSI HUNTER (Coba satu-satu)
    # ==========================================
    final_res = None
    
    for url in urls_to_try:
        try:
            print(f"👉 Nembak ke: {url}")
            res = requests.get(url, headers=headers, timeout=20)
            
            if res.status_code == 200:
                try:
                    data = res.json()
                    # Validasi: Harus ada isi data/episode
                    if data: 
                        final_res = data
                        print("   ✅ HIT! Target terkunci.")
                        break 
                except:
                    print("   ❌ Bukan JSON Valid.")
            else:
                print(f"   ❌ Gagal (Status: {res.status_code})")
        except Exception as e:
            print(f"   ⚠️ Error Koneksi: {e}")

    if not final_res:
        print("❌ GAGAL TOTAL: Semua link dicoba tapi zonk. Cek ID lagi.")
        return None

    # ==========================================
    # 3. PARSING DATA (OLAH HASIL)
    # ==========================================
    try:
        drama_data = {}
        episodes = []
        data_json = final_res

        # --- A. NETSHORT ---
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
                    'desc': first.get('desc')
                }

        # --- B. DRAMABOX & LAINNYA ---
        else:
            # Kadang ada di dalam 'data', kadang langsung di root
            root_data = data_json.get('data', data_json)

            # RADAR EPISODE (Cari list video)
            episodes = (
                root_data.get('episodes') or 
                root_data.get('episode_list') or 
                root_data.get('chapterList') or 
                root_data.get('chapters') or 
                []
            )
            drama_data = root_data

        # ==========================================
        # 4. FINALISASI
        # ==========================================
        if not episodes:
            print(f"⚠️ JSON masuk tapi Episode Kosong! API mungkin berubah.")
            # Debug buat lu liat isinya apa kalau kosong
            print(f"   🔑 Kunci yang ada: {list(drama_data.keys())}")
            return None

        # Master Radar Info
        poster = (
            drama_data.get('poster') or 
            drama_data.get('cover') or 
            drama_data.get('coverWap') or # Khas Dramabox
            drama_data.get('bookCover')
        )

        title = (
            drama_data.get('title') or 
            drama_data.get('bookName') or # Khas Dramabox
            drama_data.get('name') or 
            f"{platform.upper()}_{drama_id}"
        )
        
        desc = (
            drama_data.get('introduction') or # Khas Dramabox
            drama_data.get('desc') or 
            drama_data.get('description') or 
            "-"
        )

        print(f"✅ SUKSES: {title} | Total: {len(episodes)} Episode")

        return {
            'title': title,
            'poster': poster,
            'desc': desc,
            'episodes': episodes,
            'total_eps': len(episodes)
        }
        
    except Exception as e:
        print(f"❌ Error Parsing ({platform}): {e}")
        return None
