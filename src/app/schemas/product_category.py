from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_category_id: Optional[int] = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_category_id: Optional[int] = None


class ProductCategoryInDB(ProductCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ProductCategoryOut(ProductCategoryInDB):
    parent_category_name: Optional[str] = None
    category_tree: list[str] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class ProductCategoryOutPaginated(BaseModel):
    items: list[ProductCategoryOut]
    total: int
    page: int
    size: int
    pages: int
