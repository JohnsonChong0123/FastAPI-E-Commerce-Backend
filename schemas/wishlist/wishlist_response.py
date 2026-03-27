from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class WishlistResponse(BaseModel):
    id: UUID
    product_id: str
    name: str
    price: float
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)