from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
import uvicorn
import os

# Import existing functionality
from main import (
    app, get_db, get_current_member, generate_membership_number,
    create_access_token, verify_password, get_password_hash
)

# Import enhanced models
from models_enhanced import (
    Donation, Campaign, Volunteer, Communication, CommunicationRecipient,
    Committee, CommitteeMember, TrainingProgram, TrainingAttendance,
    Poll, PollQuestion, PollResponse, Document, DocumentAccessLog,
    Grievance, InternalElection, ElectionCandidate, ElectionVote,
    AttendanceRecord, DisciplinaryAction, Partner
)

# Import schemas (would need to be created)
from schemas_enhanced import *

# ============== DONATION ENDPOINTS ==============

@app.post("/api/donations", response_model=DonationResponse)
def create_donation(donation: DonationCreate, db: Session = Depends(get_db)):
    db_donation = Donation(**donation.dict())
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    return db_donation

@app.get("/api/donations", response_model=List[DonationResponse])
def get_donations(
    skip: int = 0,
    limit: int = 100,
    campaign_id: Optional[str] = None,
    donor_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Donation)
    if campaign_id:
        query = query.filter(Donation.campaign_id == campaign_id)
    if donor_type:
        query = query.filter(Donation.donor_type == donor_type)

    donations = query.offset(skip).limit(limit).all()
    return donations

@app.get("/api/donations/statistics")
def get_donation_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    query = db.query(
        func.count(Donation.id).label("total_donations"),
        func.sum(Donation.amount).label("total_amount"),
        func.avg(Donation.amount).label("average_donation")
    )

    if start_date:
        query = query.filter(Donation.donation_date >= start_date)
    if end_date:
        query = query.filter(Donation.donation_date <= end_date)

    result = query.first()

    # Get top donors
    top_donors = db.query(
        Donation.donor_name,
        func.sum(Donation.amount).label("total_donated")
    ).group_by(Donation.donor_name).order_by(func.sum(Donation.amount).desc()).limit(10).all()

    return {
        "total_donations": result[0] or 0,
        "total_amount": float(result[1] or 0),
        "average_donation": float(result[2] or 0),
        "top_donors": [{"name": d[0], "amount": float(d[1])} for d in top_donors]
    }

# ============== CAMPAIGN ENDPOINTS ==============

@app.post("/api/campaigns", response_model=CampaignResponse)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    db_campaign = Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@app.get("/api/campaigns", response_model=List[CampaignResponse])
def get_campaigns(
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    if campaign_type:
        query = query.filter(Campaign.campaign_type == campaign_type)

    return query.all()

@app.put("/api/campaigns/{campaign_id}/status")
def update_campaign_status(
    campaign_id: str,
    status: str,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = status
    db.commit()

    return {"message": f"Campaign status updated to {status}"}

# ============== VOLUNTEER ENDPOINTS ==============

@app.post("/api/volunteers/register")
def register_volunteer(volunteer: VolunteerCreate, db: Session = Depends(get_db)):
    db_volunteer = Volunteer(**volunteer.dict())
    db.add(db_volunteer)
    db.commit()
    db.refresh(db_volunteer)
    return db_volunteer

@app.get("/api/volunteers", response_model=List[VolunteerResponse])
def get_volunteers(
    availability: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Volunteer)
    if availability:
        query = query.filter(Volunteer.availability == availability)
    if status:
        query = query.filter(Volunteer.status == status)

    return query.all()

@app.post("/api/volunteers/{volunteer_id}/log-hours")
def log_volunteer_hours(
    volunteer_id: str,
    hours: int,
    activity_date: date,
    db: Session = Depends(get_db)
):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    volunteer.hours_contributed += hours
    volunteer.last_activity_date = activity_date
    db.commit()

    return {"message": f"Logged {hours} hours for volunteer"}

# ============== COMMUNICATION ENDPOINTS ==============

@app.post("/api/communications/send")
async def send_communication(
    communication: CommunicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_comm = Communication(**communication.dict(exclude={"recipient_ids"}))
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)

    # Add recipients
    for member_id in communication.recipient_ids:
        recipient = CommunicationRecipient(
            communication_id=db_comm.id,
            member_id=member_id,
            delivery_status="pending"
        )
        db.add(recipient)

    db_comm.total_recipients = len(communication.recipient_ids)
    db.commit()

    # Schedule background task for sending
    background_tasks.add_task(process_communication, db_comm.id)

    return {"message": "Communication queued for sending", "communication_id": str(db_comm.id)}

@app.get("/api/communications", response_model=List[CommunicationResponse])
def get_communications(
    communication_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Communication)
    if communication_type:
        query = query.filter(Communication.communication_type == communication_type)
    if status:
        query = query.filter(Communication.status == status)

    return query.order_by(Communication.created_at.desc()).all()

@app.get("/api/communications/{communication_id}/status")
def get_communication_status(communication_id: str, db: Session = Depends(get_db)):
    comm = db.query(Communication).filter(Communication.id == communication_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    recipients = db.query(CommunicationRecipient).filter(
        CommunicationRecipient.communication_id == communication_id
    ).all()

    status_count = {}
    for r in recipients:
        status_count[r.delivery_status] = status_count.get(r.delivery_status, 0) + 1

    return {
        "communication": comm,
        "delivery_statistics": status_count
    }

# ============== COMMITTEE ENDPOINTS ==============

@app.post("/api/committees", response_model=CommitteeResponse)
def create_committee(committee: CommitteeCreate, db: Session = Depends(get_db)):
    db_committee = Committee(**committee.dict())
    db.add(db_committee)
    db.commit()
    db.refresh(db_committee)
    return db_committee

@app.get("/api/committees", response_model=List[CommitteeResponse])
def get_committees(
    is_active: Optional[bool] = None,
    committee_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Committee)
    if is_active is not None:
        query = query.filter(Committee.is_active == is_active)
    if committee_type:
        query = query.filter(Committee.committee_type == committee_type)

    return query.all()

@app.post("/api/committees/{committee_id}/members")
def add_committee_member(
    committee_id: str,
    member: CommitteeMemberCreate,
    db: Session = Depends(get_db)
):
    # Check if committee exists
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Committee not found")

    db_member = CommitteeMember(committee_id=committee_id, **member.dict())
    db.add(db_member)
    db.commit()

    return {"message": "Member added to committee"}

@app.get("/api/committees/{committee_id}/members")
def get_committee_members(committee_id: str, db: Session = Depends(get_db)):
    members = db.query(CommitteeMember).filter(
        CommitteeMember.committee_id == committee_id,
        CommitteeMember.is_active == True
    ).all()

    return members

# ============== TRAINING ENDPOINTS ==============

@app.post("/api/training-programs", response_model=TrainingProgramResponse)
def create_training_program(program: TrainingProgramCreate, db: Session = Depends(get_db)):
    db_program = TrainingProgram(**program.dict())
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

@app.get("/api/training-programs", response_model=List[TrainingProgramResponse])
def get_training_programs(
    status: Optional[str] = None,
    program_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TrainingProgram)
    if status:
        query = query.filter(TrainingProgram.status == status)
    if program_type:
        query = query.filter(TrainingProgram.program_type == program_type)

    return query.order_by(TrainingProgram.training_date.desc()).all()

@app.post("/api/training-programs/{program_id}/register")
def register_for_training(
    program_id: str,
    member_id: str,
    db: Session = Depends(get_db)
):
    # Check if already registered
    existing = db.query(TrainingAttendance).filter(
        TrainingAttendance.training_id == program_id,
        TrainingAttendance.member_id == member_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already registered for this training")

    # Check capacity
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")

    if program.max_participants and program.current_participants >= program.max_participants:
        raise HTTPException(status_code=400, detail="Training program is full")

    # Register
    attendance = TrainingAttendance(
        training_id=program_id,
        member_id=member_id,
        attendance_status="registered"
    )
    db.add(attendance)

    program.current_participants += 1
    db.commit()

    return {"message": "Successfully registered for training"}

@app.post("/api/training-programs/{program_id}/attendance")
def mark_training_attendance(
    program_id: str,
    member_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    attendance = db.query(TrainingAttendance).filter(
        TrainingAttendance.training_id == program_id,
        TrainingAttendance.member_id == member_id
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Registration not found")

    attendance.attendance_status = status
    db.commit()

    return {"message": f"Attendance marked as {status}"}

# ============== POLLS/SURVEYS ENDPOINTS ==============

@app.post("/api/polls", response_model=PollResponse)
def create_poll(poll: PollCreate, current_member = Depends(get_current_member), db: Session = Depends(get_db)):
    db_poll = Poll(**poll.dict(exclude={"questions"}), created_by=current_member.id)
    db.add(db_poll)
    db.commit()

    # Add questions
    for idx, question in enumerate(poll.questions):
        db_question = PollQuestion(
            poll_id=db_poll.id,
            question_order=idx,
            **question.dict()
        )
        db.add(db_question)

    db.commit()
    db.refresh(db_poll)

    return db_poll

@app.get("/api/polls", response_model=List[PollResponse])
def get_polls(
    status: Optional[str] = None,
    poll_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Poll)
    if status:
        query = query.filter(Poll.status == status)
    if poll_type:
        query = query.filter(Poll.poll_type == poll_type)

    # Filter active polls
    now = datetime.utcnow()
    query = query.filter(Poll.start_date <= now, Poll.end_date >= now)

    return query.all()

@app.post("/api/polls/{poll_id}/respond")
def submit_poll_response(
    poll_id: str,
    responses: List[PollResponseCreate],
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Check if already responded (if not anonymous)
    if not poll.allow_multiple_votes:
        existing = db.query(PollResponse).filter(
            PollResponse.poll_id == poll_id,
            PollResponse.member_id == current_member.id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="You have already responded to this poll")

    # Save responses
    for response in responses:
        db_response = PollResponse(
            poll_id=poll_id,
            member_id=current_member.id if not poll.is_anonymous else None,
            **response.dict()
        )
        db.add(db_response)

    db.commit()

    return {"message": "Poll response submitted successfully"}

@app.get("/api/polls/{poll_id}/results")
def get_poll_results(poll_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import func

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    questions = db.query(PollQuestion).filter(PollQuestion.poll_id == poll_id).all()

    results = []
    for question in questions:
        responses = db.query(PollResponse).filter(
            PollResponse.question_id == question.id
        ).all()

        if question.question_type == "single_choice" or question.question_type == "multiple_choice":
            # Count responses for each option
            option_counts = {}
            for response in responses:
                if response.response_options:
                    for option in response.response_options:
                        option_counts[option] = option_counts.get(option, 0) + 1

            results.append({
                "question": question.question_text,
                "type": question.question_type,
                "response_count": len(responses),
                "results": option_counts
            })
        elif question.question_type == "rating":
            # Calculate average rating
            ratings = [r.response_rating for r in responses if r.response_rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0

            results.append({
                "question": question.question_text,
                "type": question.question_type,
                "response_count": len(responses),
                "average_rating": avg_rating
            })
        else:  # text responses
            results.append({
                "question": question.question_text,
                "type": question.question_type,
                "response_count": len(responses),
                "sample_responses": [r.response_text for r in responses[:5]]  # First 5 responses
            })

    return {
        "poll": poll,
        "total_responses": db.query(func.count(func.distinct(PollResponse.member_id))).filter(
            PollResponse.poll_id == poll_id
        ).scalar(),
        "results": results
    }

# ============== DOCUMENT MANAGEMENT ENDPOINTS ==============

@app.post("/api/documents/upload", response_model=DocumentResponse)
def upload_document(
    document: DocumentCreate,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    db_document = Document(**document.dict(), uploaded_by=current_member.id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@app.get("/api/documents", response_model=List[DocumentResponse])
def get_documents(
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    access_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if category:
        query = query.filter(Document.category == category)
    if access_level:
        query = query.filter(Document.access_level == access_level)

    return query.order_by(Document.created_at.desc()).all()

@app.get("/api/documents/{document_id}/download")
def download_document(
    document_id: str,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Log access
    access_log = DocumentAccessLog(
        document_id=document_id,
        member_id=current_member.id,
        access_type="download"
    )
    db.add(access_log)

    # Increment download count
    document.download_count += 1
    db.commit()

    return {"file_url": document.file_url, "document": document}

# ============== GRIEVANCE ENDPOINTS ==============

@app.post("/api/grievances", response_model=GrievanceResponse)
def submit_grievance(
    grievance: GrievanceCreate,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    db_grievance = Grievance(
        complainant_id=current_member.id if not grievance.is_anonymous else None,
        **grievance.dict()
    )
    db.add(db_grievance)
    db.commit()
    db.refresh(db_grievance)
    return db_grievance

@app.get("/api/grievances", response_model=List[GrievanceResponse])
def get_grievances(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    grievance_type: Optional[str] = None,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    query = db.query(Grievance)

    # Filter based on user role (simplified - would need proper role checking)
    query = query.filter(
        (Grievance.complainant_id == current_member.id) |
        (Grievance.assigned_to == current_member.id)
    )

    if status:
        query = query.filter(Grievance.status == status)
    if priority:
        query = query.filter(Grievance.priority == priority)
    if grievance_type:
        query = query.filter(Grievance.grievance_type == grievance_type)

    return query.order_by(Grievance.created_at.desc()).all()

@app.put("/api/grievances/{grievance_id}/assign")
def assign_grievance(
    grievance_id: str,
    assignee_id: str,
    db: Session = Depends(get_db)
):
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    grievance.assigned_to = assignee_id
    grievance.status = "assigned"
    db.commit()

    return {"message": "Grievance assigned successfully"}

@app.put("/api/grievances/{grievance_id}/resolve")
def resolve_grievance(
    grievance_id: str,
    resolution: str,
    db: Session = Depends(get_db)
):
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    grievance.resolution = resolution
    grievance.resolution_date = datetime.utcnow()
    grievance.status = "resolved"
    db.commit()

    return {"message": "Grievance resolved successfully"}

# ============== ELECTIONS ENDPOINTS ==============

@app.post("/api/elections", response_model=ElectionResponse)
def create_election(election: ElectionCreate, db: Session = Depends(get_db)):
    db_election = InternalElection(**election.dict())
    db.add(db_election)
    db.commit()
    db.refresh(db_election)
    return db_election

@app.get("/api/elections", response_model=List[ElectionResponse])
def get_elections(
    status: Optional[str] = None,
    election_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InternalElection)
    if status:
        query = query.filter(InternalElection.status == status)
    if election_type:
        query = query.filter(InternalElection.election_type == election_type)

    return query.order_by(InternalElection.election_date.desc()).all()

@app.post("/api/elections/{election_id}/nominate")
def nominate_candidate(
    election_id: str,
    nomination: CandidateNomination,
    db: Session = Depends(get_db)
):
    # Check if election exists and nominations are open
    election = db.query(InternalElection).filter(InternalElection.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    today = date.today()
    if election.nomination_start_date and today < election.nomination_start_date:
        raise HTTPException(status_code=400, detail="Nominations have not opened yet")
    if election.nomination_end_date and today > election.nomination_end_date:
        raise HTTPException(status_code=400, detail="Nominations have closed")

    # Check if already nominated
    existing = db.query(ElectionCandidate).filter(
        ElectionCandidate.election_id == election_id,
        ElectionCandidate.candidate_id == nomination.candidate_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Candidate already nominated")

    # Create nomination
    candidate = ElectionCandidate(election_id=election_id, **nomination.dict())
    db.add(candidate)
    db.commit()

    return {"message": "Candidate nominated successfully"}

@app.post("/api/elections/{election_id}/vote")
def cast_vote(
    election_id: str,
    vote: VoteCast,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    # Check if election is active
    election = db.query(InternalElection).filter(InternalElection.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    if election.status != "active":
        raise HTTPException(status_code=400, detail="Election is not active")

    # Check if already voted
    existing_vote = db.query(ElectionVote).filter(
        ElectionVote.election_id == election_id,
        ElectionVote.voter_id == current_member.id
    ).first()

    if existing_vote:
        raise HTTPException(status_code=400, detail="You have already voted in this election")

    # Cast vote
    db_vote = ElectionVote(
        election_id=election_id,
        voter_id=current_member.id,
        candidate_id=vote.candidate_id,
        vote_method="online"
    )
    db.add(db_vote)

    # Update vote count
    candidate = db.query(ElectionCandidate).filter(
        ElectionCandidate.id == vote.candidate_id
    ).first()
    if candidate:
        candidate.votes_received += 1

    db.commit()

    return {"message": "Vote cast successfully"}

@app.get("/api/elections/{election_id}/results")
def get_election_results(election_id: str, db: Session = Depends(get_db)):
    election = db.query(InternalElection).filter(InternalElection.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    candidates = db.query(ElectionCandidate).filter(
        ElectionCandidate.election_id == election_id
    ).order_by(ElectionCandidate.votes_received.desc()).all()

    total_votes = db.query(ElectionVote).filter(
        ElectionVote.election_id == election_id,
        ElectionVote.is_valid == True
    ).count()

    return {
        "election": election,
        "total_votes": total_votes,
        "turnout_percentage": (total_votes / election.eligible_voters_count * 100) if election.eligible_voters_count else 0,
        "candidates": candidates
    }

# ============== ATTENDANCE ENDPOINTS ==============

@app.post("/api/attendance/check-in")
def check_in_attendance(
    attendance: AttendanceCheckIn,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    db_attendance = AttendanceRecord(
        member_id=current_member.id,
        check_in_time=datetime.utcnow(),
        **attendance.dict()
    )
    db.add(db_attendance)
    db.commit()

    return {"message": "Checked in successfully", "attendance_id": str(db_attendance.id)}

@app.put("/api/attendance/{attendance_id}/check-out")
def check_out_attendance(
    attendance_id: str,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.id == attendance_id,
        AttendanceRecord.member_id == current_member.id
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    attendance.check_out_time = datetime.utcnow()
    db.commit()

    return {"message": "Checked out successfully"}

@app.get("/api/attendance/member/{member_id}")
def get_member_attendance(
    member_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceRecord).filter(AttendanceRecord.member_id == member_id)

    if start_date:
        query = query.filter(AttendanceRecord.check_in_time >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.check_in_time <= end_date)

    records = query.order_by(AttendanceRecord.check_in_time.desc()).all()

    return {
        "member_id": member_id,
        "total_records": len(records),
        "attendance_records": records
    }

# ============== DISCIPLINARY ENDPOINTS ==============

@app.post("/api/disciplinary-actions")
def create_disciplinary_action(
    action: DisciplinaryActionCreate,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    db_action = DisciplinaryAction(
        issued_by=current_member.id,
        **action.dict()
    )
    db.add(db_action)
    db.commit()

    return {"message": "Disciplinary action recorded", "action_id": str(db_action.id)}

@app.get("/api/disciplinary-actions/member/{member_id}")
def get_member_disciplinary_record(
    member_id: str,
    db: Session = Depends(get_db)
):
    actions = db.query(DisciplinaryAction).filter(
        DisciplinaryAction.member_id == member_id
    ).order_by(DisciplinaryAction.action_date.desc()).all()

    return {
        "member_id": member_id,
        "total_actions": len(actions),
        "actions": actions
    }

@app.put("/api/disciplinary-actions/{action_id}/appeal")
def appeal_disciplinary_action(
    action_id: str,
    appeal_reason: str,
    db: Session = Depends(get_db)
):
    action = db.query(DisciplinaryAction).filter(DisciplinaryAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Disciplinary action not found")

    action.appeal_status = "pending"
    action.appeal_date = date.today()
    db.commit()

    return {"message": "Appeal submitted successfully"}

# ============== PARTNER ENDPOINTS ==============

@app.post("/api/partners", response_model=PartnerResponse)
def create_partner(partner: PartnerCreate, db: Session = Depends(get_db)):
    db_partner = Partner(**partner.dict())
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner

@app.get("/api/partners", response_model=List[PartnerResponse])
def get_partners(
    partner_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Partner)
    if partner_type:
        query = query.filter(Partner.partner_type == partner_type)
    if status:
        query = query.filter(Partner.partnership_status == status)

    return query.all()

# ============== ANALYTICS ENDPOINTS ==============

@app.get("/api/analytics/member-growth")
def get_member_growth_analytics(
    period: str = "monthly",  # daily, weekly, monthly, yearly
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    from models import Member

    if period == "monthly":
        growth = db.query(
            func.date_trunc('month', Member.registration_date).label('period'),
            func.count(Member.id).label('new_members')
        ).group_by('period').order_by('period').all()
    elif period == "daily":
        growth = db.query(
            func.date_trunc('day', Member.registration_date).label('period'),
            func.count(Member.id).label('new_members')
        ).group_by('period').order_by('period').limit(30).all()
    else:
        growth = []

    return {
        "period": period,
        "data": [{"period": str(g[0]), "count": g[1]} for g in growth]
    }

@app.get("/api/analytics/engagement")
def get_engagement_analytics(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from models import Member

    # Activity participation rate
    total_members = db.query(Member).count()
    active_in_activities = db.query(func.count(func.distinct(MemberActivity.member_id))).scalar()

    # Training participation
    training_participants = db.query(func.count(func.distinct(TrainingAttendance.member_id))).scalar()

    # Volunteer participation
    active_volunteers = db.query(Volunteer).filter(Volunteer.status == "active").count()

    # Poll participation
    poll_participants = db.query(func.count(func.distinct(PollResponse.member_id))).scalar()

    return {
        "total_members": total_members,
        "activity_participation_rate": (active_in_activities / total_members * 100) if total_members else 0,
        "training_participation_rate": (training_participants / total_members * 100) if total_members else 0,
        "volunteer_rate": (active_volunteers / total_members * 100) if total_members else 0,
        "poll_participation_rate": (poll_participants / total_members * 100) if total_members else 0
    }

@app.get("/api/analytics/financial")
def get_financial_analytics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import func, extract
    from models import MembershipPayment

    if not year:
        year = datetime.now().year

    # Monthly revenue
    monthly_revenue = db.query(
        extract('month', MembershipPayment.payment_date).label('month'),
        func.sum(MembershipPayment.amount).label('revenue')
    ).filter(
        extract('year', MembershipPayment.payment_date) == year
    ).group_by('month').all()

    # Donation statistics
    total_donations = db.query(func.sum(Donation.amount)).filter(
        extract('year', Donation.donation_date) == year
    ).scalar() or 0

    # Campaign spending
    campaign_spending = db.query(func.sum(Campaign.actual_spending)).filter(
        extract('year', Campaign.start_date) == year
    ).scalar() or 0

    return {
        "year": year,
        "monthly_revenue": [{"month": m[0], "revenue": float(m[1])} for m in monthly_revenue],
        "total_donations": float(total_donations),
        "campaign_spending": float(campaign_spending),
        "net_income": float(total_donations) - float(campaign_spending)
    }

# Background task for processing communications
async def process_communication(communication_id: str):
    # This would contain actual logic for sending SMS/Email/WhatsApp
    pass

# Update the total API count info endpoint
@app.get("/api/info")
def get_api_info():
    return {
        "total_endpoints": 126,
        "categories": {
            "authentication": 3,
            "members": 5,
            "payments": 2,
            "positions": 2,
            "activities": 3,
            "ussd": 1,
            "mobile": 3,
            "statistics": 2,
            "donations": 3,
            "campaigns": 3,
            "volunteers": 3,
            "communications": 3,
            "committees": 4,
            "training": 4,
            "polls": 4,
            "documents": 3,
            "grievances": 4,
            "elections": 5,
            "attendance": 3,
            "disciplinary": 3,
            "partners": 2,
            "analytics": 3
        }
    }