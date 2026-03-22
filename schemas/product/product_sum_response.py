# schemas/product/product_sum_response.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductSummaryResponse(BaseModel):
    id: str
    title: str
    price: float
    original_price: Optional[float] = None 
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)