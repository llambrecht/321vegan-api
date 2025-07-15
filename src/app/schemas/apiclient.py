from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ApiClientBase(BaseModel):
    api_key: str = Field(..., min_length=1)
    is_active: bool = False


class ApiClientCreate(ApiClientBase):
    name: str


class ApiClientUpdate(ApiClientBase):
    name: str


class ApiClientInDB(ApiClientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str


class ApiClientOut(ApiClientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class ApiClientOutPaginated(BaseModel):
    items: List[ApiClientOut]
    total: int
    page: int
    size: int
    pages: int


class ApiClientFilters(BaseModel):
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    api_key: Optional[str] = None
    api_key__ilike: Optional[str] = None
    api_key__contains: Optional[str] = None
    is_active: Optional[str] = None
