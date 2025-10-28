"""
Province API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.config.database import get_db
from backend.schemas.province import ProvinceCreate, ProvinceResponse
from backend.services.province_service import ProvinceService

router = APIRouter()


@router.post("/", response_model=ProvinceResponse, status_code=201)
def create_province(province: ProvinceCreate, db: Session = Depends(get_db)):
    """Create a new province"""
    # Check if province already exists
    existing = ProvinceService.get_province_by_name(db, province.name)
    if existing:
        raise HTTPException(status_code=400, detail="Province already exists")
    return ProvinceService.create_province(db, province)


@router.get("/", response_model=List[ProvinceResponse])
def get_provinces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all provinces"""
    return ProvinceService.get_all_provinces(db, skip, limit)


@router.get("/{province_id}", response_model=ProvinceResponse)
def get_province(province_id: int, db: Session = Depends(get_db)):
    """Get a specific province"""
    province = ProvinceService.get_province(db, province_id)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return province


@router.delete("/{province_id}", status_code=204)
def delete_province(province_id: int, db: Session = Depends(get_db)):
    """Delete a province"""
    success = ProvinceService.delete_province(db, province_id)
    if not success:
        raise HTTPException(status_code=404, detail="Province not found")
    return None
