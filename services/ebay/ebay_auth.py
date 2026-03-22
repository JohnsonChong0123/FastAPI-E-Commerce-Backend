# services/ebay/ebay_auth.py
import httpx
import base64
from core.config import settings
from core.decoration import handle_api_errors

@handle_api_errors(service_name="eBay-OAuth")
async def get_ebay_access_token():
    client_id = settings.EBAY_CLIENT_ID
    client_secret = settings.EBAY_CLIENT_SECRET
    
    b64_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope" 
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)
        # This will raise an HTTPStatusError for non-2xx responses, which our decorator will catch and log
        response.raise_for_status() 
        
        token = response.json().get("access_token")
        if not token:
            raise ValueError("Token missing in response payload")
            
        return token