from typing import List, Optional
from pydantic import BaseModel, EmailStr
import datetime

class UserBase(BaseModel):
    role: str
    email: EmailStr
    nickname: str
    is_active: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    pass

class UserInDB(UserBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    avatar: Optional[str] = None
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    avatar: Optional[str] = None

class UserOutPaginated(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    size: int
    pages: int

class UserFilters(BaseModel):
    nickname: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class UserUpdateOwn(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None