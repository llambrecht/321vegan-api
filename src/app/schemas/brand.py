from pydantic import BaseModel
from typing import List, Optional
import datetime

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
    created_at: datetime.datetime
    updated_at: datetime.datetime

class BrandOut(BaseModel):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str
    parent: Optional[Brand] = None

    class Config:
        from_attributes = True

class BrandOutPaginated(BaseModel):
    items: List[BrandOut]
    total: int
    page: int
    size: int
    pages: int

class BrandFilters(BaseModel):
    name: Optional[str] = None
    parent_name: Optional[int] = None