"""
Province service layer
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.province import Province
from backend.schemas.province import ProvinceCreate


class ProvinceService:
    @staticmethod
    def create_province(db: Session, province: ProvinceCreate) -> Province:
        """Create a new province"""
        db_province = Province(name=province.name)
        db.add(db_province)
        db.commit()
        db.refresh(db_province)
        return db_province

    @staticmethod
    def get_province(db: Session, province_id: int) -> Optional[Province]:
        """Get province by ID"""
        return db.query(Province).filter(Province.id == province_id).first()

    @staticmethod
    def get_province_by_name(db: Session, name: str) -> Optional[Province]:
        """Get province by name"""
        return db.query(Province).filter(Province.name == name).first()

    @staticmethod
    def get_all_provinces(db: Session, skip: int = 0, limit: int = 100) -> List[Province]:
        """Get all provinces with pagination"""
        return db.query(Province).offset(skip).limit(limit).all()

    @staticmethod
    def delete_province(db: Session, province_id: int) -> bool:
        """Delete a province"""
        province = db.query(Province).filter(Province.id == province_id).first()
        if province:
            db.delete(province)
            db.commit()
            return True
        return False
