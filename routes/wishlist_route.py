# routes/wishlist_route.py
from typing import List

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
from schemas.wishlist.wishlist_create import WishlistCreate
from schemas.wishlist.wishlist_response import WishlistResponse
from services.cart import cart_services
from services.wishlist import wishlist_services

router = APIRouter()

@router.post("/add")
async def add_wishlist(
    payload: WishlistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await wishlist_services.add_to_wishlist(db, user, payload)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.get("", response_model=List[WishlistResponse])
async def get_wishlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await wishlist_services.get_wishlist(db, user)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.delete("/remove/{product_id}")
def remove_wishlist(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = wishlist_services.remove_wishlist(db, user, product_id)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.delete("/clear")
def clear_wishlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = wishlist_services.clear_wishlist(db, user)
        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )