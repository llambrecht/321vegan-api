from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.brand import Brand

class CheckingUserOut(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None

class CheckingProductOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    ean: str
    name: Optional[str] = None
    description: Optional[str] = None
    problem_description: Optional[str] = None
    brand: Optional[Brand] = None
    status: str
    biodynamic: bool
    state: str 
    created_from_off: bool

class Checking(BaseModel):
    id: int


class CheckingBase(BaseModel):
    requested_on: Optional[datetime] = None
    responded_on: Optional[datetime] = None
    response: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None
    product_id: int


class CheckingCreate(CheckingBase):
    pass


class CheckingUpdate(CheckingBase):
    pass


class CheckingInDB(CheckingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int


class CheckingOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    requested_on: datetime
    responded_on: Optional[datetime] = None
    response: Optional[str] = None
    status: str
    user: CheckingUserOut
    product: CheckingProductOut

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class CheckingOutPaginated(BaseModel):
    items: List[CheckingOut]
    total: int
    page: int
    size: int
    pages: int


class CheckingOutCount(BaseModel):
    total: int


class CheckingFilters(BaseModel):
    status: Optional[str] = None
    requested_on: Optional[str] = None
    requested_on__gt: Optional[str] = None
    responded_on: Optional[str] = None
    responded_on__gt: Optional[str] = None
    user___nickname__ilike: Optional[str] = None
    product___ean: Optional[str] = None
    product_id: Optional[str] = None
    
class CheckingOutForProduct(BaseModel):
    id: int
    requested_on: datetime
    responded_on: Optional[datetime] = None
    response: Optional[str] = None
    status: str
    user: CheckingUserOut

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }