from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.database.base_class import Base

class Cosmetic(Base):
    __tablename__ = "cosmetics"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    brand_name = Column(String, unique=True, index=True, nullable=False)
    is_vegan = Column(Boolean, default=False)
    is_cruelty_free = Column(Boolean, default=False)
    description = Column(Text)