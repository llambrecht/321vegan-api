from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, nullable=False, unique=True, index=True)
    parent_category_id = Column(Integer, ForeignKey(
        "product_categories.id"), nullable=True)
    image = Column(String, nullable=True)


    # Self-referential relationship for hierarchical categories
    parent = relationship(
        "ProductCategory", back_populates="children", remote_side=[id])
    children = relationship("ProductCategory", back_populates="parent")

    # Relationship with interesting products
    interesting_products = relationship(
        "InterestingProduct", back_populates="category")

    @property
    def parent_category_name(self) -> str | None:
        """Get the parent category name if it exists"""
        return self.parent.name if self.parent else None

    @property
    def category_tree(self) -> list:
        """Get the full category tree from root to this category"""
        if self.parent:
            return self.parent.category_tree + [self.name]
        return [self.name]

    @property
    def nb_interesting_products(self) -> int:
        """Return the number of interesting_products made by the user"""
        return len(self.interesting_products) if self.interesting_products else 0
