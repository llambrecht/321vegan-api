from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

class Brand(BaseModel):
    id: int
    name: str

class BrandBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BrandBase):
    pass

class BrandInDB(BrandBase):
    id: int
    created_at: datetime
    updated_at: datetime

class BrandOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    parent: Optional[Brand] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }

class BrandOutPaginated(BaseModel):
    items: List[BrandOut]
    total: int
    page: int
    size: int
    pages: int

class BrandFilters(BaseModel):
    name: Optional[str] = None
    parent: Optional[str] = None