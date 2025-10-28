"""
Constituency schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConstituencyBase(BaseModel):
    name: str
    district_id: int


class ConstituencyCreate(ConstituencyBase):
    pass


class ConstituencyResponse(ConstituencyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
