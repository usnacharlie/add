from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, DECIMAL, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

# ============== ZAMBIAN GEOGRAPHICAL MODELS ==============

class Province(Base):
    __tablename__ = "provinces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_code = Column(String(10), unique=True, nullable=False)
    province_name = Column(String(100), unique=True, nullable=False)
    capital_city = Column(String(100))
    population = Column(Integer)
    area_sq_km = Column(DECIMAL(10, 2))
    number_of_districts = Column(Integer)
    number_of_constituencies = Column(Integer)
    region = Column(String(50))  # Northern, Southern, Eastern, Western, Central
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    districts = relationship("District", back_populates="province")
    constituencies = relationship("Constituency", back_populates="province")
    wards = relationship("Ward", back_populates="province")

class District(Base):
    __tablename__ = "districts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="CASCADE"))
    district_code = Column(String(10), unique=True, nullable=False)
    district_name = Column(String(100), nullable=False)
    administrative_center = Column(String(100))
    population = Column(Integer)
    area_sq_km = Column(DECIMAL(10, 2))
    number_of_constituencies = Column(Integer)
    number_of_wards = Column(Integer)
    rural_urban = Column(String(20))  # rural, urban, mixed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province", back_populates="districts")
    constituencies = relationship("Constituency", back_populates="district")
    wards = relationship("Ward", back_populates="district")

class Constituency(Base):
    __tablename__ = "constituencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="CASCADE"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"))
    constituency_code = Column(String(10), unique=True, nullable=False)
    constituency_name = Column(String(100), nullable=False)
    mp_name = Column(String(200))  # Current Member of Parliament
    mp_party = Column(String(100))
    registered_voters = Column(Integer)
    polling_stations = Column(Integer)
    number_of_wards = Column(Integer)
    constituency_type = Column(String(30))  # urban, rural, mixed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province", back_populates="constituencies")
    district = relationship("District", back_populates="constituencies")
    wards = relationship("Ward", back_populates="constituency")

class Ward(Base):
    __tablename__ = "wards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="CASCADE"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id", ondelete="CASCADE"))
    ward_code = Column(String(10), unique=True, nullable=False)
    ward_name = Column(String(100), nullable=False)
    councillor_name = Column(String(200))
    councillor_party = Column(String(100))
    registered_voters = Column(Integer)
    polling_districts = Column(Integer)
    villages = Column(Integer)
    population = Column(Integer)
    ward_type = Column(String(30))  # urban, peri-urban, rural
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province", back_populates="wards")
    district = relationship("District", back_populates="wards")
    constituency = relationship("Constituency", back_populates="wards")
    polling_stations = relationship("PollingStation", back_populates="ward")

class PollingStation(Base):
    __tablename__ = "polling_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"))
    station_code = Column(String(20), unique=True, nullable=False)
    station_name = Column(String(200), nullable=False)
    location_description = Column(Text)
    gps_latitude = Column(DECIMAL(10, 8))
    gps_longitude = Column(DECIMAL(11, 8))
    registered_voters = Column(Integer)
    facility_type = Column(String(100))  # school, church, community center, etc.
    accessibility = Column(String(50))  # accessible, partially_accessible, not_accessible
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ward = relationship("Ward", back_populates="polling_stations")

class TraditionalArea(Base):
    __tablename__ = "traditional_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    chiefdom_name = Column(String(200), nullable=False)
    chief_title = Column(String(100))  # Paramount Chief, Senior Chief, Chief, etc.
    chief_name = Column(String(200))
    tribe = Column(String(100))
    headquarters = Column(String(200))
    subjects_population = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province")
    district = relationship("District")

# ============== ZAMBIAN POLITICAL PARTY MODELS ==============

class PoliticalParty(Base):
    __tablename__ = "political_parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    party_code = Column(String(10), unique=True, nullable=False)
    party_name = Column(String(200), unique=True, nullable=False)
    abbreviation = Column(String(20))
    registration_number = Column(String(50), unique=True)
    registration_date = Column(Date)
    party_symbol = Column(String(100))
    party_colors = Column(String(100))
    party_slogan = Column(String(500))
    headquarters_address = Column(Text)
    postal_address = Column(String(200))
    phone_numbers = Column(ARRAY(Text))
    email = Column(String(150))
    website = Column(String(200))
    president_name = Column(String(200))
    secretary_general = Column(String(200))
    treasurer = Column(String(200))
    youth_leader = Column(String(200))
    women_leader = Column(String(200))
    membership_count = Column(Integer)
    ecz_compliance_status = Column(String(50))  # compliant, non-compliant, suspended
    last_ecz_filing_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    structures = relationship("PartyStructure", back_populates="party")

class PartyStructure(Base):
    __tablename__ = "party_structures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    party_id = Column(UUID(as_uuid=True), ForeignKey("political_parties.id", ondelete="CASCADE"))
    structure_level = Column(String(50))  # national, provincial, district, constituency, ward, branch, village
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    office_name = Column(String(200))
    office_address = Column(Text)
    chairperson_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    secretary_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    treasurer_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    youth_chairperson_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    women_chairperson_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    members_count = Column(Integer)
    active_status = Column(Boolean, default=True)
    formation_date = Column(Date)
    last_meeting_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    party = relationship("PoliticalParty", back_populates="structures")
    province = relationship("Province")
    district = relationship("District")
    constituency = relationship("Constituency")
    ward = relationship("Ward")

# ============== ZAMBIAN ELECTORAL MODELS ==============

class ElectionZambia(Base):
    __tablename__ = "elections_zambia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_code = Column(String(20), unique=True, nullable=False)
    election_type = Column(String(50))  # presidential, parliamentary, local_government, by-election
    election_date = Column(Date, nullable=False)
    gazette_date = Column(Date)
    nomination_date = Column(Date)
    campaign_start_date = Column(Date)
    campaign_end_date = Column(Date)
    total_registered_voters = Column(Integer)
    total_votes_cast = Column(Integer)
    valid_votes = Column(Integer)
    rejected_votes = Column(Integer)
    voter_turnout_percentage = Column(DECIMAL(5, 2))
    winner_name = Column(String(200))
    winner_party = Column(String(100))
    runner_up_name = Column(String(200))
    runner_up_party = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    results = relationship("ElectionResultConstituency", back_populates="election")

class ElectionResultConstituency(Base):
    __tablename__ = "election_results_constituency"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections_zambia.id", ondelete="CASCADE"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    candidate_name = Column(String(200))
    party_id = Column(UUID(as_uuid=True), ForeignKey("political_parties.id"))
    votes_received = Column(Integer)
    percentage_votes = Column(DECIMAL(5, 2))
    position = Column(Integer)  # 1st, 2nd, 3rd, etc.
    elected = Column(Boolean, default=False)
    petitioned = Column(Boolean, default=False)
    petition_outcome = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    election = relationship("ElectionZambia", back_populates="results")
    constituency = relationship("Constituency")
    party = relationship("PoliticalParty")

class VoterRegistration(Base):
    __tablename__ = "voter_registration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    voters_card_number = Column(String(30), unique=True, nullable=False)
    registration_date = Column(Date, nullable=False)
    registration_center = Column(String(200))
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    polling_station_id = Column(UUID(as_uuid=True), ForeignKey("polling_stations.id"))
    card_status = Column(String(30))  # active, lost, damaged, replaced
    replacement_date = Column(Date)
    verification_status = Column(String(30))  # verified, pending, rejected
    fingerprint_captured = Column(Boolean, default=True)
    photo_captured = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member")
    province = relationship("Province")
    district = relationship("District")
    constituency = relationship("Constituency")
    ward = relationship("Ward")
    polling_station = relationship("PollingStation")

# ============== ZAMBIAN DEMOGRAPHIC MODELS ==============

class DemographicStatistics(Base):
    __tablename__ = "demographic_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_type = Column(String(30))  # province, district, constituency, ward
    area_id = Column(UUID(as_uuid=True))
    total_population = Column(Integer)
    male_population = Column(Integer)
    female_population = Column(Integer)
    youth_population = Column(Integer)  # 15-35 years
    elderly_population = Column(Integer)  # 65+ years
    literacy_rate = Column(DECIMAL(5, 2))
    unemployment_rate = Column(DECIMAL(5, 2))
    poverty_rate = Column(DECIMAL(5, 2))
    access_to_electricity = Column(DECIMAL(5, 2))
    access_to_clean_water = Column(DECIMAL(5, 2))
    access_to_health_facilities = Column(DECIMAL(5, 2))
    school_enrollment_rate = Column(DECIMAL(5, 2))
    main_economic_activity = Column(String(100))
    languages_spoken = Column(ARRAY(Text))
    major_tribes = Column(ARRAY(Text))
    urban_population_percentage = Column(DECIMAL(5, 2))
    rural_population_percentage = Column(DECIMAL(5, 2))
    data_year = Column(Integer)
    data_source = Column(String(100))  # Census, Survey, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

# ============== CAMPAIGN EVENTS SPECIFIC TO ZAMBIA ==============

class CampaignEvent(Base):
    __tablename__ = "campaign_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50))  # rally, door_to_door, roadshow, debate, townhall
    event_name = Column(String(200))
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    venue = Column(String(200))
    traditional_area = Column(String(200))
    event_date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    expected_attendance = Column(Integer)
    actual_attendance = Column(Integer)
    main_speaker = Column(String(200))
    other_speakers = Column(ARRAY(Text))
    key_messages = Column(ARRAY(Text))
    languages_used = Column(ARRAY(Text))
    police_notification_number = Column(String(100))
    ecz_approval_number = Column(String(100))
    security_arrangements = Column(Text)
    media_coverage = Column(ARRAY(Text))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province")
    district = relationship("District")
    constituency = relationship("Constituency")
    ward = relationship("Ward")

# ============== YOUTH AND WOMEN WINGS ==============

class YouthWing(Base):
    __tablename__ = "youth_wing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    position = Column(String(100))
    level = Column(String(50))  # national, provincial, district, constituency, ward
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    university_chapter = Column(String(200))  # UNZA, CBU, etc.
    college_chapter = Column(String(200))
    appointment_date = Column(Date)
    age_at_appointment = Column(Integer)
    education_level = Column(String(100))
    employment_status = Column(String(100))
    skills_training = Column(ARRAY(Text))
    leadership_training_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member")
    province = relationship("Province")
    district = relationship("District")
    constituency = relationship("Constituency")
    ward = relationship("Ward")

class WomensLeague(Base):
    __tablename__ = "womens_league"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    position = Column(String(100))
    level = Column(String(50))  # national, provincial, district, constituency, ward
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"))
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    women_group_affiliations = Column(ARRAY(Text))
    cooperative_membership = Column(ARRAY(Text))
    appointment_date = Column(Date)
    market_committee_member = Column(Boolean, default=False)
    church_group_leader = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    member = relationship("Member")
    province = relationship("Province")
    district = relationship("District")
    constituency = relationship("Constituency")
    ward = relationship("Ward")

# ============== RESOURCE MOBILIZATION ==============

class ResourceMobilization(Base):
    __tablename__ = "resource_mobilization"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobilization_type = Column(String(50))  # fundraising_dinner, concert, sports_tournament, chitenge_sales
    event_name = Column(String(200))
    province_id = Column(UUID(as_uuid=True), ForeignKey("provinces.id"))
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id"))
    target_amount = Column(DECIMAL(12, 2))
    amount_raised = Column(DECIMAL(12, 2))
    currency = Column(String(10), default="ZMW")
    event_date = Column(Date)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("members.id"))
    guest_of_honor = Column(String(200))
    attendance = Column(Integer)
    corporate_sponsors = Column(ARRAY(Text))
    individual_donors = Column(Integer)
    expenses = Column(DECIMAL(12, 2))
    net_proceeds = Column(DECIMAL(12, 2))
    beneficiary = Column(String(200))  # party_operations, campaign, youth_programs, etc.
    mpesa_collection = Column(DECIMAL(12, 2))
    airtel_money_collection = Column(DECIMAL(12, 2))
    zanaco_express_collection = Column(DECIMAL(12, 2))
    bank_deposits = Column(DECIMAL(12, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    province = relationship("Province")
    district = relationship("District")
    organizer = relationship("Member")