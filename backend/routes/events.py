"""
Events API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime

from backend.config.database import get_db
from backend.models import Event, EventRegistration, Member, Province, District, Constituency, Ward
from backend.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventDetailResponse,
    EventListResponse, EventRegistrationCreate, EventRegistrationResponse,
    EventRegistrationWithMember, EventRegistrationListResponse,
    AttendanceMarkRequest, EventStatistics
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """
    Create a new event
    """
    # Validate dates
    if event.end_date and event.end_date < event.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    # Create event
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Add registration and attendance counts
    response_data = EventResponse.from_orm(db_event)
    response_data.registration_count = 0
    response_data.attendance_count = 0

    return response_data


@router.get("", response_model=EventListResponse)
def list_events(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    event_type: Optional[str] = None,
    province_id: Optional[int] = None,
    district_id: Optional[int] = None,
    constituency_id: Optional[int] = None,
    ward_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all events with optional filters
    """
    query = db.query(Event)

    # Apply filters
    if status_filter:
        query = query.filter(Event.status == status_filter)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if province_id:
        query = query.filter(Event.province_id == province_id)
    if district_id:
        query = query.filter(Event.district_id == district_id)
    if constituency_id:
        query = query.filter(Event.constituency_id == constituency_id)
    if ward_id:
        query = query.filter(Event.ward_id == ward_id)
    if search:
        query = query.filter(
            or_(
                Event.title.ilike(f"%{search}%"),
                Event.description.ilike(f"%{search}%"),
                Event.location.ilike(f"%{search}%")
            )
        )

    # Get total count
    total = query.count()

    # Get events with registration counts
    events = query.order_by(Event.start_date.desc()).offset(skip).limit(limit).all()

    # Add registration and attendance counts to each event
    event_responses = []
    for event in events:
        registration_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id,
            EventRegistration.registration_status != 'cancelled'
        ).count()

        attendance_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id,
            EventRegistration.registration_status == 'attended'
        ).count()

        event_data = EventResponse.from_orm(event)
        event_data.registration_count = registration_count
        event_data.attendance_count = attendance_count
        event_responses.append(event_data)

    return {"total": total, "events": event_responses}


@router.get("/statistics", response_model=EventStatistics)
def get_event_statistics(db: Session = Depends(get_db)):
    """
    Get event statistics
    """
    total_events = db.query(Event).count()
    upcoming_events = db.query(Event).filter(Event.status == 'upcoming').count()
    ongoing_events = db.query(Event).filter(Event.status == 'ongoing').count()
    completed_events = db.query(Event).filter(Event.status == 'completed').count()
    cancelled_events = db.query(Event).filter(Event.status == 'cancelled').count()

    total_registrations = db.query(EventRegistration).filter(
        EventRegistration.registration_status != 'cancelled'
    ).count()

    total_attendance = db.query(EventRegistration).filter(
        EventRegistration.registration_status == 'attended'
    ).count()

    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "ongoing_events": ongoing_events,
        "completed_events": completed_events,
        "cancelled_events": cancelled_events,
        "total_registrations": total_registrations,
        "total_attendance": total_attendance
    }


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get event details
    """
    event = db.query(Event).options(
        joinedload(Event.province),
        joinedload(Event.district),
        joinedload(Event.constituency),
        joinedload(Event.ward)
    ).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    # Get registration and attendance counts
    registration_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status != 'cancelled'
    ).count()

    attendance_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status == 'attended'
    ).count()

    # Build response
    event_data = {
        **event.__dict__,
        "registration_count": registration_count,
        "attendance_count": attendance_count,
        "province_name": event.province.name if event.province else None,
        "district_name": event.district.name if event.district else None,
        "constituency_name": event.constituency.name if event.constituency else None,
        "ward_name": event.ward.name if event.ward else None
    }

    return EventDetailResponse(**event_data)


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    """
    Update event details
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    # Validate dates if both are provided
    start_date = event_update.start_date or db_event.start_date
    end_date = event_update.end_date or db_event.end_date

    if end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    # Update fields
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)

    # Add counts
    registration_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status != 'cancelled'
    ).count()

    attendance_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status == 'attended'
    ).count()

    event_data = EventResponse.from_orm(db_event)
    event_data.registration_count = registration_count
    event_data.attendance_count = attendance_count

    return event_data


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """
    Delete an event
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    db.delete(db_event)
    db.commit()

    return None


# ==================== Event Registration Endpoints ====================

@router.post("/{event_id}/register", response_model=EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(
    event_id: int,
    registration: EventRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Register a member for an event
    """
    # Verify event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    # Check if event is cancelled
    if event.status == 'cancelled':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for a cancelled event"
        )

    # Verify member exists
    member = db.query(Member).filter(Member.id == registration.member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {registration.member_id} not found"
        )

    # Check if already registered
    existing = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.member_id == registration.member_id,
        EventRegistration.registration_status != 'cancelled'
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member is already registered for this event"
        )

    # Check max attendees
    if event.max_attendees:
        current_registrations = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.registration_status != 'cancelled'
        ).count()

        if current_registrations >= event.max_attendees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event has reached maximum capacity"
            )

    # Create registration
    db_registration = EventRegistration(
        event_id=event_id,
        member_id=registration.member_id,
        notes=registration.notes
    )

    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)

    return db_registration


@router.get("/{event_id}/attendees", response_model=EventRegistrationListResponse)
def get_event_attendees(
    event_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Get all attendees for an event
    """
    # Verify event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    # Query registrations with member details
    query = db.query(EventRegistration, Member).join(
        Member, EventRegistration.member_id == Member.id
    ).filter(EventRegistration.event_id == event_id)

    if status_filter:
        query = query.filter(EventRegistration.registration_status == status_filter)

    registrations = query.all()

    # Build response
    attendee_list = []
    for reg, member in registrations:
        attendee_data = EventRegistrationWithMember(
            id=reg.id,
            event_id=reg.event_id,
            member_id=reg.member_id,
            registration_status=reg.registration_status,
            registered_at=reg.registered_at,
            attendance_marked_at=reg.attendance_marked_at,
            notes=reg.notes,
            member_name=member.name,
            member_contact=member.contact
        )
        attendee_list.append(attendee_data)

    return {"total": len(attendee_list), "registrations": attendee_list}


@router.post("/{event_id}/mark-attendance", response_model=dict)
def mark_attendance(
    event_id: int,
    attendance_data: AttendanceMarkRequest,
    db: Session = Depends(get_db)
):
    """
    Mark attendance for multiple members
    """
    # Verify event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found"
        )

    marked_count = 0
    for member_id in attendance_data.member_ids:
        registration = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.member_id == member_id
        ).first()

        if registration:
            if attendance_data.mark_as_attended:
                registration.registration_status = 'attended'
                registration.attendance_marked_at = datetime.utcnow()
            else:
                registration.registration_status = 'registered'
                registration.attendance_marked_at = None
            marked_count += 1

    db.commit()

    return {
        "message": f"Attendance marked for {marked_count} members",
        "marked_count": marked_count
    }


@router.delete("/{event_id}/register/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_registration(event_id: int, member_id: int, db: Session = Depends(get_db)):
    """
    Cancel event registration
    """
    registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.member_id == member_id
    ).first()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )

    registration.registration_status = 'cancelled'
    db.commit()

    return None


@router.get("/registrations/member/{member_id}")
def get_member_registrations(member_id: int, db: Session = Depends(get_db)):
    """
    Get all event registrations for a specific member
    """
    # Verify member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {member_id} not found"
        )

    # Query registrations with event details
    registrations = db.query(EventRegistration, Event).join(
        Event, EventRegistration.event_id == Event.id
    ).filter(
        EventRegistration.member_id == member_id,
        EventRegistration.registration_status != 'cancelled'
    ).order_by(Event.start_date.desc()).all()

    # Build response
    result = []
    for reg, event in registrations:
        result.append({
            "id": reg.id,
            "member_id": reg.member_id,
            "registration_status": reg.registration_status,
            "registered_at": reg.registered_at,
            "attendance_marked_at": reg.attendance_marked_at,
            "notes": reg.notes,
            "event": {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_date": event.start_date.isoformat() if event.start_date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "location": event.location,
                "venue": event.venue,
                "event_type": event.event_type,
                "status": event.status,
                "max_attendees": event.max_attendees
            }
        })

    return result
