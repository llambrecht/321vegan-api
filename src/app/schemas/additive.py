from pydantic import BaseModel, Field
from fastapi import Query
from typing import List, Optional
from datetime import datetime, timezone


class Additive(BaseModel):
    id: int
    e_number: str
    name: Optional[str] = None


class AdditiveBase(BaseModel):
    e_number: str = Field(..., min_length=1)
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None


class AdditiveCreate(AdditiveBase):
    pass


class AdditiveUpdate(AdditiveBase):
    pass


class AdditiveInDB(AdditiveBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AdditiveOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    e_number: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    source: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class AdditiveOutPaginated(BaseModel):
    items: List[AdditiveOut]
    total: int
    page: int
    size: int
    pages: int


class AdditiveOutCount(BaseModel):
    total: int


class AdditiveFilters(BaseModel):
    e_number: Optional[str] = None
    e_number__ilike: Optional[str] = None
    e_number__contains: Optional[str] = None
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_at__gt: Optional[str] = None
