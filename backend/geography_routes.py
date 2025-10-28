"""
Geography API Routes for Zambian Administrative Divisions
Provides endpoints for provinces, districts, constituencies, and wards
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from uuid import UUID

from database import SessionLocal

# Pydantic models for responses
class ProvinceResponse(BaseModel):
    id: UUID
    province_code: str
    province_name: str
    capital_city: str | None
    number_of_districts: int | None
    number_of_constituencies: int | None

    class Config:
        from_attributes = True

class DistrictResponse(BaseModel):
    id: UUID
    province_id: UUID
    district_code: str
    district_name: str
    administrative_center: str | None

    class Config:
        from_attributes = True

class ConstituencyResponse(BaseModel):
    id: UUID
    province_id: UUID
    district_id: UUID | None
    constituency_code: str
    constituency_name: str
    constituency_type: str | None

    class Config:
        from_attributes = True

class WardResponse(BaseModel):
    id: UUID
    province_id: UUID
    district_id: UUID
    constituency_id: UUID | None
    ward_code: str
    ward_name: str
    population: int | None
    ward_type: str | None

    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create router
router = APIRouter(prefix="/api/geography", tags=["geography"])

# Import models directly from database
from sqlalchemy import text

@router.get("/provinces", response_model=List[ProvinceResponse])
def get_provinces(db: Session = Depends(get_db)):
    """Get all provinces"""
    result = db.execute(text("""
        SELECT id, province_code, province_name, capital_city,
               number_of_districts, number_of_constituencies
        FROM provinces
        ORDER BY province_name
    """))

    provinces = []
    for row in result:
        provinces.append({
            "id": row[0],
            "province_code": row[1],
            "province_name": row[2],
            "capital_city": row[3],
            "number_of_districts": row[4],
            "number_of_constituencies": row[5]
        })
    return provinces

@router.get("/provinces/{province_id}", response_model=ProvinceResponse)
def get_province(province_id: str, db: Session = Depends(get_db)):
    """Get a specific province"""
    result = db.execute(text("""
        SELECT id, province_code, province_name, capital_city,
               number_of_districts, number_of_constituencies
        FROM provinces
        WHERE id = :province_id
    """), {"province_id": province_id})

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Province not found")

    return {
        "id": row[0],
        "province_code": row[1],
        "province_name": row[2],
        "capital_city": row[3],
        "number_of_districts": row[4],
        "number_of_constituencies": row[5]
    }

@router.get("/districts", response_model=List[DistrictResponse])
def get_districts(province_id: str | None = None, db: Session = Depends(get_db)):
    """Get all districts, optionally filtered by province"""
    if province_id:
        result = db.execute(text("""
            SELECT id, province_id, district_code, district_name, administrative_center
            FROM districts
            WHERE province_id = :province_id
            ORDER BY district_name
        """), {"province_id": province_id})
    else:
        result = db.execute(text("""
            SELECT id, province_id, district_code, district_name, administrative_center
            FROM districts
            ORDER BY district_name
        """))

    districts = []
    for row in result:
        districts.append({
            "id": row[0],
            "province_id": row[1],
            "district_code": row[2],
            "district_name": row[3],
            "administrative_center": row[4]
        })
    return districts

@router.get("/provinces/{province_id}/districts", response_model=List[DistrictResponse])
def get_province_districts(province_id: str, db: Session = Depends(get_db)):
    """Get all districts in a specific province"""
    result = db.execute(text("""
        SELECT id, province_id, district_code, district_name, administrative_center
        FROM districts
        WHERE province_id = :province_id
        ORDER BY district_name
    """), {"province_id": province_id})

    districts = []
    for row in result:
        districts.append({
            "id": row[0],
            "province_id": row[1],
            "district_code": row[2],
            "district_name": row[3],
            "administrative_center": row[4]
        })
    return districts

@router.get("/districts/{district_id}", response_model=DistrictResponse)
def get_district(district_id: str, db: Session = Depends(get_db)):
    """Get a specific district"""
    result = db.execute(text("""
        SELECT id, province_id, district_code, district_name, administrative_center
        FROM districts
        WHERE id = :district_id
    """), {"district_id": district_id})

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="District not found")

    return {
        "id": row[0],
        "province_id": row[1],
        "district_code": row[2],
        "district_name": row[3],
        "administrative_center": row[4]
    }

@router.get("/constituencies", response_model=List[ConstituencyResponse])
def get_constituencies(
    province_id: str | None = None,
    district_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Get all constituencies, optionally filtered by province or district"""
    if district_id:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_code,
                   constituency_name, constituency_type
            FROM constituencies
            WHERE district_id = :district_id
            ORDER BY constituency_name
        """), {"district_id": district_id})
    elif province_id:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_code,
                   constituency_name, constituency_type
            FROM constituencies
            WHERE province_id = :province_id
            ORDER BY constituency_name
        """), {"province_id": province_id})
    else:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_code,
                   constituency_name, constituency_type
            FROM constituencies
            ORDER BY constituency_name
        """))

    constituencies = []
    for row in result:
        constituencies.append({
            "id": row[0],
            "province_id": row[1],
            "district_id": row[2],
            "constituency_code": row[3],
            "constituency_name": row[4],
            "constituency_type": row[5]
        })
    return constituencies

@router.get("/districts/{district_id}/constituencies", response_model=List[ConstituencyResponse])
def get_district_constituencies(district_id: str, db: Session = Depends(get_db)):
    """Get all constituencies in a specific district"""
    result = db.execute(text("""
        SELECT id, province_id, district_id, constituency_code,
               constituency_name, constituency_type
        FROM constituencies
        WHERE district_id = :district_id
        ORDER BY constituency_name
    """), {"district_id": district_id})

    constituencies = []
    for row in result:
        constituencies.append({
            "id": row[0],
            "province_id": row[1],
            "district_id": row[2],
            "constituency_code": row[3],
            "constituency_name": row[4],
            "constituency_type": row[5]
        })
    return constituencies

@router.get("/constituencies/{constituency_id}", response_model=ConstituencyResponse)
def get_constituency(constituency_id: str, db: Session = Depends(get_db)):
    """Get a specific constituency"""
    result = db.execute(text("""
        SELECT id, province_id, district_id, constituency_code,
               constituency_name, constituency_type
        FROM constituencies
        WHERE id = :constituency_id
    """), {"constituency_id": constituency_id})

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Constituency not found")

    return {
        "id": row[0],
        "province_id": row[1],
        "district_id": row[2],
        "constituency_code": row[3],
        "constituency_name": row[4],
        "constituency_type": row[5]
    }

@router.get("/wards", response_model=List[WardResponse])
def get_wards(
    province_id: str | None = None,
    district_id: str | None = None,
    constituency_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Get all wards, optionally filtered by province, district, or constituency"""
    if constituency_id:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_id,
                   ward_code, ward_name, population, ward_type
            FROM wards
            WHERE constituency_id = :constituency_id
            ORDER BY ward_name
        """), {"constituency_id": constituency_id})
    elif district_id:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_id,
                   ward_code, ward_name, population, ward_type
            FROM wards
            WHERE district_id = :district_id
            ORDER BY ward_name
        """), {"district_id": district_id})
    elif province_id:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_id,
                   ward_code, ward_name, population, ward_type
            FROM wards
            WHERE province_id = :province_id
            ORDER BY ward_name
        """), {"province_id": province_id})
    else:
        result = db.execute(text("""
            SELECT id, province_id, district_id, constituency_id,
                   ward_code, ward_name, population, ward_type
            FROM wards
            ORDER BY ward_name
            LIMIT 1000
        """))

    wards = []
    for row in result:
        wards.append({
            "id": row[0],
            "province_id": row[1],
            "district_id": row[2],
            "constituency_id": row[3],
            "ward_code": row[4],
            "ward_name": row[5],
            "population": row[6],
            "ward_type": row[7]
        })
    return wards

@router.get("/constituencies/{constituency_id}/wards", response_model=List[WardResponse])
def get_constituency_wards(constituency_id: str, db: Session = Depends(get_db)):
    """Get all wards in a specific constituency"""
    result = db.execute(text("""
        SELECT id, province_id, district_id, constituency_id,
               ward_code, ward_name, population, ward_type
        FROM wards
        WHERE constituency_id = :constituency_id
        ORDER BY ward_name
    """), {"constituency_id": constituency_id})

    wards = []
    for row in result:
        wards.append({
            "id": row[0],
            "province_id": row[1],
            "district_id": row[2],
            "constituency_id": row[3],
            "ward_code": row[4],
            "ward_name": row[5],
            "population": row[6],
            "ward_type": row[7]
        })
    return wards

@router.get("/districts/{district_id}/wards", response_model=List[WardResponse])
def get_district_wards(district_id: str, db: Session = Depends(get_db)):
    """Get all wards in a specific district"""
    result = db.execute(text("""
        SELECT id, province_id, district_id, constituency_id,
               ward_code, ward_name, population, ward_type
        FROM wards
        WHERE district_id = :district_id
        ORDER BY ward_name
    """), {"district_id": district_id})

    wards = []
    for row in result:
        wards.append({
            "id": row[0],
            "province_id": row[1],
            "district_id": row[2],
            "constituency_id": row[3],
            "ward_code": row[4],
            "ward_name": row[5],
            "population": row[6],
            "ward_type": row[7]
        })
    return wards

@router.get("/wards/{ward_id}", response_model=WardResponse)
def get_ward(ward_id: str, db: Session = Depends(get_db)):
    """Get a specific ward"""
    result = db.execute(text("""
        SELECT id, province_id, district_id, constituency_id,
               ward_code, ward_name, population, ward_type
        FROM wards
        WHERE id = :ward_id
    """), {"ward_id": ward_id})

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Ward not found")

    return {
        "id": row[0],
        "province_id": row[1],
        "district_id": row[2],
        "constituency_id": row[3],
        "ward_code": row[4],
        "ward_name": row[5],
        "population": row[6],
        "ward_type": row[7]
    }
