from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

# ============== DONATION SCHEMAS ==============
class DonationCreate(BaseModel):
    donor_member_id: Optional[UUID] = None
    donor_name: Optional[str] = None
    donor_type: str
    amount: float
    currency: str = "ZMW"
    donation_method: str
    purpose: Optional[str] = None
    campaign_id: Optional[UUID] = None
    anonymous: bool = False
    notes: Optional[str] = None

class DonationResponse(DonationCreate):
    id: UUID
    donation_date: datetime
    receipt_issued: bool
    receipt_number: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

# ============== CAMPAIGN SCHEMAS ==============
class CampaignCreate(BaseModel):
    campaign_name: str
    campaign_type: str
    start_date: date
    end_date: Optional[date] = None
    budget: Optional[float] = None
    campaign_manager_id: Optional[UUID] = None
    description: Optional[str] = None

class CampaignResponse(CampaignCreate):
    id: UUID
    status: str
    actual_spending: Optional[float]
    created_at: datetime

    class Config:
        orm_mode = True

# ============== VOLUNTEER SCHEMAS ==============
class VolunteerCreate(BaseModel):
    member_id: UUID
    availability: str
    skills: List[str] = []
    preferred_tasks: List[str] = []
    volunteer_coordinator_id: Optional[UUID] = None
    notes: Optional[str] = None

class VolunteerResponse(VolunteerCreate):
    id: UUID
    hours_contributed: int
    last_activity_date: Optional[date]
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# ============== COMMUNICATION SCHEMAS ==============
class CommunicationCreate(BaseModel):
    communication_type: str
    subject: Optional[str] = None
    message: str
    recipient_type: str
    recipient_ids: List[UUID]
    recipient_filter: Optional[Dict[str, Any]] = None
    scheduled_time: Optional[datetime] = None

class CommunicationResponse(BaseModel):
    id: UUID
    communication_type: str
    subject: Optional[str]
    message: str
    sender_id: UUID
    recipient_type: str
    status: str
    total_recipients: Optional[int]
    successful_deliveries: Optional[int]
    failed_deliveries: Optional[int]
    sent_time: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True

# ============== COMMITTEE SCHEMAS ==============
class CommitteeCreate(BaseModel):
    committee_name: str
    committee_type: str
    description: Optional[str] = None
    formation_date: Optional[date] = None
    meeting_frequency: Optional[str] = None
    next_meeting_date: Optional[date] = None

class CommitteeResponse(CommitteeCreate):
    id: UUID
    is_active: bool
    dissolution_date: Optional[date]
    created_at: datetime

    class Config:
        orm_mode = True

class CommitteeMemberCreate(BaseModel):
    member_id: UUID
    role: str
    appointment_date: date
    voting_rights: bool = True

class CommitteeMemberResponse(CommitteeMemberCreate):
    id: UUID
    committee_id: UUID
    end_date: Optional[date]
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# ============== TRAINING SCHEMAS ==============
class TrainingProgramCreate(BaseModel):
    program_name: str
    program_type: str
    description: Optional[str] = None
    trainer: Optional[str] = None
    training_date: date
    duration_hours: Optional[int] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None
    materials_url: Optional[str] = None
    certificate_issued: bool = False
    cost_per_participant: Optional[float] = None

class TrainingProgramResponse(TrainingProgramCreate):
    id: UUID
    current_participants: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# ============== POLL SCHEMAS ==============
class PollQuestionCreate(BaseModel):
    question_text: str
    question_type: str  # single_choice, multiple_choice, text, rating
    options: Optional[List[str]] = None
    is_required: bool = True

class PollCreate(BaseModel):
    poll_title: str
    poll_type: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    target_audience: str
    audience_filter: Optional[Dict[str, Any]] = None
    is_anonymous: bool = False
    allow_multiple_votes: bool = False
    questions: List[PollQuestionCreate]

class PollResponse(BaseModel):
    id: UUID
    poll_title: str
    poll_type: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    target_audience: str
    is_anonymous: bool
    status: str
    created_by: UUID
    created_at: datetime

    class Config:
        orm_mode = True

class PollResponseCreate(BaseModel):
    question_id: UUID
    response_text: Optional[str] = None
    response_options: Optional[List[str]] = None
    response_rating: Optional[int] = None

# ============== DOCUMENT SCHEMAS ==============
class DocumentCreate(BaseModel):
    document_title: str
    document_type: str
    category: Optional[str] = None
    file_url: str
    file_size_kb: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_public: bool = False
    access_level: str = "member"

class DocumentResponse(DocumentCreate):
    id: UUID
    uploaded_by: UUID
    approval_status: str
    approved_by: Optional[UUID]
    approval_date: Optional[datetime]
    download_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ============== GRIEVANCE SCHEMAS ==============
class GrievanceCreate(BaseModel):
    grievance_type: str
    subject: str
    description: str
    priority: str = "medium"
    is_anonymous: bool = False

class GrievanceResponse(BaseModel):
    id: UUID
    complainant_id: Optional[UUID]
    grievance_type: str
    subject: str
    description: str
    priority: str
    status: str
    assigned_to: Optional[UUID]
    resolution: Optional[str]
    resolution_date: Optional[datetime]
    satisfaction_rating: Optional[int]
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ============== ELECTION SCHEMAS ==============
class ElectionCreate(BaseModel):
    election_title: str
    election_type: str
    position_contested: Optional[str] = None
    election_date: date
    nomination_start_date: Optional[date] = None
    nomination_end_date: Optional[date] = None
    campaign_start_date: Optional[date] = None
    campaign_end_date: Optional[date] = None
    eligible_voters_count: Optional[int] = None
    election_method: str = "secret_ballot"

class ElectionResponse(ElectionCreate):
    id: UUID
    actual_voters_count: Optional[int]
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class CandidateNomination(BaseModel):
    candidate_id: UUID
    running_mate_id: Optional[UUID] = None
    manifesto_url: Optional[str] = None
    campaign_slogan: Optional[str] = None

class VoteCast(BaseModel):
    candidate_id: UUID

# ============== ATTENDANCE SCHEMAS ==============
class AttendanceCheckIn(BaseModel):
    event_type: str
    event_id: Optional[UUID] = None
    attendance_method: str = "physical"
    location: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: UUID
    member_id: UUID
    event_type: str
    event_id: Optional[UUID]
    check_in_time: datetime
    check_out_time: Optional[datetime]
    attendance_method: str
    location: Optional[str]
    verified_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

# ============== DISCIPLINARY SCHEMAS ==============
class DisciplinaryActionCreate(BaseModel):
    member_id: UUID
    action_type: str
    reason: str
    action_date: date
    effective_from: date
    effective_until: Optional[date] = None
    committee_id: Optional[UUID] = None

class DisciplinaryActionResponse(DisciplinaryActionCreate):
    id: UUID
    issued_by: UUID
    appeal_status: Optional[str]
    appeal_date: Optional[date]
    appeal_decision: Optional[str]
    reversed: bool
    created_at: datetime

    class Config:
        orm_mode = True

# ============== PARTNER SCHEMAS ==============
class PartnerCreate(BaseModel):
    partner_name: str
    partner_type: str
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    agreement_date: Optional[date] = None
    agreement_expiry: Optional[date] = None
    partnership_details: Optional[str] = None

class PartnerResponse(PartnerCreate):
    id: UUID
    partnership_status: str
    created_at: datetime

    class Config:
        orm_mode = True