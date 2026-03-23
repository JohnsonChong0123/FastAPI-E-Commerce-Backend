from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from core.deps import get_current_user
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User
from schemas.cart.cart_create import CartItemCreate
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