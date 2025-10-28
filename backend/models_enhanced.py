from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON, DECIMAL, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

# Donations and Fundraising
class Donation(Base):
    __tablename__ = "donations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"))
    donor_name = Column(String(200))
    donor_type = Column(String(50))
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(10), default="ZMW")
    donation_date = Column(DateTime, default=datetime.utcnow)
    donation_method = Column(String(50))
    purpose = Column(String(200))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    receipt_issued = Column(Boolean, default=False)
    receipt_number = Column(String(50))
    anonymous = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("Member", foreign_keys=[donor_member_id])
    campaign = relationship("Campaign", back_populates="donations")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_name = Column(String(200), nullable=False)
    campaign_type = Column(String(50))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    budget = Column(DECIMAL(12, 2))
    actual_spending = Column(DECIMAL(12, 2))
    campaign_manager_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    status = Column(String(30), default="planning")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("Member", foreign_keys=[campaign_manager_id])
    donations = relationship("Donation", back_populates="campaign")

class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    availability = Column(String(50))
    skills = Column(ARRAY(Text))
    preferred_tasks = Column(ARRAY(Text))
    hours_contributed = Column(Integer, default=0)
    last_activity_date = Column(Date)
    volunteer_coordinator_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    status = Column(String(30), default="active")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", foreign_keys=[member_id])
    coordinator = relationship("Member", foreign_keys=[volunteer_coordinator_id])

class Communication(Base):
    __tablename__ = "communications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    communication_type = Column(String(50))
    subject = Column(String(500))
    message = Column(Text, nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    recipient_type = Column(String(50))
    recipient_filter = Column(JSONB)
    scheduled_time = Column(DateTime)
    sent_time = Column(DateTime)
    status = Column(String(30), default="draft")
    total_recipients = Column(Integer)
    successful_deliveries = Column(Integer)
    failed_deliveries = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("Member")
    recipients = relationship("CommunicationRecipient", back_populates="communication")

class CommunicationRecipient(Base):
    __tablename__ = "communication_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    communication_id = Column(UUID(as_uuid=True), ForeignKey("communications.id", ondelete="CASCADE"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    delivery_status = Column(String(30))
    delivery_time = Column(DateTime)
    read_time = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    communication = relationship("Communication", back_populates="recipients")
    member = relationship("Member")

class Committee(Base):
    __tablename__ = "committees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_name = Column(String(200), nullable=False)
    committee_type = Column(String(50))
    description = Column(Text)
    formation_date = Column(Date)
    dissolution_date = Column(Date)
    is_active = Column(Boolean, default=True)
    meeting_frequency = Column(String(50))
    next_meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("CommitteeMember", back_populates="committee")

class CommitteeMember(Base):
    __tablename__ = "committee_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_id = Column(UUID(as_uuid=True), ForeignKey("committees.id", ondelete="CASCADE"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    role = Column(String(100))
    appointment_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    voting_rights = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    committee = relationship("Committee", back_populates="members")
    member = relationship("Member")

class TrainingProgram(Base):
    __tablename__ = "training_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_name = Column(String(200), nullable=False)
    program_type = Column(String(50))
    description = Column(Text)
    trainer = Column(String(200))
    training_date = Column(Date, nullable=False)
    duration_hours = Column(Integer)
    location = Column(String(200))
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    materials_url = Column(String(500))
    certificate_issued = Column(Boolean, default=False)
    cost_per_participant = Column(DECIMAL(10, 2))
    status = Column(String(30), default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)

    attendees = relationship("TrainingAttendance", back_populates="training")

class TrainingAttendance(Base):
    __tablename__ = "training_attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_id = Column(UUID(as_uuid=True), ForeignKey("training_programs.id", ondelete="CASCADE"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    registration_date = Column(DateTime, default=datetime.utcnow)
    attendance_status = Column(String(30), default="registered")
    completion_status = Column(String(30))
    certificate_number = Column(String(50))
    certificate_issued_date = Column(Date)
    feedback_score = Column(Integer, CheckConstraint("feedback_score >= 1 AND feedback_score <= 5"))
    feedback_comments = Column(Text)

    training = relationship("TrainingProgram", back_populates="attendees")
    member = relationship("Member")

class Poll(Base):
    __tablename__ = "polls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_title = Column(String(500), nullable=False)
    poll_type = Column(String(50))
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    target_audience = Column(String(50))
    audience_filter = Column(JSONB)
    is_anonymous = Column(Boolean, default=False)
    allow_multiple_votes = Column(Boolean, default=False)
    status = Column(String(30), default="draft")
    created_by = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Member")
    questions = relationship("PollQuestion", back_populates="poll")

class PollQuestion(Base):
    __tablename__ = "poll_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30))
    options = Column(JSONB)
    is_required = Column(Boolean, default=True)
    question_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    poll = relationship("Poll", back_populates="questions")
    responses = relationship("PollResponse", back_populates="question")

class PollResponse(Base):
    __tablename__ = "poll_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id", ondelete="CASCADE"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("poll_questions.id", ondelete="CASCADE"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    response_text = Column(Text)
    response_options = Column(JSONB)
    response_rating = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("PollQuestion", back_populates="responses")
    member = relationship("Member")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_title = Column(String(500), nullable=False)
    document_type = Column(String(50))
    category = Column(String(100))
    file_url = Column(String(500))
    file_size_kb = Column(Integer)
    file_type = Column(String(50))
    description = Column(Text)
    version = Column(String(20))
    is_public = Column(Boolean, default=False)
    access_level = Column(String(30))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    approval_status = Column(String(30), default="pending")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    approval_date = Column(DateTime)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploader = relationship("Member", foreign_keys=[uploaded_by])
    approver = relationship("Member", foreign_keys=[approved_by])
    access_logs = relationship("DocumentAccessLog", back_populates="document")

class DocumentAccessLog(Base):
    __tablename__ = "document_access_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    access_type = Column(String(30))
    ip_address = Column(String(45))
    access_time = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="access_logs")
    member = relationship("Member")

class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complainant_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    grievance_type = Column(String(50))
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(String(30), default="submitted")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    resolution = Column(Text)
    resolution_date = Column(DateTime)
    satisfaction_rating = Column(Integer, CheckConstraint("satisfaction_rating >= 1 AND satisfaction_rating <= 5"))
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complainant = relationship("Member", foreign_keys=[complainant_id])
    assignee = relationship("Member", foreign_keys=[assigned_to])

class InternalElection(Base):
    __tablename__ = "internal_elections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_title = Column(String(200), nullable=False)
    election_type = Column(String(50))
    position_contested = Column(String(200))
    election_date = Column(Date, nullable=False)
    nomination_start_date = Column(Date)
    nomination_end_date = Column(Date)
    campaign_start_date = Column(Date)
    campaign_end_date = Column(Date)
    eligible_voters_count = Column(Integer)
    actual_voters_count = Column(Integer)
    election_method = Column(String(30))
    status = Column(String(30), default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)

    candidates = relationship("ElectionCandidate", back_populates="election")
    votes = relationship("ElectionVote", back_populates="election")

class ElectionCandidate(Base):
    __tablename__ = "election_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("internal_elections.id", ondelete="CASCADE"))
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    running_mate_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    nomination_date = Column(DateTime, default=datetime.utcnow)
    manifesto_url = Column(String(500))
    campaign_slogan = Column(String(500))
    votes_received = Column(Integer, default=0)
    is_winner = Column(Boolean, default=False)
    withdrawal_date = Column(DateTime)
    withdrawal_reason = Column(Text)

    election = relationship("InternalElection", back_populates="candidates")
    candidate = relationship("Member", foreign_keys=[candidate_id])
    running_mate = relationship("Member", foreign_keys=[running_mate_id])

class ElectionVote(Base):
    __tablename__ = "election_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("internal_elections.id", ondelete="CASCADE"))
    voter_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("election_candidates.id", ondelete="CASCADE"))
    vote_timestamp = Column(DateTime, default=datetime.utcnow)
    vote_method = Column(String(30))
    is_valid = Column(Boolean, default=True)
    invalidation_reason = Column(Text)

    election = relationship("InternalElection", back_populates="votes")
    voter = relationship("Member")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    event_type = Column(String(50))
    event_id = Column(UUID(as_uuid=True))
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    attendance_method = Column(String(30))
    location = Column(String(200))
    verified_by = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", foreign_keys=[member_id])
    verifier = relationship("Member", foreign_keys=[verified_by])

class DisciplinaryAction(Base):
    __tablename__ = "disciplinary_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    action_type = Column(String(50))
    reason = Column(Text, nullable=False)
    action_date = Column(Date, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date)
    issued_by = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    committee_id = Column(UUID(as_uuid=True), ForeignKey("committees.id"))
    appeal_status = Column(String(30))
    appeal_date = Column(Date)
    appeal_decision = Column(Text)
    reversed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", foreign_keys=[member_id])
    issuer = relationship("Member", foreign_keys=[issued_by])
    committee = relationship("Committee")

class Partner(Base):
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_name = Column(String(200), nullable=False)
    partner_type = Column(String(50))
    contact_person = Column(String(200))
    contact_email = Column(String(150))
    contact_phone = Column(String(20))
    partnership_status = Column(String(30), default="active")
    agreement_date = Column(Date)
    agreement_expiry = Column(Date)
    partnership_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)