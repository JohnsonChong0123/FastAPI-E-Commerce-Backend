from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional


class CartItemResponse(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: UUID
    items: List[CartItemResponse]
    cart_total: float

    model_config = ConfigDict(from_attributes=True)