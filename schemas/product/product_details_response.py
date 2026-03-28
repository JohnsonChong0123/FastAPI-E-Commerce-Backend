# schemas/product/product_sum_response.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductDetailsResponse(BaseModel):
    id: str
    title: str
    description: str
    price: float
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)