# schemas/auth/register_request.py
import string
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    """Schema for user registration request."""
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    
    @field_validator("email") 
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()
    
    @field_validator("first_name", "last_name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()  
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):      
            raise ValueError("Password must contain a number")
        if not any(c in string.punctuation for c in v):
            raise ValueError("Password must contain a special character (!@#$...)")
        return v