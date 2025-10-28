"""
District API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.config.database import get_db
from backend.schemas.district import DistrictCreate, DistrictResponse
from backend.services.district_service import DistrictService

router = APIRouter()


@router.post("/", response_model=DistrictResponse, status_code=201)
def create_district(district: DistrictCreate, db: Session = Depends(get_db)):
    """Create a new district"""
    return DistrictService.create_district(db, district)


@router.get("/", response_model=List[DistrictResponse])
def get_districts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all districts"""
    return DistrictService.get_all_districts(db, skip, limit)


@router.get("/province/{province_id}", response_model=List[DistrictResponse])
def get_districts_by_province(province_id: int, db: Session = Depends(get_db)):
    """Get all districts in a province"""
    return DistrictService.get_districts_by_province(db, province_id)


@router.get("/{district_id}", response_model=DistrictResponse)
def get_district(district_id: int, db: Session = Depends(get_db)):
    """Get a specific district"""
    district = DistrictService.get_district(db, district_id)
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district


@router.delete("/{district_id}", status_code=204)
def delete_district(district_id: int, db: Session = Depends(get_db)):
    """Delete a district"""
    success = DistrictService.delete_district(db, district_id)
    if not success:
        raise HTTPException(status_code=404, detail="District not found")
    return None
