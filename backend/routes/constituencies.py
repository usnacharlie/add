"""
Constituency API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.config.database import get_db
from backend.schemas.constituency import ConstituencyCreate, ConstituencyResponse
from backend.services.constituency_service import ConstituencyService

router = APIRouter()


@router.post("/", response_model=ConstituencyResponse, status_code=201)
def create_constituency(constituency: ConstituencyCreate, db: Session = Depends(get_db)):
    """Create a new constituency"""
    return ConstituencyService.create_constituency(db, constituency)


@router.get("/", response_model=List[ConstituencyResponse])
def get_constituencies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all constituencies"""
    return ConstituencyService.get_all_constituencies(db, skip, limit)


@router.get("/district/{district_id}", response_model=List[ConstituencyResponse])
def get_constituencies_by_district(district_id: int, db: Session = Depends(get_db)):
    """Get all constituencies in a district"""
    return ConstituencyService.get_constituencies_by_district(db, district_id)


@router.get("/{constituency_id}", response_model=ConstituencyResponse)
def get_constituency(constituency_id: int, db: Session = Depends(get_db)):
    """Get a specific constituency"""
    constituency = ConstituencyService.get_constituency(db, constituency_id)
    if not constituency:
        raise HTTPException(status_code=404, detail="Constituency not found")
    return constituency


@router.delete("/{constituency_id}", status_code=204)
def delete_constituency(constituency_id: int, db: Session = Depends(get_db)):
    """Delete a constituency"""
    success = ConstituencyService.delete_constituency(db, constituency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Constituency not found")
    return None
