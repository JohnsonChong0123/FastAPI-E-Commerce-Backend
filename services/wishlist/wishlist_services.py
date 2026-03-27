# services/wishlist/wishlist_services.py
import asyncio

from sqlalchemy import delete, select
from models.wishlist_model import Wishlist
from services.ebay.ebay_services import fetch_single_product
from exceptions.product_exceptions import ProductNotFoundError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from exceptions.wishlist_exceptions import (
    WishlistNotFoundError
)

async def add_to_wishlist(db, user, payload):
    ebay_product = await fetch_single_product(payload.product_id)

    if not ebay_product:
        raise ProductNotFoundError()

    wishlist = db.execute(
        select(Wishlist).where(
            Wishlist.user_id == user.id,
            Wishlist.product_id == payload.product_id
        )
    ).scalar_one_or_none()

    if not wishlist:
        db.add(Wishlist(
            user_id=user.id,
            product_id=payload.product_id
        ))

    return {"message": "Added to wishlist successfully"}

async def get_wishlist(db, user):
    wishlist = db.execute(
        select(Wishlist)
        .where(Wishlist.user_id == user.id)
    ).scalars().all()
    
    if not wishlist:
        return []
        # return {
        #     "id": None,
        #     "products_id": None,
        #     "user_id": user.id
        # }
    
    tasks = [fetch_single_product(item.product_id) for item in wishlist]
    
    ebay_results = await asyncio.gather(*tasks)

    ebay_products_map = {
        res["itemId"]: res for res in ebay_results if res
    }

    items = []
    
    for item in wishlist:
        product = ebay_products_map.get(item.product_id)

        if not product:
            continue

        price = float(product.get("price", {}).get("value", 0))
        
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "name": product.get("title"),
            "price": price,
            "image_url": product.get("image", {}).get("imageUrl")
        })

    return items

def remove_wishlist(db, user, product_id):

    wishlist = db.execute(
        select(Wishlist).where(
        Wishlist.user_id == user.id, 
        Wishlist.product_id == product_id)
    ).scalar_one_or_none()

    if not wishlist:
        raise WishlistNotFoundError()

    db.delete(wishlist)
    return {"message": "Wishlist removed successfully"}

def clear_wishlist(db, user):

    stmt = delete(Wishlist).where(Wishlist.user_id == user.id)
    
    result = db.execute(stmt)
    
    if result.rowcount == 0:
        raise WishlistNotFoundError()
    
    return {"message": "Wishlist cleared successfully"}