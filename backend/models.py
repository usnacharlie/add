from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class Member(Base):
    __tablename__ = "members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    membership_number = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    national_id = Column(String(50), unique=True, nullable=False, index=True)
    voter_id_number = Column(String(50), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    alternate_phone = Column(String(20))
    email = Column(String(150), unique=True, index=True)
    physical_address = Column(Text, nullable=False)
    postal_address = Column(String(200))
    constituency = Column(String(100), nullable=False, index=True)
    ward = Column(String(100), nullable=False, index=True)
    branch = Column(String(100), nullable=False, index=True)
    occupation = Column(String(100))
    employer = Column(String(150))
    education_level = Column(String(50))
    marital_status = Column(String(20))
    preferred_language = Column(String(50), default="English")
    literacy_level = Column(String(20), default="advanced")
    communication_preference = Column(String(20), default="sms")
    registration_channel = Column(String(20), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    membership_status = Column(String(20), default="pending", index=True)
    membership_type = Column(String(30), default="regular")
    photo_url = Column(String(500))
    id_document_url = Column(String(500))
    password_hash = Column(String(255))
    ussd_pin_hash = Column(String(255))  # 4-digit PIN for USSD authentication
    pin_attempts = Column(Integer, default=0)  # Track failed PIN attempts
    pin_locked_until = Column(DateTime)  # Lock account after 3 failed attempts
    last_login = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100))
    referred_by = Column(String(20))  # Membership number of referrer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship("MembershipPayment", back_populates="member")
    positions = relationship("Position", back_populates="member")
    activities = relationship("MemberActivity", back_populates="member")

class MembershipPayment(Base):
    __tablename__ = "membership_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_reference = Column(String(100), unique=True)
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_year = Column(Integer, nullable=False)
    payment_status = Column(String(20), default="pending")
    receipt_number = Column(String(50), unique=True)
    processed_by = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member", back_populates="payments")

class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    position_title = Column(String(100), nullable=False)
    position_level = Column(String(50), nullable=False)
    appointment_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    appointed_by = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member", back_populates="positions")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_name = Column(String(200), nullable=False)
    activity_type = Column(String(50), nullable=False)
    activity_date = Column(Date, nullable=False, index=True)
    location = Column(String(200), nullable=False)
    description = Column(Text)
    organizer = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attendees = relationship("MemberActivity", back_populates="activity")

class MemberActivity(Base):
    __tablename__ = "member_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"))
    attendance_status = Column(String(20), default="registered")
    check_in_time = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member", back_populates="activities")
    activity = relationship("Activity", back_populates="attendees")

class USSDSession(Base):
    __tablename__ = "ussd_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    current_step = Column(String(50), nullable=False)
    session_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    table_name = Column(String(50))
    record_id = Column(UUID(as_uuid=True))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)