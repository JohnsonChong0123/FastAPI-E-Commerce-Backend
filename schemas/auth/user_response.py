# schemas/auth/user_response.py
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str

    wallet: Decimal | None = None
    address: str | None = None
    phone: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("wallet")
    def serialize_wallet(self, value: Decimal | None):
        if value is None:
            return None
        return float(value)
    