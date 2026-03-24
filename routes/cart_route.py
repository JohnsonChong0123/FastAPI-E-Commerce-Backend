# routes/cart_route.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from database import get_db
from core.deps import get_current_user
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User
from schemas.cart.cart_create import CartItemCreate
from schemas.cart.cart_response import CartItemResponse, CartResponse
from services.cart import cart_services

router = APIRouter()

@router.post("/add")
async def add_to_cart(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await cart_services.add_to_cart(db, user, payload)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.get("", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await cart_services.get_cart(db, user)

@router.delete("/remove/{product_id}")
def delete_cart_item(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = cart_services.remove_cart_item(db, user, product_id)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/clear")
def clear_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = cart_services.clear_cart(db, user)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )