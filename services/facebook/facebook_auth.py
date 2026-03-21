import requests


def verify_facebook_token(token: str):
    try:
        url = "https://graph.facebook.com/me"
        params = {
            "fields": "id,name,email",
            "access_token": token,
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return None
        data = res.json()
        if "error" in data:                
            return None
        return data
    except Exception:
        return None