"""
Referral Management Schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============== Referral Schemas ==============

class ReferralBase(BaseModel):
    referred_name: str = Field(..., min_length=1, max_length=200)
    referred_contact: str = Field(..., min_length=1, max_length=50)
    referred_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class ReferralCreate(ReferralBase):
    referrer_id: int


class ReferralUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|contacted|registered|expired|declined)$")
    referred_name: Optional[str] = Field(None, min_length=1, max_length=200)
    referred_contact: Optional[str] = Field(None, min_length=1, max_length=50)
    referred_email: Optional[EmailStr] = None
    referred_member_id: Optional[int] = None
    notes: Optional[str] = None


class ReferralResponse(ReferralBase):
    id: int
    referrer_id: int
    referred_member_id: Optional[int] = None
    referral_code: str
    status: str
    referred_date: datetime
    contacted_date: Optional[datetime] = None
    registered_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReferralWithDetails(ReferralResponse):
    referrer_name: str
    referrer_contact: Optional[str] = None
    referred_member_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReferralListResponse(BaseModel):
    total: int
    referrals: List[ReferralWithDetails]


# ============== Referral Statistics Schema ==============

class ReferralStatistics(BaseModel):
    total_referrals: int
    pending_referrals: int
    contacted_referrals: int
    successful_referrals: int
    declined_referrals: int
    expired_referrals: int
    conversion_rate: float


class MemberReferralStats(BaseModel):
    member_id: int
    member_name: str
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    conversion_rate: float


class TopReferrersResponse(BaseModel):
    top_referrers: List[MemberReferralStats]


# ============== Referral Contact Schema ==============

class ReferralContactRequest(BaseModel):
    referral_ids: List[int] = Field(..., min_items=1)
    mark_as_contacted: bool = True
