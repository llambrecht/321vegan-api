from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ShopBase(BaseModel):
    name: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    osm_id: Optional[str] = None
    osm_type: Optional[str] = None
    shop_type: Optional[str] = None


class ShopCreate(ShopBase):
    pass


class ShopUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    osm_id: Optional[str] = None
    osm_type: Optional[str] = None
    shop_type: Optional[str] = None


class ShopInDB(ShopBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ShopOut(ShopInDB):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class ShopOutPaginated(BaseModel):
    items: list[ShopOut]
    total: int
    page: int
    size: int
    pages: int


class ShopFilters(BaseModel):
    """Filters for shops search."""
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    shop_type: Optional[str] = None
    ean__in: Optional[str] = None
