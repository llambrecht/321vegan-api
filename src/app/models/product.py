from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base
import enum

class ProductState(str, enum.Enum):
    CREATED = "CREATED"
    NEED_CONTACT = "NEED_CONTACT"
    WAITING_REPLY = "WAITING_BRAND_REPLY"
    NOT_FOUND = "NOT_FOUND"
    WAITING_PUBLISH = "WAITING_PUBLISH"
    PUBLISHED = "PUBLISHED"

class ProductStatus(str, enum.Enum):
    VEGAN = "VEGAN"
    NON_VEGAN = "NON_VEGAN"
    MAYBE_VEGAN = "MAYBE_VEGAN"
    NOT_FOUND = "NOT_FOUND"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ean = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    description = Column(Text)
    problem_description = Column(Text)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    brand = relationship("Brand", back_populates="products")
    brand_name = Column(String, index=True, nullable=True)
    status = Column(Enum(ProductStatus), default=ProductStatus.MAYBE_VEGAN)
    biodynamic = Column(Boolean, default=False)
    state = Column(Enum(ProductState), default=ProductState.CREATED)
    created_from_off = Column(Boolean, default=False)

