"""
District service layer
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.district import District
from backend.schemas.district import DistrictCreate


class DistrictService:
    @staticmethod
    def create_district(db: Session, district: DistrictCreate) -> District:
        """Create a new district"""
        db_district = District(name=district.name, province_id=district.province_id)
        db.add(db_district)
        db.commit()
        db.refresh(db_district)
        return db_district

    @staticmethod
    def get_district(db: Session, district_id: int) -> Optional[District]:
        """Get district by ID"""
        return db.query(District).filter(District.id == district_id).first()

    @staticmethod
    def get_districts_by_province(db: Session, province_id: int) -> List[District]:
        """Get all districts in a province"""
        return db.query(District).filter(District.province_id == province_id).all()

    @staticmethod
    def get_all_districts(db: Session, skip: int = 0, limit: int = 100) -> List[District]:
        """Get all districts with pagination"""
        return db.query(District).offset(skip).limit(limit).all()

    @staticmethod
    def delete_district(db: Session, district_id: int) -> bool:
        """Delete a district"""
        district = db.query(District).filter(District.id == district_id).first()
        if district:
            db.delete(district)
            db.commit()
            return True
        return False
