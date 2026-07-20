from typing import Optional
from pydantic import BaseModel

class Price(BaseModel):
    value: float
    currency: Optional[str] = None