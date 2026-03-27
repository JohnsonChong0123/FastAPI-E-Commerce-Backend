# models/wishlist_model.py
import uuid
from sqlalchemy import VARCHAR, Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base

class Wishlist(Base):
    __tablename__ = "wishlists"
     
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    product_id = Column(VARCHAR(50), nullable=False) 
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_wishlist'),
    )

    user = relationship("User", back_populates="wishlist") 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = uuid.uuid4()
