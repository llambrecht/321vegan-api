from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base
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


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    biodynamic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ean = Column(String, nullable=False)
    name = Column(String)
    description = Column(Text)
    problem_description = Column(Text)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    status = Column(Enum(ProductStatus), default=ProductStatus.MAYBE_VEGAN)
    state = Column(Enum(ProductState), default=ProductState.CREATED)
    created_from_off = Column(Boolean, default=False)
