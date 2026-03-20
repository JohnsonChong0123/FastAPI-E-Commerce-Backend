from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    
    @field_validator("email")
    @classmethod    
    def normalize_email(cls, v: EmailStr) -> str:
        return v.strip().lower()