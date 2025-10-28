from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

# Member schemas
class MemberBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: date
    gender: str
    national_id: str
    voter_id_number: str
    phone_number: str
    alternate_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    physical_address: str
    postal_address: Optional[str] = None
    constituency: str
    ward: str
    branch: str
    occupation: Optional[str] = None
    employer: Optional[str] = None
    education_level: Optional[str] = None
    marital_status: Optional[str] = None
    preferred_language: Optional[str] = "English"
    literacy_level: Optional[str] = "advanced"
    communication_preference: Optional[str] = "sms"
    membership_type: Optional[str] = "regular"

class MemberCreate(MemberBase):
    registration_channel: str
    password: Optional[str] = None

class MemberUpdate(BaseModel):
    phone_number: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    physical_address: Optional[str] = None
    postal_address: Optional[str] = None
    constituency: Optional[str] = None
    ward: Optional[str] = None
    branch: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    education_level: Optional[str] = None
    marital_status: Optional[str] = None
    membership_status: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    voter_registration_number: Optional[str] = None

class MemberResponse(MemberBase):
    id: UUID
    membership_number: str
    registration_date: datetime
    membership_status: str
    photo_url: Optional[str] = None
    id_document_url: Optional[str] = None
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MemberLogin(BaseModel):
    username: str  # Can be email or membership number
    password: str

# Payment schemas
class PaymentBase(BaseModel):
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    payment_year: int
    payment_status: Optional[str] = "pending"
    processed_by: Optional[str] = None
    notes: Optional[str] = None
    payment_phone: Optional[str] = None  # Phone number for mobile money payments

class PaymentCreate(PaymentBase):
    member_id: UUID

class PaymentResponse(PaymentBase):
    id: UUID
    member_id: UUID
    payment_date: datetime
    receipt_number: str
    created_at: datetime

    class Config:
        orm_mode = True

# Position schemas
class PositionBase(BaseModel):
    position_title: str
    position_level: str
    appointment_date: date
    end_date: Optional[date] = None
    is_active: bool = True
    appointed_by: Optional[str] = None
    notes: Optional[str] = None

class PositionCreate(PositionBase):
    member_id: UUID

class PositionResponse(PositionBase):
    id: UUID
    member_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Activity schemas
class ActivityBase(BaseModel):
    activity_name: str
    activity_type: str
    activity_date: date
    location: str
    description: Optional[str] = None
    organizer: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# USSD schemas
class USSDRequest(BaseModel):
    sessionId: str
    phoneNumber: str
    text: str
    serviceCode: Optional[str] = None

class USSDResponse(BaseModel):
    text: str
    sessionId: str
    phoneNumber: str
    endSession: bool = False

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    membership_number: Optional[str] = None