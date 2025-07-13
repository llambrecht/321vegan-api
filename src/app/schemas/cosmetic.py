from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class CosmeticCreate(BaseModel):
    brand_name: str
    is_vegan: bool = False
    is_cruelty_free: bool = False
    description: Optional[str] = None

class CosmeticUpdate(BaseModel):
    brand_name: Optional[str] = None
    is_vegan: Optional[bool] = None
    is_cruelty_free: Optional[bool] = None
    description: Optional[str] = None

class CosmeticOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    brand_name: str
    is_vegan: bool
    is_cruelty_free: bool
    description: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }

class CosmeticOutPaginated(BaseModel):
    items: list[CosmeticOut]
    total: int
    page: int
    size: int
    pages: int

class CosmeticFilters(BaseModel):
    brand_name: Optional[str] = None
    brand_name__ilike: Optional[str] = None
    brand_name__contains: Optional[str] = None
    is_vegan: Optional[bool] = None
    is_cruelty_free: Optional[bool] = None
