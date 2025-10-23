from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone

class UserBase(BaseModel):
    role: str
    email: EmailStr
    nickname: str
    is_active: bool = False
    vegan_since: Optional[datetime] = None
    nb_products_sent: Optional[int] = 0

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    avatar: Optional[str] = None
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    avatar: Optional[str] = None
    roles: List
    nb_products_sent: int = 0

    @field_validator('nb_products_sent', mode='before')
    @classmethod
    def validate_nb_products_sent(cls, v):
        """Convert None to 0 for nb_products_sent"""
        return 0 if v is None else v

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        }

class UserOutPaginated(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    size: int
    pages: int

class UserFilters(BaseModel):
    nickname: Optional[str] = None
    nickname__ilike: Optional[str] = None
    nickname__contains: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[str] = None

class UserUpdateOwn(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None
    vegan_since: Optional[datetime] = None

class UserPatch(BaseModel):
    """Schema for partial user updates (PATCH requests)"""
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    is_active: Optional[bool] = None
    vegan_since: Optional[datetime] = None
    nb_products_sent: Optional[int] = None
    password: Optional[str] = None
