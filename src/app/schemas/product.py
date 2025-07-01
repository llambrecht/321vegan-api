from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.brand import Brand
import datetime

class Product(BaseModel):
    id: int
    ean: str
    name: Optional[str] = None

class ProductBase(BaseModel):
    ean: str = Field(..., min_length=1)
    name: Optional[str] = None
    description: Optional[str] = None
    problem_description: Optional[str] = None
    brand_id: Optional[int] = None
    status: str = Field(..., min_length=1)
    biodynamic: bool
    state: str = Field(..., min_length=1)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductInDB(ProductBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_from_off: bool

class ProductOut(BaseModel):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    ean: str
    name: Optional[str] = None
    description: Optional[str] = None
    problem_description: Optional[str] = None
    brand: Optional[Brand] = None
    status: str
    biodynamic: bool
    state: str 
    created_from_off: bool

    class Config:
        from_attributes = True

class ProductOutPaginated(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    size: int
    pages: int

class ProductFilters(BaseModel):
    name: Optional[str] = None
    brand_name: Optional[str] = None
    status: Optional[str] = None
    state: Optional[str] = None