"""
Event Management Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Event Schemas ==============

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[str] = Field(None, pattern="^(meeting|rally|training|social)$")
    start_date: datetime
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    venue: Optional[str] = None
    max_attendees: Optional[int] = Field(None, gt=0)
    province_id: Optional[int] = None
    district_id: Optional[int] = None
    constituency_id: Optional[int] = None
    ward_id: Optional[int] = None


class EventCreate(EventBase):
    created_by: int


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[str] = Field(None, pattern="^(meeting|rally|training|social)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    venue: Optional[str] = None
    max_attendees: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(upcoming|ongoing|completed|cancelled)$")
    province_id: Optional[int] = None
    district_id: Optional[int] = None
    constituency_id: Optional[int] = None
    ward_id: Optional[int] = None


class EventResponse(EventBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    registration_count: Optional[int] = 0
    attendance_count: Optional[int] = 0

    class Config:
        from_attributes = True


class EventDetailResponse(EventResponse):
    # Include location details if available
    province_name: Optional[str] = None
    district_name: Optional[str] = None
    constituency_name: Optional[str] = None
    ward_name: Optional[str] = None

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    total: int
    events: List[EventResponse]


# ============== Event Registration Schemas ==============

class EventRegistrationBase(BaseModel):
    event_id: int
    member_id: int


class EventRegistrationCreate(BaseModel):
    member_id: int
    notes: Optional[str] = None


class EventRegistrationUpdate(BaseModel):
    registration_status: Optional[str] = Field(None, pattern="^(registered|attended|cancelled)$")
    notes: Optional[str] = None


class EventRegistrationResponse(EventRegistrationBase):
    id: int
    registration_status: str
    registered_at: datetime
    attendance_marked_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class EventRegistrationWithMember(EventRegistrationResponse):
    member_name: str
    member_contact: Optional[str] = None

    class Config:
        from_attributes = True


class EventRegistrationListResponse(BaseModel):
    total: int
    registrations: List[EventRegistrationWithMember]


# ============== Event Attachment Schemas ==============

class EventAttachmentBase(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)


class EventAttachmentCreate(EventAttachmentBase):
    event_id: int


class EventAttachmentResponse(EventAttachmentBase):
    id: int
    event_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ============== Attendance Marking Schema ==============

class AttendanceMarkRequest(BaseModel):
    member_ids: List[int] = Field(..., min_items=1)
    mark_as_attended: bool = True


# ============== Event Statistics Schema ==============

class EventStatistics(BaseModel):
    total_events: int
    upcoming_events: int
    ongoing_events: int
    completed_events: int
    cancelled_events: int
    total_registrations: int
    total_attendance: int
