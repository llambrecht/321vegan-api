from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone


class ProductNotFoundReportCreate(BaseModel):
    ean: str
    shop_id: int
    user_id: Optional[int] = None


class ProductNotFoundReportOut(BaseModel):
    id: int
    ean: str
    shop_id: int
    user_id: Optional[int] = None
    date_created: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }
