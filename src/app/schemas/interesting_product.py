from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class InterestingProductBase(BaseModel):
    ean: str = Field(..., min_length=1)
    name: Optional[str] = None
    image: Optional[str] = None
    type: str = Field(..., pattern="^(popular|sponsored)$")
    category_id: int
    brand_id: Optional[int] = None


class InterestingProductCreate(InterestingProductBase):
    pass


class InterestingProductUpdate(BaseModel):
    ean: Optional[str] = Field(None, min_length=1)
    name: Optional[str] = None
    image: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(popular|sponsored)$")
    category_id: Optional[int] = None
    brand_id: Optional[int] = None


class InterestingProductInDB(InterestingProductBase):
    id: int
    created_at: datetime
    updated_at: datetime


class InterestingProductOut(InterestingProductInDB):
    category_name: Optional[str] = None
    brand_name: Optional[str] = None

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
    type: Optional[str] = Field(None, pattern="^(popular|sponsored)$")
    category_id: Optional[int] = None
