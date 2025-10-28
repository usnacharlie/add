"""
Ward API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.config.database import get_db
from backend.schemas.ward import WardCreate, WardResponse
from backend.services.ward_service import WardService

router = APIRouter()


@router.post("/", response_model=WardResponse, status_code=201)
def create_ward(ward: WardCreate, db: Session = Depends(get_db)):
    """Create a new ward"""
    return WardService.create_ward(db, ward)


@router.get("/", response_model=List[WardResponse])
def get_wards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all wards"""
    return WardService.get_all_wards(db, skip, limit)


@router.get("/constituency/{constituency_id}", response_model=List[WardResponse])
def get_wards_by_constituency(constituency_id: int, db: Session = Depends(get_db)):
    """Get all wards in a constituency"""
    return WardService.get_wards_by_constituency(db, constituency_id)


@router.get("/{ward_id}", response_model=WardResponse)
def get_ward(ward_id: int, db: Session = Depends(get_db)):
    """Get a specific ward"""
    ward = WardService.get_ward(db, ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@router.delete("/{ward_id}", status_code=204)
def delete_ward(ward_id: int, db: Session = Depends(get_db)):
    """Delete a ward"""
    success = WardService.delete_ward(db, ward_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ward not found")
    return None
