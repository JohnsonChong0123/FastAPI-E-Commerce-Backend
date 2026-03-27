# schemas/wishlist/wishlist_create.py
from pydantic import BaseModel, Field

class WishlistCreate(BaseModel):
    product_id: str = Field(..., min_length=1)