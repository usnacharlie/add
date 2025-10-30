"""
Member service layer
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from backend.models.member import Member
from backend.schemas.member import MemberCreate, MemberUpdate
from fastapi import HTTPException


class MemberService:
    @staticmethod
    def create_member(db: Session, member: MemberCreate) -> Member:
        """Create a new member"""
        # Check if voters_id already exists
        existing_member = db.query(Member).filter(Member.voters_id == member.voters_id).first()
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail=f"Voter ID '{member.voters_id}' is already registered to {existing_member.name}"
            )

        # Check if NRC already exists (if provided)
        if member.nrc:
            existing_nrc = db.query(Member).filter(Member.nrc == member.nrc).first()
            if existing_nrc:
                raise HTTPException(
                    status_code=400,
                    detail=f"NRC '{member.nrc}' is already registered to {existing_nrc.name}"
                )

        try:
            db_member = Member(**member.model_dump())
            db.add(db_member)
            db.commit()
            db.refresh(db_member)
            return db_member
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error: Duplicate voter ID or NRC")

    @staticmethod
    def get_member(db: Session, member_id: int) -> Optional[Member]:
        """Get member by ID"""
        return db.query(Member).filter(Member.id == member_id).first()

    @staticmethod
    def get_members_by_ward(db: Session, ward_id: int) -> List[Member]:
        """Get all members in a ward"""
        return db.query(Member).filter(Member.ward_id == ward_id).all()

    @staticmethod
    def get_member_by_nrc(db: Session, nrc: str) -> Optional[Member]:
        """Get member by NRC"""
        return db.query(Member).filter(Member.nrc == nrc).first()

    @staticmethod
    def get_member_by_voters_id(db: Session, voters_id: str) -> Optional[Member]:
        """Get member by Voter's ID"""
        return db.query(Member).filter(Member.voters_id == voters_id).first()

    @staticmethod
    def search_members(db: Session, name: str) -> List[Member]:
        """Search members by name"""
        return db.query(Member).filter(Member.name.ilike(f"%{name}%")).all()

    @staticmethod
    def get_all_members(db: Session, skip: int = 0, limit: int = 100) -> List[Member]:
        """Get all members with pagination"""
        return db.query(Member).offset(skip).limit(limit).all()

    @staticmethod
    def update_member(db: Session, member_id: int, member_update: MemberUpdate) -> Optional[Member]:
        """Update a member"""
        db_member = db.query(Member).filter(Member.id == member_id).first()
        if db_member:
            update_data = member_update.model_dump(exclude_unset=True)

            # Check for duplicate voters_id if updating
            if 'voters_id' in update_data and update_data['voters_id']:
                existing_voter = db.query(Member).filter(
                    Member.voters_id == update_data['voters_id'],
                    Member.id != member_id
                ).first()
                if existing_voter:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Voter ID '{update_data['voters_id']}' is already registered to {existing_voter.name}"
                    )

            # Check for duplicate NRC if updating
            if 'nrc' in update_data and update_data['nrc']:
                existing_nrc = db.query(Member).filter(
                    Member.nrc == update_data['nrc'],
                    Member.id != member_id
                ).first()
                if existing_nrc:
                    raise HTTPException(
                        status_code=400,
                        detail=f"NRC '{update_data['nrc']}' is already registered to {existing_nrc.name}"
                    )

            try:
                for key, value in update_data.items():
                    setattr(db_member, key, value)
                db.commit()
                db.refresh(db_member)
            except IntegrityError:
                db.rollback()
                raise HTTPException(status_code=400, detail="Database integrity error: Duplicate voter ID or NRC")

        return db_member

    @staticmethod
    def delete_member(db: Session, member_id: int) -> bool:
        """Delete a member"""
        member = db.query(Member).filter(Member.id == member_id).first()
        if member:
            db.delete(member)
            db.commit()
            return True
        return False
