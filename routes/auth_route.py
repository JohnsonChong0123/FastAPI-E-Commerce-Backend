# routes/auth_route.py
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends
from schemas.auth.login_request import LoginRequest
from schemas.auth.login_response import LoginResponse
from schemas.auth.register_request import RegisterRequest
from services.auth import login_services, register_services

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    return register_services.register(db, data) 

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return access and refresh tokens."""
    return login_services.login(db, data)
