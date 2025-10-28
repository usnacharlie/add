"""
Province schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProvinceBase(BaseModel):
    name: str


class ProvinceCreate(ProvinceBase):
    pass


class ProvinceResponse(ProvinceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
