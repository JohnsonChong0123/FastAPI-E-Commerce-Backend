# schemas/auth/facebook_login_request.py
from pydantic import BaseModel, Field

class FacebookLoginRequest(BaseModel):
    access_token: str = Field(min_length=1)