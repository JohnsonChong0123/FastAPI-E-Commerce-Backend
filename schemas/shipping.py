from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from pydantic import BaseModel, field_serializer

class ShippingCost(BaseModel):
    value: float
    currency: str
    
    @field_serializer("value")
    def serialize_value(self, v: float) -> float:
        d = Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(d)
    
class ShippingOption(BaseModel):
    shippingServiceCode: Optional[str] = None
    type: Optional[str] = None
    shippingCost: Optional[ShippingCost] = None
    additionalShippingCostPerUnit: Optional[ShippingCost] = None
    shippingCostType: Optional[str] = None
