# schemas/cart/cart_create.py
from pydantic import BaseModel, Field, field_validator

class CartItemCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)