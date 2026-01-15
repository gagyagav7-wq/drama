import requests

def get_drama_data(platform, drama_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    platform = platform.lower()
    
    try:
        if platform == 'netshort':
            info = requests.get(f"https://api.sansekai.my.id/api/netshort/detail?shortPlayId={drama_id}", headers=headers).json()
            eps = requests.get(f"https://api.sansekai.my.id/api/netshort/allEpisode?shortPlayId={drama_id}", headers=headers).json()
            return {
                'title': info.get('shortPlayName') or info.get('title'),
                'poster': info.get('shortPlayCover') or info.get('poster'),
                'desc': info.get('shotIntroduce') or info.get('description'),
                'episodes': eps if isinstance(eps, list) else eps.get('episodeList', [])
            }
        
        url = f"https://api.sansekai.my.id/api/dramabox/detailAndAllEpisode?bookId={drama_id}" if platform == 'dramabox' else f"https://api.sansekai.my.id/api/{platform}/detailAndAllEpisode?id={drama_id}"
        res = requests.get(url, headers=headers).json()
        drama_data = res.get('drama', {})
        return {
            'title': drama_data.get('title'),
            'poster': drama_data.get('poster'),
            'desc': drama_data.get('description'),
            'episodes': res.get('episodes', [])
        }
    except Exception as e:
        print(f"Error API: {e}")
        return None
      
