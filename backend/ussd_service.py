# ussd_service.py - USSD Service for ADD Zambia Membership Registration
"""
Updated USSD service with state management for member registration,
matching the new Member model structure.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import Member, USSDSession, Province, District, Constituency, Ward, User
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class USSDService:
    """USSD Service Handler for ADD Zambia"""

    def __init__(self):
        logger.info("USSD Service initialized")

    def get_or_create_session(self, session_id: str, phone_number: str, db: Session) -> USSDSession:
        """Get existing session or create new one"""
        session = db.query(USSDSession).filter(
            USSDSession.session_id == session_id,
            USSDSession.is_active == True
        ).first()

        if not session:
            session = USSDSession(
                session_id=session_id,
                phone_number=phone_number,
                current_step="main_menu",
                session_data={}
            )
            db.add(session)
            db.commit()
            logger.info(f"[USSD] New session created: {session_id}")

        return session

    def handle_request(self, session_id: str, phone_number: str, text: str, db: Session) -> Tuple[str, bool]:
        """Main USSD request handler"""
        session = self.get_or_create_session(session_id, phone_number, db)

        # Parse user input (last part after *)
        user_input = text.split("*")[-1] if text else ""

        # For new sessions, check if user is registered
        is_new_session = ((text == "" or text == "388*3") and
                          session.current_step == "main_menu" and
                          not session.session_data)

        if is_new_session:
            # Check if phone number is registered (by contact field)
            existing_member = db.query(Member).filter(Member.contact == phone_number).first()

            # Also check in users table
            existing_user = db.query(User).filter(User.phone == phone_number).first()

            if existing_member or existing_user:
                # User is registered
                member = existing_member if existing_member else (
                    db.query(Member).filter(Member.id == existing_user.member_id).first() if existing_user and existing_user.member_id else None
                )

                if member:
                    session.session_data = {"member_id": str(member.id)}
                    db.commit()
                    return self.show_main_menu(session, member, db)
                else:
                    # User exists but no member record
                    session.current_step = "register_nrc"
                    session.session_data = {}
                    db.commit()
                    response_text = "Welcome to ADD Zambia!\n\nLet's complete your registration.\n\nEnter your NRC number:\n(Format: 123456/78/9)"
                    return response_text, False
            else:
                # User is not registered - start registration
                session.current_step = "register_nrc"
                session.session_data = {}
                db.commit()
                response_text = "Welcome to ADD Zambia!\n\nYou are not registered.\nLet's register you.\n\nEnter your NRC number:\n(Format: 123456/78/9)"
                return response_text, False

        # Route to appropriate handler based on current step
        if session.current_step == "main_menu":
            response_text, end_session = self.handle_main_menu(session, user_input, db)
        elif session.current_step.startswith("register_"):
            response_text, end_session = self.handle_registration(session, user_input, db)
        elif session.current_step.startswith("check_"):
            response_text, end_session = self.handle_status_check(session, user_input, db)
        elif session.current_step.startswith("update_"):
            response_text, end_session = self.handle_update_info(session, user_input, db)
        else:
            response_text = "Session error. Please try again."
            end_session = True

        # Update session
        session.updated_at = datetime.utcnow()
        if end_session:
            session.is_active = False
        db.commit()

        return response_text, end_session

    def show_main_menu(self, session: USSDSession, member: Member, db: Session) -> Tuple[str, bool]:
        """Display main menu"""
        session.current_step = "main_menu"
        db.commit()

        menu = f"Welcome {member.name}!\n\n"
        menu += "ADD Zambia Menu\n\n"
        menu += "1. Check my details\n"
        menu += "2. Update contact\n"
        menu += "0. Exit"

        return menu, False

    def handle_main_menu(self, session: USSDSession, choice: str, db: Session) -> Tuple[str, bool]:
        """Handle main menu selection"""
        session_data = session.session_data or {}
        member_id = session_data.get("member_id")
        member = db.query(Member).filter(Member.id == member_id).first() if member_id else None

        if choice == "1":
            # Check member details
            if member:
                return self.show_member_details(member, db), True
            else:
                return "Session error. Please try again.", True

        elif choice == "2":
            # Update contact
            if member:
                session.current_step = "update_contact"
                db.commit()
                response = f"Current contact: {member.contact}\n\n"
                response += "Enter new contact number:\n(Format: 0971234567)"
                return response, False
            else:
                return "Session error. Please try again.", True

        elif choice == "0":
            return "Thank you for using ADD Zambia USSD service", True

        else:
            return "Invalid choice. Please try again.\n\n" + self.show_main_menu(session, member, db)[0], False

    # ==================== REGISTRATION FLOW ====================

    def handle_registration(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle registration steps"""
        step = session.current_step
        session_data = session.session_data or {}

        if step == "register_nrc":
            # Validate NRC format
            if len(user_input) < 6:
                return "Invalid NRC format.\nPlease enter your NRC:\n(Format: 123456/78/9)", False

            # Check if already registered
            existing = db.query(Member).filter(Member.nrc == user_input).first()
            if existing:
                return f"NRC already registered!\nMember: {existing.name}\n\nThank you!", True

            session_data["nrc"] = user_input
            session.session_data = session_data
            session.current_step = "register_voter_id"
            db.commit()
            return "Enter your Voter ID Number:", False

        elif step == "register_voter_id":
            # Validate voter ID
            if len(user_input) < 4:
                return "Invalid Voter ID.\nPlease enter your Voter ID Number:", False

            # Check if already registered
            existing = db.query(Member).filter(Member.voters_id == user_input).first()
            if existing:
                return f"Voter ID already registered!\nMember: {existing.name}\n\nThank you!", True

            session_data["voters_id"] = user_input
            session.session_data = session_data
            session.current_step = "register_name"
            db.commit()
            return "Enter your full name:", False

        elif step == "register_name":
            session_data["name"] = user_input
            session.session_data = session_data
            session.current_step = "register_gender"
            db.commit()
            return "Select gender:\n1. Male\n2. Female", False

        elif step == "register_gender":
            if user_input == "1":
                session_data["gender"] = "Male"
            elif user_input == "2":
                session_data["gender"] = "Female"
            else:
                return "Invalid choice.\nSelect gender:\n1. Male\n2. Female", False

            session.session_data = session_data
            session.current_step = "register_dob"
            db.commit()
            return "Enter date of birth:\n(Format: DD/MM/YYYY)\nExample: 15/05/1990", False

        elif step == "register_dob":
            # Basic validation
            try:
                dob = datetime.strptime(user_input, "%d/%m/%Y").date()
                session_data["date_of_birth"] = user_input
                session.session_data = session_data
                session.current_step = "register_province"
                db.commit()

                # Fetch provinces
                provinces_text = self.get_provinces_menu(db)
                return f"Select your province:\n{provinces_text}", False
            except:
                return "Invalid date format.\nEnter date of birth:\n(DD/MM/YYYY)\nExample: 15/05/1990", False

        elif step == "register_province":
            # Store province choice and fetch districts
            provinces = self.get_provinces(db)
            try:
                province_index = int(user_input) - 1
                if 0 <= province_index < len(provinces):
                    selected_province = provinces[province_index]
                    session_data["province_id"] = selected_province["id"]
                    session.session_data = session_data
                    session.current_step = "register_district"
                    db.commit()

                    districts_text = self.get_districts_menu(selected_province["id"], db)
                    return f"Select your district:\n{districts_text}", False
                else:
                    return "Invalid choice. Try again.", False
            except:
                return "Invalid choice. Enter number only.", False

        elif step == "register_district":
            # Store district and fetch constituencies
            districts = self.get_districts(session_data.get("province_id"), db)
            try:
                district_index = int(user_input) - 1
                if 0 <= district_index < len(districts):
                    selected_district = districts[district_index]
                    session_data["district_id"] = selected_district["id"]
                    session.session_data = session_data
                    session.current_step = "register_constituency"
                    db.commit()

                    constituencies_text = self.get_constituencies_menu(selected_district["id"], db)
                    return f"Select your constituency:\n{constituencies_text}", False
                else:
                    return "Invalid choice. Try again.", False
            except:
                return "Invalid choice. Enter number only.", False

        elif step == "register_constituency":
            # Store constituency and fetch wards
            constituencies = self.get_constituencies(session_data.get("district_id"), db)
            try:
                constituency_index = int(user_input) - 1
                if 0 <= constituency_index < len(constituencies):
                    selected_constituency = constituencies[constituency_index]
                    session_data["constituency_id"] = selected_constituency["id"]
                    session.session_data = session_data
                    session.current_step = "register_ward"
                    db.commit()

                    wards_text = self.get_wards_menu(selected_constituency["id"], db)
                    return f"Select your ward:\n{wards_text}", False
                else:
                    return "Invalid choice. Try again.", False
            except:
                return "Invalid choice. Enter number only.", False

        elif step == "register_ward":
            # Store ward and create member
            wards = self.get_wards(session_data.get("constituency_id"), db)
            try:
                ward_index = int(user_input) - 1
                if 0 <= ward_index < len(wards):
                    selected_ward = wards[ward_index]
                    session_data["ward_id"] = selected_ward["id"]
                    session.session_data = session_data

                    # Create member
                    return self.create_member(session, db)
                else:
                    return "Invalid choice. Try again.", False
            except Exception as e:
                logger.error(f"[USSD] Registration error: {e}")
                return "Error. Please try again.", False

        return "Error in registration. Please start again.", True

    def create_member(self, session: USSDSession, db: Session) -> Tuple[str, bool]:
        """Create new member from session data"""
        try:
            session_data = session.session_data

            # Parse date of birth
            dob = datetime.strptime(session_data.get("date_of_birth"), "%d/%m/%Y").date()

            # Create member with new model structure
            new_member = Member(
                name=session_data.get("name"),
                nrc=session_data.get("nrc"),
                voters_id=session_data.get("voters_id"),
                contact=session.phone_number,
                gender=session_data.get("gender"),
                date_of_birth=dob,
                ward_id=int(session_data.get("ward_id")),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(new_member)
            db.commit()
            db.refresh(new_member)

            # Get ward details for display
            ward = db.query(Ward).filter(Ward.id == new_member.ward_id).first()
            ward_name = ward.name if ward else "Unknown"

            # Success message
            response = f"Registration successful!\n\n"
            response += f"Name: {new_member.name}\n"
            response += f"NRC: {new_member.nrc}\n"
            response += f"Ward: {ward_name}\n\n"
            response += f"Welcome to ADD Zambia!"

            logger.info(f"[USSD] Member registered: {new_member.name} (ID: {new_member.id})")
            return response, True

        except Exception as e:
            logger.error(f"[USSD] Member creation error: {e}")
            return "Registration failed. Please try again later.", True

    # ==================== STATUS CHECK FLOW ====================

    def handle_status_check(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle membership status check"""
        session_data = session.session_data or {}

        if session.current_step == "check_nrc":
            member = db.query(Member).filter(Member.nrc == user_input).first()

            if not member:
                return f"Member with NRC {user_input} not found.", True

            return self.show_member_details(member, db), True

        return "Error checking status.", True

    def show_member_details(self, member: Member, db: Session) -> str:
        """Display member details"""
        # Get ward details
        ward = db.query(Ward).filter(Ward.id == member.ward_id).first()
        ward_name = ward.name if ward else "N/A"

        # Get constituency
        constituency = db.query(Constituency).filter(Constituency.id == ward.constituency_id).first() if ward else None
        constituency_name = constituency.name if constituency else "N/A"

        response = f"Member Details:\n\n"
        response += f"Name: {member.name}\n"
        response += f"NRC: {member.nrc}\n"
        response += f"Contact: {member.contact}\n"
        response += f"Ward: {ward_name}\n"
        response += f"Constituency: {constituency_name}\n"

        if member.date_of_birth:
            response += f"DOB: {member.date_of_birth.strftime('%d/%m/%Y')}\n"

        return response

    # ==================== UPDATE INFORMATION FLOW ====================

    def handle_update_info(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle information update flow"""
        step = session.current_step
        session_data = session.session_data or {}

        if step == "update_contact":
            # Validate and update contact
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            # Clean phone number
            clean_phone = ''.join(c for c in user_input if c.isdigit())

            # Validate length
            if len(clean_phone) < 9 or len(clean_phone) > 15:
                return "Invalid phone number.\nEnter phone number:\n(Format: 0971234567)", False

            # Update contact
            member.contact = clean_phone
            member.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"[USSD] Contact updated for member {member.name}: {clean_phone}")

            return f"Contact updated successfully!\n\nNew contact: {clean_phone}\n\nThank you!", True

        return "Update error. Please try again.", True

    # ==================== GEOGRAPHY HELPERS ====================

    def get_provinces(self, db: Session) -> list:
        """Fetch provinces from database"""
        try:
            provinces = db.query(Province).order_by(Province.name).all()
            return [{"id": p.id, "name": p.name} for p in provinces]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching provinces: {e}")
            return []

    def get_provinces_menu(self, db: Session) -> str:
        """Get formatted provinces menu"""
        provinces = self.get_provinces(db)
        if not provinces:
            return "Error loading provinces"

        menu = ""
        for idx, province in enumerate(provinces[:10], 1):  # Limit to 10
            menu += f"{idx}. {province['name']}\n"
        return menu

    def get_districts(self, province_id: int, db: Session) -> list:
        """Fetch districts for a province from database"""
        try:
            districts = db.query(District).filter(
                District.province_id == province_id
            ).order_by(District.name).all()
            return [{"id": d.id, "name": d.name} for d in districts]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching districts: {e}")
            return []

    def get_districts_menu(self, province_id: int, db: Session) -> str:
        """Get formatted districts menu"""
        districts = self.get_districts(province_id, db)
        if not districts:
            return "Error loading districts"

        menu = ""
        for idx, district in enumerate(districts[:10], 1):
            menu += f"{idx}. {district['name']}\n"
        return menu

    def get_constituencies(self, district_id: int, db: Session) -> list:
        """Fetch constituencies for a district from database"""
        try:
            constituencies = db.query(Constituency).filter(
                Constituency.district_id == district_id
            ).order_by(Constituency.name).all()
            return [{"id": c.id, "name": c.name} for c in constituencies]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching constituencies: {e}")
            return []

    def get_constituencies_menu(self, district_id: int, db: Session) -> str:
        """Get formatted constituencies menu"""
        constituencies = self.get_constituencies(district_id, db)
        if not constituencies:
            return "Error loading constituencies"

        menu = ""
        for idx, constituency in enumerate(constituencies[:10], 1):
            menu += f"{idx}. {constituency['name']}\n"
        return menu

    def get_wards(self, constituency_id: int, db: Session) -> list:
        """Fetch wards for a constituency from database"""
        try:
            wards = db.query(Ward).filter(
                Ward.constituency_id == constituency_id
            ).order_by(Ward.name).all()
            return [{"id": w.id, "name": w.name} for w in wards]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching wards: {e}")
            return []

    def get_wards_menu(self, constituency_id: int, db: Session) -> str:
        """Get formatted wards menu"""
        wards = self.get_wards(constituency_id, db)
        if not wards:
            return "Error loading wards"

        menu = ""
        for idx, ward in enumerate(wards[:10], 1):
            menu += f"{idx}. {ward['name']}\n"
        return menu


# Create global instance
ussd_service = USSDService()
