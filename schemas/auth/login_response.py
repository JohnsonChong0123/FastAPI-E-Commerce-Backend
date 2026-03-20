from typing import Literal
from pydantic import BaseModel
from schemas.auth.user_response import UserResponse

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    provider: str
    user: UserResponse