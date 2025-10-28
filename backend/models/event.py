"""
Event Management Models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Event(Base):
    """Events table"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=True, index=True)  # 'meeting', 'rally', 'training', 'social'
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True)
    location = Column(String(200), nullable=True)
    venue = Column(Text, nullable=True)
    max_attendees = Column(Integer, nullable=True)
    status = Column(String(20), default='upcoming', index=True)  # 'upcoming', 'ongoing', 'completed', 'cancelled'
    created_by = Column(Integer, nullable=False)  # User/Admin ID who created the event

    # Location hierarchy (optional - for location-specific events)
    province_id = Column(Integer, ForeignKey("provinces.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    province = relationship("Province", foreign_keys=[province_id])
    district = relationship("District", foreign_keys=[district_id])
    constituency = relationship("Constituency", foreign_keys=[constituency_id])
    ward = relationship("Ward", foreign_keys=[ward_id])
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    attachments = relationship("EventAttachment", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event {self.title}>"


class EventRegistration(Base):
    """Event registrations table"""
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    registration_status = Column(String(20), default='registered', index=True)  # 'registered', 'attended', 'cancelled'
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    attendance_marked_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="registrations")
    member = relationship("Member")

    def __repr__(self):
        return f"<EventRegistration event_id={self.event_id} member_id={self.member_id}>"


class EventAttachment(Base):
    """Event attachments table (for documents, images, etc.)"""
    __tablename__ = "event_attachments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)  # 'image', 'document', 'pdf', etc.
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="attachments")

    def __repr__(self):
        return f"<EventAttachment {self.file_name}>"
