import httpx
from core.decoration import handle_api_errors
from exceptions.product_exceptions import EbayAuthError
from services.ebay.ebay_auth import get_ebay_access_token

@handle_api_errors(service_name="eBay-Search")
async def fetch_products(q: str = "laptop", limit: int = 100):
    try:
        token = await get_ebay_access_token()
    except Exception:
        raise EbayAuthError()

    ebay_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    params = {
        "q": q,
        "limit": limit,
        "filter": "conditions:{NEW}",
        "sort": "newlyListed"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(ebay_url, headers=headers, params=params)
        response.raise_for_status() 

    return response.json()

@handle_api_errors(service_name="eBay-Item-Detail")
async def fetch_single_product(item_id: str):
    """
    Fetch details for a single product based on the eBay itemId.
    """
    try:
        token = await get_ebay_access_token()
    except Exception:
        raise EbayAuthError()

    ebay_url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(ebay_url, headers=headers)    
        response.raise_for_status()
    return response.json()