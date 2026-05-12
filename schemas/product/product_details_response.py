# schemas/product/product_details_response.py
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

class ShippingCost(BaseModel):
    value: float
    currency: str
    
    @field_serializer("value")
    def serialize_value(self, v: float) -> float:
        d = Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(d)
    
class Price(BaseModel):
    value: float
    currency: Optional[str] = None

class ShippingOption(BaseModel):
    shippingServiceCode: Optional[str] = None
    type: Optional[str] = None
    shippingCost: Optional[ShippingCost] = None
    additionalShippingCostPerUnit: Optional[ShippingCost] = None
    shippingCostType: Optional[str] = None

class LocalizedAspect(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None

class ProductDetailsResponse(BaseModel):
    id: str
    title: str
    description: str
    price: Price
    image_url: Optional[str] = None
    additional_images: Optional[list[str]] = None
    localized_aspects: list[LocalizedAspect] = []
    shipping_options: list[ShippingOption] = []

    model_config = ConfigDict(from_attributes=True)