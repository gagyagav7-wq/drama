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
    # 1. TARGET URL
    # ==========================================
    urls_to_try = []

    if platform == 'dramabox':
        urls_to_try = [
            f"{BASE_URL}/dramabox/allepisode?bookId={drama_id}",       # Target Utama
            f"{BASE_URL}/dramabox/detailAndAllEpisode?bookId={drama_id}", 
            f"{BASE_URL}/dramabox/episode?bookId={drama_id}"
        ]
    elif platform == 'netshort':
        urls_to_try = [f"{BASE_URL}/netshort/allepisode?shortPlayId={drama_id}"]
    elif platform == 'flickreels':
        urls_to_try = [f"{BASE_URL}/flickreels/{drama_id}"]
    else:
        urls_to_try = [f"{BASE_URL}/{platform}/{drama_id}"]

    # ==========================================
    # 2. EKSEKUSI REQUEST
    # ==========================================
    final_res = None
    
    for url in urls_to_try:
        try:
            print(f"👉 Nembak ke: {url}")
            res = requests.get(url, headers=headers, timeout=30)
            
            if res.status_code == 200:
                try:
                    data = res.json()
                    if data: 
                        final_res = data
                        print("   ✅ HIT! Data masuk.")
                        break 
                except:
                    print("   ❌ Bukan JSON Valid.")
            else:
                print(f"   ❌ Gagal (Status: {res.status_code})")
        except Exception as e:
            print(f"   ⚠️ Error Koneksi: {e}")

    if not final_res:
        print("❌ GAGAL TOTAL: Cek ID atau Server.")
        return None

    # ==========================================
    # 3. PARSING CERDAS (LIST vs OBJECT)
    # ==========================================
    try:
        drama_data = {}
        episodes = []
        
        # --- LOGIKA 1: Kalo datanya langsung LIST [...] (Kayak Netshort/Dramabox Allepisode) ---
        if isinstance(final_res, list):
            episodes = final_res
            # Ambil info drama dari episode pertama
            if episodes:
                drama_data = episodes[0]

        # --- LOGIKA 2: Kalo datanya OBJECT {...} (Kayak Flickreels/Standard) ---
        elif isinstance(final_res, dict):
            # Kadang dibungkus 'data', kadang nggak
            root = final_res.get('data', final_res)
            
            # Cek lagi, dalem 'data' isinya List atau Object?
            if isinstance(root, list):
                episodes = root
                if episodes: drama_data = episodes[0]
            else:
                # Struktur Object Standard
                episodes = (
                    root.get('episodes') or 
                    root.get('episode_list') or 
                    root.get('chapterList') or 
                    root.get('chapters') or 
                    []
                )
                drama_data = root

        # ==========================================
        # 4. AMBIL DATA FINAL
        # ==========================================
        if not episodes:
            print(f"⚠️ Data kosong! (0 Episode)")
            return None

        # Master Radar (Cari Poster/Judul dimanapun dia ngumpet)
        poster = (
            drama_data.get('poster') or 
            drama_data.get('cover') or 
            drama_data.get('coverWap') or # Khas Dramabox
            drama_data.get('bookCover') or
            drama_data.get('shortPlayCover')
        )

        title = (
            drama_data.get('title') or 
            drama_data.get('bookName') or # Khas Dramabox
            drama_data.get('name') or 
            drama_data.get('dramaTitle') or
            drama_data.get('shortPlayName') or
            f"{platform.upper()}_{drama_id}"
        )
        
        desc = (
            drama_data.get('introduction') or 
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
        import traceback
        traceback.print_exc() # Print detail error biar kita tau baris mana
        return None
        
