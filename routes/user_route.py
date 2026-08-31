# routes/user_route.py
from fastapi.params import Depends
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_current_user
from database import get_db
from models.user_model import User
from schemas.auth.user_response import UserResponse
from schemas.user.address_update_request import AddressUpdateRequest

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def me(current_user = Depends(get_current_user)):
    return current_user

@router.put("/me/address")
def update_my_address(
    data: AddressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.address = data.user_address
    current_user.latitude = data.user_latitude
    current_user.longitude = data.user_longitude
    
    db.commit()

    return {"message": "Address updated successfully"}

@router.get("/me/location")
def get_my_location(
    current_user: User = Depends(get_current_user),
):
    if not current_user.latitude or not current_user.longitude:
        current_user.latitude = 0.0
        current_user.longitude = 0.0
        current_user.address = "Location not set"
        
    return {
        "latitude": current_user.latitude,
        "longitude": current_user.longitude,
        "address": current_user.address,
    }