"""
Ward service layer
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.ward import Ward
from backend.schemas.ward import WardCreate


class WardService:
    @staticmethod
    def create_ward(db: Session, ward: WardCreate) -> Ward:
        """Create a new ward"""
        db_ward = Ward(name=ward.name, constituency_id=ward.constituency_id)
        db.add(db_ward)
        db.commit()
        db.refresh(db_ward)
        return db_ward

    @staticmethod
    def get_ward(db: Session, ward_id: int) -> Optional[Ward]:
        """Get ward by ID"""
        return db.query(Ward).filter(Ward.id == ward_id).first()

    @staticmethod
    def get_wards_by_constituency(db: Session, constituency_id: int) -> List[Ward]:
        """Get all wards in a constituency"""
        return db.query(Ward).filter(Ward.constituency_id == constituency_id).all()

    @staticmethod
    def get_all_wards(db: Session, skip: int = 0, limit: int = 100) -> List[Ward]:
        """Get all wards with pagination"""
        return db.query(Ward).offset(skip).limit(limit).all()

    @staticmethod
    def delete_ward(db: Session, ward_id: int) -> bool:
        """Delete a ward"""
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        if ward:
            db.delete(ward)
            db.commit()
            return True
        return False
