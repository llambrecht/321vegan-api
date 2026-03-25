from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from app.schemas.brand import Brand
from app.schemas.product_category import ProductCategory


class Product(BaseModel):
    id: int
    ean: str
    name: Optional[str] = None


class InterestingProductBase(BaseModel):
    ean: str = Field(..., min_length=1)
    name: Optional[str] = None
    image: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(popular|sponsored)$")
    category_id: int
    brand_id: Optional[int] = None


class InterestingProductCreate(InterestingProductBase):
    alternative_products: list[Optional[int]] = []


class InterestingProductUpdate(InterestingProductBase):
    alternative_products: list[Optional[int]] = []


class InterestingProductInsert(InterestingProductBase):
    pass


class InterestingProductUploadImage(BaseModel):
    image: str


class InterestingProductInDB(InterestingProductBase):
    id: int
    created_at: datetime
    updated_at: datetime


class InterestingProductOut(InterestingProductInDB):
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    brand: Optional[Brand] = None
    category: Optional[ProductCategory] = None
    alternative_eans: list[Optional[str]] = []
    product: Optional[Product] = None
    alternative_products: list[Optional[Product]] = []
    eans: list[str] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class InterestingProductOutPaginated(BaseModel):
    items: list[InterestingProductOut]
    total: int
    page: int
    size: int
    pages: int


class InterestingProductFilters(BaseModel):
    """Filters for interesting products search."""
    ean: Optional[str] = None
    ean__ne: Optional[str] = None
    eans__any: Optional[str] = None
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    brand: Optional[str] = None
    brand___name__contains: Optional[str] = None
    brand___name__lookalike: Optional[str] = None
    brand___id: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(popular|sponsored)$")
    category_id: Optional[int] = None
    category___name__contains: Optional[str] = None
    category___name__lookalike: Optional[str] = None
    category___id: Optional[str] = None
    created_at: Optional[str] = None
    created_at__gt: Optional[str] = None
