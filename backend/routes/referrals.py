"""
Referrals API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime
import secrets
import string

from backend.config.database import get_db
from backend.models import Referral, Member
from backend.schemas.referral import (
    ReferralCreate, ReferralUpdate, ReferralResponse,
    ReferralWithDetails, ReferralListResponse, ReferralStatistics,
    ReferralContactRequest, TopReferrersResponse, MemberReferralStats
)

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def generate_referral_code(length=8):
    """Generate a unique referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post("", response_model=ReferralResponse, status_code=status.HTTP_201_CREATED)
def create_referral(referral: ReferralCreate, db: Session = Depends(get_db)):
    """
    Create a new referral
    """
    # Verify referrer exists
    referrer = db.query(Member).filter(Member.id == referral.referrer_id).first()
    if not referrer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referrer with id {referral.referrer_id} not found"
        )

    # Generate unique referral code
    while True:
        referral_code = generate_referral_code()
        existing = db.query(Referral).filter(Referral.referral_code == referral_code).first()
        if not existing:
            break

    # Create referral
    db_referral = Referral(
        **referral.dict(),
        referral_code=referral_code
    )

    db.add(db_referral)
    db.commit()
    db.refresh(db_referral)

    return db_referral


@router.get("", response_model=ReferralListResponse)
def list_referrals(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    referrer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all referrals with optional filters
    """
    query = db.query(Referral, Member).join(
        Member, Referral.referrer_id == Member.id
    )

    # Apply filters
    if status_filter:
        query = query.filter(Referral.status == status_filter)
    if referrer_id:
        query = query.filter(Referral.referrer_id == referrer_id)
    if search:
        query = query.filter(
            or_(
                Referral.referred_name.ilike(f"%{search}%"),
                Referral.referred_contact.ilike(f"%{search}%"),
                Referral.referred_email.ilike(f"%{search}%"),
                Member.name.ilike(f"%{search}%")
            )
        )

    # Get total count
    total = query.count()

    # Get referrals with referrer details
    referrals = query.order_by(Referral.referred_date.desc()).offset(skip).limit(limit).all()

    # Build response
    referral_list = []
    for referral, referrer in referrals:
        # Get referred member name if registered
        referred_member_name = None
        if referral.referred_member_id:
            referred_member = db.query(Member).filter(Member.id == referral.referred_member_id).first()
            if referred_member:
                referred_member_name = referred_member.name

        referral_data = ReferralWithDetails(
            id=referral.id,
            referrer_id=referral.referrer_id,
            referred_member_id=referral.referred_member_id,
            referral_code=referral.referral_code,
            referred_name=referral.referred_name,
            referred_contact=referral.referred_contact,
            referred_email=referral.referred_email,
            status=referral.status,
            notes=referral.notes,
            referred_date=referral.referred_date,
            contacted_date=referral.contacted_date,
            registered_date=referral.registered_date,
            created_at=referral.created_at,
            updated_at=referral.updated_at,
            referrer_name=referrer.name,
            referrer_contact=referrer.contact,
            referred_member_name=referred_member_name
        )
        referral_list.append(referral_data)

    return {"total": total, "referrals": referral_list}


@router.get("/statistics", response_model=ReferralStatistics)
def get_referral_statistics(db: Session = Depends(get_db)):
    """
    Get referral statistics
    """
    total_referrals = db.query(Referral).count()
    pending_referrals = db.query(Referral).filter(Referral.status == 'pending').count()
    contacted_referrals = db.query(Referral).filter(Referral.status == 'contacted').count()
    successful_referrals = db.query(Referral).filter(Referral.status == 'registered').count()
    declined_referrals = db.query(Referral).filter(Referral.status == 'declined').count()
    expired_referrals = db.query(Referral).filter(Referral.status == 'expired').count()

    conversion_rate = 0.0
    if total_referrals > 0:
        conversion_rate = round((successful_referrals / total_referrals) * 100, 2)

    return {
        "total_referrals": total_referrals,
        "pending_referrals": pending_referrals,
        "contacted_referrals": contacted_referrals,
        "successful_referrals": successful_referrals,
        "declined_referrals": declined_referrals,
        "expired_referrals": expired_referrals,
        "conversion_rate": conversion_rate
    }


@router.get("/top-referrers", response_model=TopReferrersResponse)
def get_top_referrers(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get top referrers by total referrals
    """
    from sqlalchemy import case

    # Query to get referral counts per member
    referral_counts = db.query(
        Referral.referrer_id,
        func.count(Referral.id).label('total_referrals'),
        func.sum(case((Referral.status == 'registered', 1), else_=0)).label('successful_referrals'),
        func.sum(case((Referral.status == 'pending', 1), else_=0)).label('pending_referrals')
    ).group_by(Referral.referrer_id).order_by(func.count(Referral.id).desc()).limit(limit).all()

    # Build response with member details
    top_referrers = []
    for referrer_id, total, successful, pending in referral_counts:
        member = db.query(Member).filter(Member.id == referrer_id).first()
        if member:
            conversion_rate = 0.0
            if total > 0:
                conversion_rate = round((successful / total) * 100, 2)

            top_referrers.append(MemberReferralStats(
                member_id=member.id,
                member_name=member.name,
                total_referrals=total,
                successful_referrals=successful,
                pending_referrals=pending,
                conversion_rate=conversion_rate
            ))

    return {"top_referrers": top_referrers}


@router.get("/{referral_id}", response_model=ReferralWithDetails)
def get_referral(referral_id: int, db: Session = Depends(get_db)):
    """
    Get referral details
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with id {referral_id} not found"
        )

    # Get referrer details
    referrer = db.query(Member).filter(Member.id == referral.referrer_id).first()

    # Get referred member name if registered
    referred_member_name = None
    if referral.referred_member_id:
        referred_member = db.query(Member).filter(Member.id == referral.referred_member_id).first()
        if referred_member:
            referred_member_name = referred_member.name

    return ReferralWithDetails(
        id=referral.id,
        referrer_id=referral.referrer_id,
        referred_member_id=referral.referred_member_id,
        referral_code=referral.referral_code,
        referred_name=referral.referred_name,
        referred_contact=referral.referred_contact,
        referred_email=referral.referred_email,
        status=referral.status,
        notes=referral.notes,
        referred_date=referral.referred_date,
        contacted_date=referral.contacted_date,
        registered_date=referral.registered_date,
        created_at=referral.created_at,
        updated_at=referral.updated_at,
        referrer_name=referrer.name if referrer else None,
        referrer_contact=referrer.contact if referrer else None,
        referred_member_name=referred_member_name
    )


@router.put("/{referral_id}", response_model=ReferralResponse)
def update_referral(referral_id: int, referral_update: ReferralUpdate, db: Session = Depends(get_db)):
    """
    Update referral details
    """
    db_referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not db_referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with id {referral_id} not found"
        )

    # Update fields
    update_data = referral_update.dict(exclude_unset=True)

    # Update timestamps based on status changes
    if 'status' in update_data:
        if update_data['status'] == 'contacted' and not db_referral.contacted_date:
            db_referral.contacted_date = datetime.utcnow()
        elif update_data['status'] == 'registered' and not db_referral.registered_date:
            db_referral.registered_date = datetime.utcnow()

    for field, value in update_data.items():
        setattr(db_referral, field, value)

    db.commit()
    db.refresh(db_referral)

    return db_referral


@router.delete("/{referral_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_referral(referral_id: int, db: Session = Depends(get_db)):
    """
    Delete a referral
    """
    db_referral = db.query(Referral).filter(Referral.id == referral_id).first()

    if not db_referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with id {referral_id} not found"
        )

    db.delete(db_referral)
    db.commit()

    return None


@router.post("/mark-contacted", response_model=dict)
def mark_contacted(
    contact_data: ReferralContactRequest,
    db: Session = Depends(get_db)
):
    """
    Mark referrals as contacted
    """
    marked_count = 0
    for referral_id in contact_data.referral_ids:
        referral = db.query(Referral).filter(Referral.id == referral_id).first()

        if referral:
            if contact_data.mark_as_contacted:
                referral.status = 'contacted'
                if not referral.contacted_date:
                    referral.contacted_date = datetime.utcnow()
            else:
                referral.status = 'pending'
                referral.contacted_date = None
            marked_count += 1

    db.commit()

    return {
        "message": f"Marked {marked_count} referrals as {'contacted' if contact_data.mark_as_contacted else 'pending'}",
        "marked_count": marked_count
    }
