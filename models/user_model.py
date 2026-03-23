# models/user_model.py
import uuid
import hashlib
from sqlalchemy import Column, Float, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    phone = Column(String)
    
    image_url = Column(String, nullable=True)
    
    wallet = Column(Numeric(10, 2), default=0)
    provider = Column(String, default="email")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    avatar_key = Column(String, nullable=True)

    @property
    def avatar(self):
        """
        Returns the URL of the user's avatar. If the user has an image_url, it returns that.
        """
        if self.image_url:
            return self.image_url
        
        email_hash = hashlib.md5(self.email.strip().lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=200"
    
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
