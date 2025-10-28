"""
Member schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from enum import Enum


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class MemberBase(BaseModel):
    name: str
    gender: Gender
    date_of_birth: Optional[date] = None
    age: Optional[int] = None  # Keep for backward compatibility
    nrc: Optional[str] = None
    voters_id: Optional[str] = None
    contact: Optional[str] = None
    ward_id: int


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    nrc: Optional[str] = None
    voters_id: Optional[str] = None
    contact: Optional[str] = None
    ward_id: Optional[int] = None


class MemberResponse(MemberBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
