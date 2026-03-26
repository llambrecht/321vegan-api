import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, select, or_
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.database.base_class import Base
from app.models.brand import Brand
from app.models.product import Product
from app.models.product_category import ProductCategory


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
    type = Column(Enum(InterestingProductType), nullable=False,
                  default=InterestingProductType.popular)
    category_id = Column(Integer, ForeignKey(
        "product_categories.id"), nullable=False)
    category = relationship(
        "ProductCategory", back_populates="interesting_products")
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    brand = relationship("Brand", back_populates="interesting_products")
    # Relationships
    alternative_products = relationship("Product",
                                        back_populates="interesting_product")

    # orm only foreignkey
    product = relationship(
        'Product',
        primaryjoin="foreign(InterestingProduct.ean) == Product.ean"
    )

    @hybrid_property
    def category_name(self) -> str | None:
        if self.category:
            return self.category.name
        else:
            return None

    @category_name.inplace.expression
    @classmethod
    def _category_name_expression(cls):
        """SQL expression for retrieving category name."""
        return (
            select(ProductCategory.name)
            .where(ProductCategory.id == cls.category_id)
            .as_scalar()
        )

    @hybrid_property
    def brand_name(self) -> str | None:
        if self.brand:
            return self.brand.name
        else:
            return None

    @brand_name.inplace.expression
    @classmethod
    def _brand_name_expression(cls):
        """SQL expression for retrieving brand name."""
        return (
            select(Brand.name)
            .where(Brand.id == cls.brand_id)
            .as_scalar()
        )

    @hybrid_property
    def alternative_eans(self) -> list[str]:
        return [p.ean for p in self.alternative_products]

    @alternative_eans.inplace.expression
    @classmethod
    def _alternative_eans_expression(cls):
        """SQL expression for retrieving alternative eans."""
        return (
            select(Product.ean)
            .where(Product.interesting_product_id == cls.id)
            .as_scalar()
        )

    @hybrid_property
    def eans(self) -> list[str]:
        return [self.ean, *self.alternative_eans]

    @eans.inplace.expression
    @classmethod
    def _eans_expression(cls):
        """SQL expression for retrieving all eans."""
        return (
            select(Product.ean).where(
                or_(
                    Product.ean == cls.ean,
                    Product.interesting_product_id == cls.id
                )
            ).scalar_subquery()
        )
