"""
Ward schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WardBase(BaseModel):
    name: str
    constituency_id: int


class WardCreate(WardBase):
    pass


class WardResponse(WardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
