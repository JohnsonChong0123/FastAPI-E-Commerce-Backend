# schemas/product/product_sum_response.py
from typing import Optional
from pydantic import BaseModel, ConfigDict

from schemas.product.price_response import Price


class ProductSummaryResponse(BaseModel):
    id: str
    title: str
    price: Price
    original_price: Optional[Price] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)