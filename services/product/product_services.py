# services/product/product_services.py
from services.ebay.ebay_services import fetch_products, fetch_single_product
from exceptions.product_exceptions import ExternalAPIError

async def get_products():
    data = await fetch_products()
    
    if not data or "itemSummaries" not in data:
        raise ExternalAPIError()

    items = data.get("itemSummaries", [])
    results = []

    for item in items:
        marketing = item.get("marketingPrice")
        
        original_price = None
        if marketing is not None:
            original_val = marketing.get("originalPrice", {}).get("value", 0.0)
            original_price = float(original_val)

        results.append({
            "id": item.get("itemId"),
            "title": item.get("title"),
            "price": float(item.get("price", {}).get("value", 0.0)),
            "original_price": original_price,
            "image_url": item.get("image", {}).get("imageUrl"),
        })

    return results     

async def get_product_details(product_id: str):
    data = await fetch_single_product(product_id)
    
    if not data:
        raise ExternalAPIError()
    
    return {
        "id": data.get("itemId"),
        "title": data.get("title"),
        "description": data.get("shortDescription"),
        "price": float(data.get("price", {}).get("value", 0.0)),
        "image_url": data.get("image", {}).get("imageUrl"),
    }