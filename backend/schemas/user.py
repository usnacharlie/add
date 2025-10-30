"""
User schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    pin: str = Field(..., min_length=4, max_length=6)
    full_name: str
    role: str = "member"  # admin, coordinator, member, viewer
    member_id: Optional[int] = None


class UserLogin(BaseModel):
    identifier: str  # Can be email or phone
    pin: str


class UserResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    full_name: str
    role: str
    is_active: bool
    member_id: Optional[int]
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    member_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
