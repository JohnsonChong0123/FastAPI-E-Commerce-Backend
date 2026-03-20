# routes/auth_route.py
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends
from schemas.auth.google_login_request import GoogleLoginRequest
from schemas.auth.login_request import LoginRequest
from schemas.auth.login_response import LoginResponse
from schemas.auth.register_request import RegisterRequest
from schemas.auth.user_response import UserResponse
from services.auth import google_login_services, login_services, register_services

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    return register_services.register(db, data) 

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return access and refresh tokens."""
    return login_services.login(db, data)

@router.post("/google")
def google_login(
    data: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    result = google_login_services.login_with_google(db, data.id_token)
    print(f"Google login result: {result['user']}")

    return {
        **result,
        "user": UserResponse.model_validate(result["user"])
    }
