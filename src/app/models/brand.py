from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, unique=True, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    children = relationship("Brand", back_populates="parent")
    parent = relationship("Brand", back_populates="children", remote_side=[id])
    products = relationship("Product", back_populates="brand")