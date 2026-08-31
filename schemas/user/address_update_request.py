from pydantic import BaseModel

class AddressUpdateRequest(BaseModel):
    user_address: str
    user_latitude: float
    user_longitude: float
