from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database.base_class import Base


class Shop(Base):
    """
    Shop model representing a physical store location.
    """
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    osm_id = Column(String, nullable=True, unique=True, index=True)  # OpenStreetMap ID
    osm_type = Column(String, nullable=True)  # node, way, relation
    shop_type = Column(String, nullable=True)  # supermarket, convenience, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
