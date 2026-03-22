# routes/user_route.py
from fastapi.params import Depends
from fastapi import APIRouter, Depends
from core.deps import get_current_user
from schemas.auth.user_response import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def me(current_user = Depends(get_current_user)):
    return current_user