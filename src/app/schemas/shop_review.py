from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from app.models.shop_review import ShopReviewStatus


class ShopReviewCreate(BaseModel):
    shop_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    user_id: Optional[int] = None


class ShopReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class ShopReviewStatusUpdate(BaseModel):
    status: ShopReviewStatus


class ShopReviewOut(BaseModel):
    id: int
    shop_id: int
    user_id: Optional[int] = None
    user_nickname: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    status: ShopReviewStatus
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }


class ShopReviewOutPaginated(BaseModel):
    items: list[ShopReviewOut]
    total: int
    page: int
    size: int
    pages: int


class ShopReviewFilters(BaseModel):
    """Filters for shop reviews search."""
    shop_id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[ShopReviewStatus] = None


class ShopReviewSummaryOut(BaseModel):
    shop_id: int
    review_count: int
    rating_avg: float
