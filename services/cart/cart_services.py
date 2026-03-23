from sqlalchemy import select
from models.cart_model import Cart
from models.cart_item_model import CartItem
from services.ebay.ebay_services import fetch_single_product
from exceptions.product_exceptions import ProductNotFoundError

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