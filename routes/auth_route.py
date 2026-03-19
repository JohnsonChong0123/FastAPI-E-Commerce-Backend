# routes/auth.py
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends
from schemas.auth.register_request import RegisterRequest
from services import auth_services

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    return auth_services.register(db, data) 
