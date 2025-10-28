"""
District schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DistrictBase(BaseModel):
    name: str
    province_id: int


class DistrictCreate(DistrictBase):
    pass


class DistrictResponse(DistrictBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
