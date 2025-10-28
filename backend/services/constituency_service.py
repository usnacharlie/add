"""
Constituency service layer
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.constituency import Constituency
from backend.schemas.constituency import ConstituencyCreate


class ConstituencyService:
    @staticmethod
    def create_constituency(db: Session, constituency: ConstituencyCreate) -> Constituency:
        """Create a new constituency"""
        db_constituency = Constituency(name=constituency.name, district_id=constituency.district_id)
        db.add(db_constituency)
        db.commit()
        db.refresh(db_constituency)
        return db_constituency

    @staticmethod
    def get_constituency(db: Session, constituency_id: int) -> Optional[Constituency]:
        """Get constituency by ID"""
        return db.query(Constituency).filter(Constituency.id == constituency_id).first()

    @staticmethod
    def get_constituencies_by_district(db: Session, district_id: int) -> List[Constituency]:
        """Get all constituencies in a district"""
        return db.query(Constituency).filter(Constituency.district_id == district_id).all()

    @staticmethod
    def get_all_constituencies(db: Session, skip: int = 0, limit: int = 100) -> List[Constituency]:
        """Get all constituencies with pagination"""
        return db.query(Constituency).offset(skip).limit(limit).all()

    @staticmethod
    def delete_constituency(db: Session, constituency_id: int) -> bool:
        """Delete a constituency"""
        constituency = db.query(Constituency).filter(Constituency.id == constituency_id).first()
        if constituency:
            db.delete(constituency)
            db.commit()
            return True
        return False
