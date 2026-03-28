from pydantic import BaseModel, Field, field_validator

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

    @field_validator("refresh_token")
    @classmethod
    def must_not_be_whitespace(cls, v):
        if not v.strip():
            raise ValueError("refresh_token cannot be whitespace")
        return v