# services/cart/cart_services.py
from sqlalchemy import select
from models.cart_model import Cart
from models.cart_item_model import CartItem
from services.ebay.ebay_services import fetch_single_product
from exceptions.product_exceptions import ProductNotFoundError
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from exceptions.cart_exceptions import (
    CartNotFoundError,
    CartItemNotFoundError
)

async def add_to_cart(db, user, payload):
    ebay_product = await fetch_single_product(payload.product_id)

    if not ebay_product:
        raise ProductNotFoundError()

    cart = db.execute(
        select(Cart).where(Cart.user_id == user.id)
    ).scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()

    cart_item = db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == payload.product_id
        )
    ).scalar_one_or_none()

    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        db.add(CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity
        ))

    return {"message": "Added to cart successfully"}


async def get_cart(db, user):
    cart = db.execute(
        select(Cart)
        .where(Cart.user_id == user.id)
        .options(selectinload(Cart.items))
    ).scalar_one_or_none()

    if not cart or not cart.items:
        return {
            "id": getattr(cart, "id", None),
            "items": [],
            "cart_total": 0
        }

    tasks = [fetch_single_product(item.product_id) for item in cart.items]

    ebay_results = await asyncio.gather(*tasks)

    ebay_products_map = {
        res["itemId"]: res for res in ebay_results if res
    }

    items = []
    cart_total = 0

    for item in cart.items:
        product = ebay_products_map.get(item.product_id)

        if not product:
            continue

        price = float(product.get("price", {}).get("value", 0))
        subtotal = price * item.quantity
        cart_total += subtotal

        items.append({
            "product_id": item.product_id,
            "name": product.get("title"),
            "price": price,
            "quantity": item.quantity,
            "image_url": product.get("image", {}).get("imageUrl")
        })

    return {
        "id": cart.id,
        "items": items,
        "cart_total": cart_total
    }
    
    
def remove_cart_item(db, user, product_id):

    cart = db.execute(
        select(Cart).where(Cart.user_id == user.id)
    ).scalar_one_or_none()

    if not cart:
        raise CartNotFoundError()

    cart_item = db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    ).scalar_one_or_none()

    if not cart_item:
        raise CartItemNotFoundError()

    db.delete(cart_item)
    return {"message": "Item removed successfully"}


def clear_cart(db, user):

    cart = db.execute(
        select(Cart).where(Cart.user_id == user.id)
    ).scalar_one_or_none()

    if not cart:
        raise CartNotFoundError()

    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete()

    return {"message": "Cart cleared successfully"}