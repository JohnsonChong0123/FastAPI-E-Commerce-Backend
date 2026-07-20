# services/product/product_services.py
from services.ebay.ebay_services import fetch_products, fetch_single_product
from exceptions.product_exceptions import ExternalAPIError

async def get_products(q: str = "laptop", limit: int = 100):
    data = await fetch_products(q=q, limit=limit)

    if not data or "itemSummaries" not in data:
        raise ExternalAPIError()

    items = data.get("itemSummaries", [])
    results = []

    for item in items:
        marketing = item.get("marketingPrice")
        
        if marketing is not None:
            original_obj = marketing.get("originalPrice", {})
            original_value = float(original_obj.get("value", 0.0))
            original_currency = original_obj.get("currency")
            
        price_obj = item.get("price", {}) or {}
        price_value = float(price_obj.get("value", 0.0))
        price_currency = price_obj.get("currency")

        results.append({
            "id": item.get("itemId"),
            "title": item.get("title"),
            "price": {"value": price_value, "currency": price_currency},
            "original_price": {"value": original_value, "currency": original_currency} if marketing is not None else None,
            "image_url": item.get("image", {}).get("imageUrl"),
        })

    return results     

async def get_product_details(product_id: str):
    data = await fetch_single_product(product_id)
    
    if not data:
        raise ExternalAPIError()
    
    price_obj = data.get("price", {}) or {}
    price_value = float(price_obj.get("value", 0.0))
    price_currency = price_obj.get("currency")
    
    marketing = data.get("marketingPrice")
        
    if marketing is not None:
        original_obj = marketing.get("originalPrice", {})
        original_value = float(original_obj.get("value", 0.0))
        original_currency = original_obj.get("currency")
    
    return {
        "id": data.get("itemId"),
        "title": data.get("title"),
        "description": data.get("shortDescription"),
        "original_price": {"value": original_value, "currency": original_currency} if marketing is not None else None,
        "price": {"value": price_value, "currency": price_currency},
        "image_url": data.get("image", {}).get("imageUrl"),
        "additional_images": [img.get("imageUrl") for img in data.get("additionalImages", [])],
        "localized_aspects": data.get("localizedAspects", []),
        "shipping_options": data.get("shippingOptions", []),
    }