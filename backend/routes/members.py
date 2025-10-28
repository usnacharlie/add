"""
Member API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.config.database import get_db
from backend.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from backend.services.member_service import MemberService

router = APIRouter()


@router.post("/", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Create a new member"""
    return MemberService.create_member(db, member)


@router.get("/", response_model=List[MemberResponse])
def get_members(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all members or search by name"""
    if name:
        return MemberService.search_members(db, name)
    return MemberService.get_all_members(db, skip, limit)


@router.get("/ward/{ward_id}", response_model=List[MemberResponse])
def get_members_by_ward(ward_id: int, db: Session = Depends(get_db)):
    """Get all members in a ward"""
    return MemberService.get_members_by_ward(db, ward_id)


@router.get("/nrc/{nrc}", response_model=MemberResponse)
def get_member_by_nrc(nrc: str, db: Session = Depends(get_db)):
    """Get member by NRC"""
    member = MemberService.get_member_by_nrc(db, nrc)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("/voters-id/{voters_id}", response_model=MemberResponse)
def get_member_by_voters_id(voters_id: str, db: Session = Depends(get_db)):
    """Get member by Voter's ID"""
    member = MemberService.get_member_by_voters_id(db, voters_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a specific member"""
    member = MemberService.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member_update: MemberUpdate, db: Session = Depends(get_db)):
    """Update a member"""
    member = MemberService.update_member(db, member_id, member_update)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a member"""
    success = MemberService.delete_member(db, member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return None
