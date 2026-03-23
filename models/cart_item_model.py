# models/cart_item_model.py
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import VARCHAR, Column, Integer, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, validates
from models.base import Base

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(
        UUID(as_uuid=True),
        ForeignKey("carts.id"),
        nullable=False
    )

    product_id = Column(VARCHAR(50), nullable=False) 
    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    
    def __init__(self, **kwargs):
        kwargs.setdefault("quantity", 1) 
        super().__init__(**kwargs)