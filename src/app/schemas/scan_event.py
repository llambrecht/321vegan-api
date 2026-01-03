from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ScanEventBase(BaseModel):
    ean: str = Field(..., min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    shop_name: Optional[str] = None
    lookup_api_response: Optional[str] = None
    user_id: Optional[int] = None


class ScanEventCreate(ScanEventBase):
    pass


class ScanEventUpdate(BaseModel):
    ean: Optional[str] = Field(None, min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    shop_name: Optional[str] = None
    lookup_api_response: Optional[str] = None
    user_id: Optional[int] = None


class ScanEventInDB(ScanEventBase):
    id: int
    date_created: datetime


class ScanEventOut(ScanEventInDB):
    user_nickname: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class ScanEventOutPaginated(BaseModel):
    items: list[ScanEventOut]
    total: int
    page: int
    size: int
    pages: int
