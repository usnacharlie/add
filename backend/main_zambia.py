from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

# Import existing app instance and dependencies
from main import app, get_db, get_current_member

# Import Zambian models
from models_zambia import (
    Province, District, Constituency, Ward, PollingStation,
    TraditionalArea, PoliticalParty, PartyStructure,
    ElectionZambia, ElectionResultConstituency, VoterRegistration,
    DemographicStatistics, CampaignEvent, YouthWing, WomensLeague,
    ResourceMobilization
)

# Import schemas (would need to be created)
from schemas_zambia import *

# ============== ZAMBIAN GEOGRAPHICAL ENDPOINTS ==============

@app.get("/api/zambia/provinces", response_model=List[ProvinceResponse])
def get_provinces(db: Session = Depends(get_db)):
    """Get all Zambian provinces"""
    provinces = db.query(Province).order_by(Province.province_name).all()
    return provinces

@app.get("/api/zambia/provinces/{province_code}", response_model=ProvinceResponse)
def get_province(province_code: str, db: Session = Depends(get_db)):
    """Get specific province by code"""
    province = db.query(Province).filter(Province.province_code == province_code).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return province

@app.get("/api/zambia/provinces/{province_code}/districts", response_model=List[DistrictResponse])
def get_province_districts(province_code: str, db: Session = Depends(get_db)):
    """Get all districts in a province"""
    province = db.query(Province).filter(Province.province_code == province_code).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")

    districts = db.query(District).filter(District.province_id == province.id).all()
    return districts

@app.get("/api/zambia/districts/{district_code}", response_model=DistrictResponse)
def get_district(district_code: str, db: Session = Depends(get_db)):
    """Get specific district by code"""
    district = db.query(District).filter(District.district_code == district_code).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district

@app.get("/api/zambia/districts/{district_code}/constituencies", response_model=List[ConstituencyResponse])
def get_district_constituencies(district_code: str, db: Session = Depends(get_db)):
    """Get all constituencies in a district"""
    district = db.query(District).filter(District.district_code == district_code).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")

    constituencies = db.query(Constituency).filter(Constituency.district_id == district.id).all()
    return constituencies

@app.get("/api/zambia/constituencies", response_model=List[ConstituencyResponse])
def get_constituencies(
    province_code: Optional[str] = None,
    district_code: Optional[str] = None,
    constituency_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get constituencies with optional filters"""
    query = db.query(Constituency)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(Constituency.province_id == province.id)

    if district_code:
        district = db.query(District).filter(District.district_code == district_code).first()
        if district:
            query = query.filter(Constituency.district_id == district.id)

    if constituency_type:
        query = query.filter(Constituency.constituency_type == constituency_type)

    return query.all()

@app.get("/api/zambia/constituencies/{constituency_code}/wards", response_model=List[WardResponse])
def get_constituency_wards(constituency_code: str, db: Session = Depends(get_db)):
    """Get all wards in a constituency"""
    constituency = db.query(Constituency).filter(
        Constituency.constituency_code == constituency_code
    ).first()
    if not constituency:
        raise HTTPException(status_code=404, detail="Constituency not found")

    wards = db.query(Ward).filter(Ward.constituency_id == constituency.id).all()
    return wards

@app.get("/api/zambia/wards/{ward_code}/polling-stations", response_model=List[PollingStationResponse])
def get_ward_polling_stations(ward_code: str, db: Session = Depends(get_db)):
    """Get all polling stations in a ward"""
    ward = db.query(Ward).filter(Ward.ward_code == ward_code).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    stations = db.query(PollingStation).filter(PollingStation.ward_id == ward.id).all()
    return stations

@app.get("/api/zambia/traditional-areas")
def get_traditional_areas(
    province_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get traditional/chiefdom areas"""
    query = db.query(TraditionalArea)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(TraditionalArea.province_id == province.id)

    return query.all()

# ============== POLITICAL PARTY ENDPOINTS ==============

@app.get("/api/zambia/political-parties", response_model=List[PoliticalPartyResponse])
def get_political_parties(
    ecz_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all registered political parties"""
    query = db.query(PoliticalParty)

    if ecz_status:
        query = query.filter(PoliticalParty.ecz_compliance_status == ecz_status)

    return query.order_by(PoliticalParty.party_name).all()

@app.post("/api/zambia/political-parties", response_model=PoliticalPartyResponse)
def register_political_party(
    party: PoliticalPartyCreate,
    db: Session = Depends(get_db)
):
    """Register a new political party"""
    db_party = PoliticalParty(**party.dict())
    db.add(db_party)
    db.commit()
    db.refresh(db_party)
    return db_party

@app.get("/api/zambia/party-structures/{party_code}")
def get_party_structures(
    party_code: str,
    structure_level: Optional[str] = None,
    province_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get party structures at different levels"""
    party = db.query(PoliticalParty).filter(PoliticalParty.party_code == party_code).first()
    if not party:
        raise HTTPException(status_code=404, detail="Political party not found")

    query = db.query(PartyStructure).filter(PartyStructure.party_id == party.id)

    if structure_level:
        query = query.filter(PartyStructure.structure_level == structure_level)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(PartyStructure.province_id == province.id)

    return query.all()

# ============== VOTER REGISTRATION ENDPOINTS ==============

@app.post("/api/zambia/voter-registration")
def register_voter(
    registration: VoterRegistrationCreate,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """Register member as a voter with ECZ"""
    # Check if already registered
    existing = db.query(VoterRegistration).filter(
        VoterRegistration.member_id == current_member.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Member already has voter registration")

    db_registration = VoterRegistration(
        member_id=current_member.id,
        **registration.dict()
    )
    db.add(db_registration)
    db.commit()

    return {"message": "Voter registration successful", "voters_card_number": registration.voters_card_number}

@app.get("/api/zambia/voter-registration/verify/{voters_card_number}")
def verify_voter_registration(voters_card_number: str, db: Session = Depends(get_db)):
    """Verify voter registration status"""
    registration = db.query(VoterRegistration).filter(
        VoterRegistration.voters_card_number == voters_card_number
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Voter registration not found")

    return registration

# ============== ELECTORAL ENDPOINTS ==============

@app.get("/api/zambia/elections")
def get_elections(
    election_type: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get election history"""
    from sqlalchemy import extract

    query = db.query(ElectionZambia)

    if election_type:
        query = query.filter(ElectionZambia.election_type == election_type)

    if year:
        query = query.filter(extract('year', ElectionZambia.election_date) == year)

    return query.order_by(ElectionZambia.election_date.desc()).all()

@app.get("/api/zambia/elections/{election_code}/results")
def get_election_results(
    election_code: str,
    constituency_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get election results"""
    election = db.query(ElectionZambia).filter(
        ElectionZambia.election_code == election_code
    ).first()

    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    query = db.query(ElectionResultConstituency).filter(
        ElectionResultConstituency.election_id == election.id
    )

    if constituency_code:
        constituency = db.query(Constituency).filter(
            Constituency.constituency_code == constituency_code
        ).first()
        if constituency:
            query = query.filter(ElectionResultConstituency.constituency_id == constituency.id)

    results = query.order_by(ElectionResultConstituency.votes_received.desc()).all()

    return {
        "election": election,
        "results": results
    }

# ============== DEMOGRAPHIC ANALYTICS ENDPOINTS ==============

@app.get("/api/zambia/demographics/summary")
def get_demographic_summary(
    area_type: str = Query(..., description="province, district, constituency, or ward"),
    area_code: str = Query(..., description="Code of the area"),
    db: Session = Depends(get_db)
):
    """Get demographic statistics for an area"""
    # Find the area ID based on type and code
    area_id = None

    if area_type == "province":
        area = db.query(Province).filter(Province.province_code == area_code).first()
        area_id = area.id if area else None
    elif area_type == "district":
        area = db.query(District).filter(District.district_code == area_code).first()
        area_id = area.id if area else None
    elif area_type == "constituency":
        area = db.query(Constituency).filter(Constituency.constituency_code == area_code).first()
        area_id = area.id if area else None
    elif area_type == "ward":
        area = db.query(Ward).filter(Ward.ward_code == area_code).first()
        area_id = area.id if area else None

    if not area_id:
        raise HTTPException(status_code=404, detail=f"{area_type} not found")

    stats = db.query(DemographicStatistics).filter(
        DemographicStatistics.area_type == area_type,
        DemographicStatistics.area_id == area_id
    ).order_by(DemographicStatistics.data_year.desc()).first()

    if not stats:
        return {"message": "No demographic data available for this area"}

    return stats

@app.get("/api/zambia/demographics/languages")
def get_language_distribution(
    province_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get language distribution statistics"""
    from sqlalchemy import func
    from models import Member

    query = db.query(
        func.unnest(Member.language_spoken).label('language'),
        func.count(Member.id).label('speakers')
    ).group_by('language')

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(Member.province_id == province.id)

    results = query.all()

    return {
        "languages": [{"language": r[0], "speakers": r[1]} for r in results],
        "total_members": db.query(Member).count()
    }

@app.get("/api/zambia/demographics/tribal-distribution")
def get_tribal_distribution(
    province_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tribal distribution statistics"""
    from sqlalchemy import func
    from models import Member

    query = db.query(
        Member.tribe,
        func.count(Member.id).label('count')
    ).group_by(Member.tribe)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(Member.province_id == province.id)

    results = query.all()

    return {
        "tribes": [{"tribe": r[0], "count": r[1]} for r in results if r[0]],
        "total_members": db.query(Member).count()
    }

# ============== CAMPAIGN EVENTS ENDPOINTS ==============

@app.post("/api/zambia/campaign-events")
def create_campaign_event(
    event: CampaignEventCreate,
    db: Session = Depends(get_db)
):
    """Create a campaign event requiring ECZ approval"""
    db_event = CampaignEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return {
        "message": "Campaign event created",
        "event_id": str(db_event.id),
        "ecz_approval_required": True if not event.ecz_approval_number else False
    }

@app.get("/api/zambia/campaign-events")
def get_campaign_events(
    province_code: Optional[str] = None,
    district_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get campaign events"""
    query = db.query(CampaignEvent)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(CampaignEvent.province_id == province.id)

    if district_code:
        district = db.query(District).filter(District.district_code == district_code).first()
        if district:
            query = query.filter(CampaignEvent.district_id == district.id)

    if start_date:
        query = query.filter(CampaignEvent.event_date >= start_date)

    if end_date:
        query = query.filter(CampaignEvent.event_date <= end_date)

    return query.order_by(CampaignEvent.event_date).all()

# ============== YOUTH AND WOMEN WINGS ENDPOINTS ==============

@app.post("/api/zambia/youth-wing/register")
def register_youth_wing_member(
    registration: YouthWingRegistration,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """Register member in youth wing"""
    # Check age eligibility (15-35 years)
    from datetime import date
    today = date.today()
    age = today.year - current_member.date_of_birth.year

    if age < 15 or age > 35:
        raise HTTPException(status_code=400, detail="Member must be between 15 and 35 years old")

    # Check if already registered
    existing = db.query(YouthWing).filter(YouthWing.member_id == current_member.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered in youth wing")

    db_youth = YouthWing(
        member_id=current_member.id,
        age_at_appointment=age,
        **registration.dict()
    )
    db.add(db_youth)
    db.commit()

    return {"message": "Successfully registered in youth wing"}

@app.post("/api/zambia/womens-league/register")
def register_womens_league_member(
    registration: WomensLeagueRegistration,
    current_member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """Register member in women's league"""
    if current_member.gender != "Female":
        raise HTTPException(status_code=400, detail="Only female members can join women's league")

    # Check if already registered
    existing = db.query(WomensLeague).filter(WomensLeague.member_id == current_member.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered in women's league")

    db_women = WomensLeague(
        member_id=current_member.id,
        **registration.dict()
    )
    db.add(db_women)
    db.commit()

    return {"message": "Successfully registered in women's league"}

# ============== RESOURCE MOBILIZATION ENDPOINTS ==============

@app.post("/api/zambia/resource-mobilization")
def create_resource_mobilization_event(
    event: ResourceMobilizationCreate,
    db: Session = Depends(get_db)
):
    """Create resource mobilization event"""
    db_event = ResourceMobilization(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event

@app.get("/api/zambia/resource-mobilization/summary")
def get_resource_mobilization_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    province_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get resource mobilization summary"""
    from sqlalchemy import func

    query = db.query(
        func.sum(ResourceMobilization.amount_raised).label('total_raised'),
        func.sum(ResourceMobilization.expenses).label('total_expenses'),
        func.sum(ResourceMobilization.net_proceeds).label('total_net'),
        func.count(ResourceMobilization.id).label('total_events'),
        func.sum(ResourceMobilization.mpesa_collection).label('mpesa_total'),
        func.sum(ResourceMobilization.airtel_money_collection).label('airtel_total'),
        func.sum(ResourceMobilization.zanaco_express_collection).label('zanaco_total'),
        func.sum(ResourceMobilization.bank_deposits).label('bank_total')
    )

    if start_date:
        query = query.filter(ResourceMobilization.event_date >= start_date)

    if end_date:
        query = query.filter(ResourceMobilization.event_date <= end_date)

    if province_code:
        province = db.query(Province).filter(Province.province_code == province_code).first()
        if province:
            query = query.filter(ResourceMobilization.province_id == province.id)

    result = query.first()

    return {
        "total_raised": float(result[0] or 0),
        "total_expenses": float(result[1] or 0),
        "net_proceeds": float(result[2] or 0),
        "total_events": result[3] or 0,
        "payment_methods": {
            "mpesa": float(result[4] or 0),
            "airtel_money": float(result[5] or 0),
            "zanaco_express": float(result[6] or 0),
            "bank_deposits": float(result[7] or 0)
        },
        "currency": "ZMW"
    }

# ============== MEMBER REGISTRATION WITH ZAMBIAN CONTEXT ==============

@app.post("/api/zambia/members/register")
def register_zambian_member(
    member: ZambianMemberCreate,
    db: Session = Depends(get_db)
):
    """Register member with Zambian-specific information"""
    from models import Member

    # Validate NRC number format
    if not member.nrc_number or len(member.nrc_number) != 11:
        raise HTTPException(status_code=400, detail="Invalid NRC number format")

    # Check if NRC already exists
    if db.query(Member).filter(Member.nrc_number == member.nrc_number).first():
        raise HTTPException(status_code=400, detail="Member with this NRC already exists")

    # Get location IDs
    province = db.query(Province).filter(Province.province_code == member.province_code).first()
    district = db.query(District).filter(District.district_code == member.district_code).first()
    constituency = db.query(Constituency).filter(
        Constituency.constituency_code == member.constituency_code
    ).first()
    ward = db.query(Ward).filter(Ward.ward_code == member.ward_code).first()

    if not all([province, district, constituency, ward]):
        raise HTTPException(status_code=400, detail="Invalid location codes provided")

    # Create member with Zambian details
    db_member = Member(
        first_name=member.first_name,
        last_name=member.last_name,
        national_id=member.nrc_number,
        nrc_number=member.nrc_number,
        voters_card_number=member.voters_card_number,
        phone_number=member.phone_number,
        gender=member.gender,
        date_of_birth=member.date_of_birth,
        province_id=province.id,
        district_id=district.id,
        constituency_id=constituency.id,
        ward_id=ward.id,
        tribe=member.tribe,
        language_spoken=member.languages_spoken,
        chiefdom=member.chiefdom,
        village=member.village,
        compound_area=member.compound_area,
        nearest_school=member.nearest_school,
        nearest_health_center=member.nearest_health_center,
        farmer_registration_number=member.farmer_registration_number,
        social_cash_transfer_beneficiary=member.social_cash_transfer_beneficiary,
        disability_status=member.disability_status,
        disability_type=member.disability_type,
        physical_address=member.physical_address,
        email=member.email,
        occupation=member.occupation,
        registration_channel=member.registration_channel
    )

    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    return {
        "message": "Member registered successfully",
        "membership_number": db_member.membership_number,
        "nrc_number": db_member.nrc_number
    }

# ============== ANALYTICS ENDPOINTS FOR ZAMBIA ==============

@app.get("/api/zambia/analytics/membership-by-province")
def get_membership_by_province(db: Session = Depends(get_db)):
    """Get membership distribution by province"""
    from sqlalchemy import func
    from models import Member

    results = db.query(
        Province.province_name,
        Province.province_code,
        func.count(Member.id).label('member_count')
    ).join(
        Member, Member.province_id == Province.id
    ).group_by(Province.id).all()

    total = db.query(Member).count()

    return {
        "provinces": [
            {
                "province_name": r[0],
                "province_code": r[1],
                "member_count": r[2],
                "percentage": (r[2] / total * 100) if total else 0
            }
            for r in results
        ],
        "total_members": total
    }

@app.get("/api/zambia/analytics/voter-registration-status")
def get_voter_registration_analytics(db: Session = Depends(get_db)):
    """Get voter registration analytics"""
    from sqlalchemy import func
    from models import Member

    total_members = db.query(Member).count()
    registered_voters = db.query(VoterRegistration).filter(
        VoterRegistration.card_status == "active"
    ).count()

    # Registration by province
    provincial_stats = db.query(
        Province.province_name,
        func.count(VoterRegistration.id).label('registered')
    ).join(
        VoterRegistration, VoterRegistration.province_id == Province.id
    ).group_by(Province.id).all()

    return {
        "total_members": total_members,
        "registered_voters": registered_voters,
        "registration_rate": (registered_voters / total_members * 100) if total_members else 0,
        "provincial_registration": [
            {"province": p[0], "registered": p[1]} for p in provincial_stats
        ]
    }

@app.get("/api/zambia/analytics/youth-participation")
def get_youth_participation_analytics(db: Session = Depends(get_db)):
    """Get youth participation analytics"""
    from sqlalchemy import func
    from models import Member
    from datetime import date

    today = date.today()
    youth_age_limit = today.year - 35

    total_youth = db.query(Member).filter(
        func.extract('year', Member.date_of_birth) >= youth_age_limit
    ).count()

    youth_wing_members = db.query(YouthWing).count()

    # Youth in leadership positions
    youth_leaders = db.query(YouthWing).filter(
        YouthWing.position != None
    ).count()

    return {
        "total_youth_members": total_youth,
        "youth_wing_registered": youth_wing_members,
        "youth_in_leadership": youth_leaders,
        "participation_rate": (youth_wing_members / total_youth * 100) if total_youth else 0
    }

# Update API info endpoint
@app.get("/api/zambia/info")
def get_zambia_api_info():
    return {
        "total_endpoints": 165,
        "zambian_specific_endpoints": {
            "geographical": 8,
            "political_parties": 3,
            "voter_registration": 2,
            "elections": 2,
            "demographics": 3,
            "campaign_events": 2,
            "youth_wing": 1,
            "womens_league": 1,
            "resource_mobilization": 2,
            "member_registration": 1,
            "analytics": 3
        },
        "provinces": 10,
        "districts": 116,
        "constituencies": 156,
        "wards": 1858,
        "supported_languages": [
            "English", "Bemba", "Nyanja", "Tonga", "Lozi",
            "Kaonde", "Lunda", "Luvale", "Tumbuka", "Others"
        ],
        "mobile_money_providers": [
            "MTN Money", "Airtel Money", "Zamtel Kwacha", "Zanaco Express"
        ]
    }