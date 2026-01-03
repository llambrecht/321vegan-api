import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class InterestingProductType(str, enum.Enum):
    popular = "popular"
    sponsored = "sponsored"


class InterestingProduct(Base):
    __tablename__ = "interesting_products"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ean = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    image = Column(String, nullable=True)
    type = Column(Enum(InterestingProductType), nullable=False, default=InterestingProductType.popular)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    
    # Relationships
    category = relationship("ProductCategory", back_populates="interesting_products")
    brand = relationship("Brand")
    
    @property
    def category_name(self) -> str | None:
        """Get the category name"""
        return self.category.name if self.category else None
    
    @property
    def brand_name(self) -> str | None:
        """Get the brand name"""
        return self.brand.name if self.brand else None
