# ussd_service.py - USSD Service for ADD Zambia Membership Registration
"""
Comprehensive USSD service with state management for member registration,
status checks, payments, and updates via USSD *388*3#
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Member, USSDSession, MembershipPayment
from models_zambia import Province, District, Constituency, Ward
from membership_notifications import notification_service
import bcrypt

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
        # Only treat as new session if: empty text OR exact service code
        # AND the session is in initial state (main_menu with no data)
        is_new_session = ((text == "" or text == "388*3") and
                          session.current_step == "main_menu" and
                          not session.session_data)

        if is_new_session:
            # Check if phone number is registered
            existing_member = db.query(Member).filter(Member.phone_number == phone_number).first()

            if existing_member:
                # User is registered - check if PIN is set
                if existing_member.ussd_pin_hash:
                    # Has PIN - verify it
                    session.current_step = "auth_verify_pin"
                    session.session_data = {"member_id": str(existing_member.id)}
                    db.commit()
                    response_text = f"Welcome {existing_member.first_name}!\n\nEnter your PIN:"
                    end_session = False
                else:
                    # No PIN - prompt to create one
                    session.current_step = "auth_create_pin"
                    session.session_data = {"member_id": str(existing_member.id)}
                    db.commit()
                    response_text = f"Welcome {existing_member.first_name}!\n\nFor security, please create a 4-digit PIN:\n(Example: 1234)"
                    end_session = False
            else:
                # User is not registered - start registration
                session.current_step = "register_nrc"
                session.session_data = {}
                db.commit()
                response_text = "Welcome to ADD Zambia!\n\nYou are not registered.\nLet's register you.\n\nEnter your NRC number:\n(Format: 123456/78/9)"
                end_session = False

            return response_text, end_session

        # Route to appropriate handler based on current step
        if session.current_step == "auth_verify_pin":
            response_text, end_session = self.handle_auth_verify_pin(session, user_input, db)
        elif session.current_step == "auth_create_pin":
            response_text, end_session = self.handle_auth_create_pin(session, user_input, db)
        elif session.current_step == "auth_confirm_pin":
            response_text, end_session = self.handle_auth_confirm_pin(session, user_input, db)
        elif session.current_step == "main_menu":
            response_text, end_session = self.handle_main_menu(session, user_input, db)
        elif session.current_step.startswith("register_"):
            response_text, end_session = self.handle_registration(session, user_input, db)
        elif session.current_step.startswith("check_"):
            response_text, end_session = self.handle_status_check(session, user_input, db)
        elif session.current_step.startswith("payment_"):
            response_text, end_session = self.handle_payment(session, user_input, phone_number, db)
        elif session.current_step.startswith("update_"):
            response_text, end_session = self.handle_update_info(session, user_input, db)
        elif session.current_step.startswith("pin_"):
            response_text, end_session = self.handle_pin_setup(session, user_input, db)
        else:
            response_text = "Session error. Please try again."
            end_session = True

        # Update session
        session.updated_at = datetime.utcnow()
        if end_session:
            session.is_active = False
        db.commit()

        return response_text, end_session

    def show_main_menu(self, session: USSDSession, db: Session) -> Tuple[str, bool]:
        """Display main menu"""
        session.current_step = "main_menu"
        db.commit()

        menu = "ADD Zambia Main Menu\n\n"
        menu += "1. Check membership status\n"
        menu += "2. Make payment\n"
        menu += "3. Update information\n"
        menu += "4. Change PIN\n"
        menu += "0. Exit"

        return menu, False

    def handle_main_menu(self, session: USSDSession, choice: str, db: Session) -> Tuple[str, bool]:
        """Handle main menu selection"""
        # Get member from session
        session_data = session.session_data or {}
        member_id = session_data.get("member_id")
        member = db.query(Member).filter(Member.id == member_id).first() if member_id else None

        if choice == "1":
            # Check membership status
            if member:
                return self.show_member_status(member), True
            else:
                return "Session error. Please try again.", True

        elif choice == "2":
            # Make payment
            if member:
                session_data["payment_member_id"] = str(member.id)
                session_data["payment_member_number"] = member.membership_number
                session.session_data = session_data
                session.current_step = "payment_year"
                db.commit()

                current_year = datetime.now().year
                response = f"Payment for: {member.first_name} {member.last_name}\n\n"
                response += f"Select payment year:\n"
                response += f"1. {current_year}\n"
                response += f"2. {current_year + 1}\n"
                response += f"0. Cancel"
                return response, False
            else:
                return "Session error. Please try again.", True

        elif choice == "3":
            # Update information
            if member:
                session.current_step = "update_menu"
                db.commit()
                response = "Update Information\n\n"
                response += "What would you like to update?\n\n"
                response += "1. Phone number\n"
                response += "2. Address\n"
                response += "0. Cancel"
                return response, False
            else:
                return "Session error. Please try again.", True

        elif choice == "4":
            # Change PIN
            if member:
                session_data["pin_member_id"] = str(member.id)
                session_data["has_pin"] = member.ussd_pin_hash is not None
                session.session_data = session_data
                session.current_step = "pin_verify_old"
                db.commit()
                return "Enter your current PIN:", False
            else:
                return "Session error. Please try again.", True

        elif choice == "0":
            return "Thank you for using ADD Zambia USSD service", True

        else:
            return "Invalid choice. Please try again.\n\n" + self.show_main_menu(session, db)[0], False

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
            existing = db.query(Member).filter(Member.national_id == user_input).first()
            if existing:
                return f"NRC already registered!\nYour membership: {existing.membership_number}\n\nThank you!", True

            session_data["national_id"] = user_input
            session.session_data = session_data
            session.current_step = "register_voter_id"
            db.commit()
            return "Enter your Voter ID Number:\n(Format: VR2024123456 or similar)", False

        elif step == "register_voter_id":
            # Validate voter ID (basic validation)
            if len(user_input) < 4:
                return "Invalid Voter ID.\nPlease enter your Voter ID Number:", False

            # Check if already registered
            existing = db.query(Member).filter(Member.voter_id_number == user_input).first()
            if existing:
                return f"Voter ID already registered!\nYour membership: {existing.membership_number}\n\nThank you!", True

            session_data["voter_id_number"] = user_input
            session.session_data = session_data
            session.current_step = "register_first_name"
            db.commit()
            return "Enter your first name:", False

        elif step == "register_first_name":
            session_data["first_name"] = user_input
            session.session_data = session_data
            session.current_step = "register_last_name"
            db.commit()
            return "Enter your last name:", False

        elif step == "register_last_name":
            session_data["last_name"] = user_input
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
                session.current_step = "register_marital_status"
                db.commit()

                return "Select marital status:\n1. Single\n2. Married\n3. Divorced\n4. Widowed\n0. Skip", False
            except:
                return "Invalid date format.\nEnter date of birth:\n(DD/MM/YYYY)\nExample: 15/05/1990", False

        elif step == "register_marital_status":
            marital_statuses = {
                "1": "Single",
                "2": "Married",
                "3": "Divorced",
                "4": "Widowed",
                "0": None
            }

            if user_input in marital_statuses:
                session_data["marital_status"] = marital_statuses[user_input]
                session.session_data = session_data
                session.current_step = "register_email"
                db.commit()
                return "Enter your email address:\n(Or enter 0 to skip)", False
            else:
                return "Invalid choice.\n1. Single\n2. Married\n3. Divorced\n4. Widowed\n0. Skip", False

        elif step == "register_email":
            # Optional email
            if user_input == "0" or user_input.lower() == "skip":
                session_data["email"] = None
            else:
                # Basic email validation
                if "@" in user_input and "." in user_input:
                    session_data["email"] = user_input.lower()
                else:
                    return "Invalid email format.\nEnter email or 0 to skip:", False

            session.session_data = session_data
            session.current_step = "register_language"
            db.commit()

            return "Select preferred language:\n1. English\n2. Bemba\n3. Nyanja\n4. Tonga\n5. Lozi\n6. Other", False

        elif step == "register_language":
            languages = {
                "1": "English",
                "2": "Bemba",
                "3": "Nyanja",
                "4": "Tonga",
                "5": "Lozi",
                "6": "English"  # Default for "Other"
            }

            if user_input in languages:
                session_data["preferred_language"] = languages[user_input]
                session.session_data = session_data
                session.current_step = "register_literacy"
                db.commit()
                return "Select literacy level:\n1. Can read and write\n2. Basic reading\n3. Cannot read", False
            else:
                return "Invalid choice. Enter 1-6.", False

        elif step == "register_literacy":
            literacy_levels = {
                "1": "advanced",
                "2": "basic",
                "3": "none"
            }

            if user_input in literacy_levels:
                session_data["literacy_level"] = literacy_levels[user_input]
                session.session_data = session_data
                session.current_step = "register_communication"
                db.commit()
                return "Preferred communication:\n1. SMS\n2. WhatsApp\n3. Voice Call\n4. Email", False
            else:
                return "Invalid choice. Enter 1-3.", False

        elif step == "register_communication":
            communication_prefs = {
                "1": "sms",
                "2": "whatsapp",
                "3": "voice",
                "4": "email"
            }

            if user_input in communication_prefs:
                session_data["communication_preference"] = communication_prefs[user_input]
                session.session_data = session_data
                session.current_step = "register_province"
                db.commit()

                # Fetch provinces
                provinces_text = self.get_provinces_menu(db)
                return f"Select your province:\n{provinces_text}", False
            else:
                return "Invalid choice. Enter 1-4.", False

        elif step == "register_province":
            # Store province choice and fetch districts
            provinces = self.get_provinces(db)
            try:
                province_index = int(user_input) - 1
                if 0 <= province_index < len(provinces):
                    selected_province = provinces[province_index]
                    session_data["province_id"] = selected_province["id"]
                    session_data["province"] = selected_province["province_name"]
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
            session_data = session.session_data or {}
            districts = self.get_districts(session_data.get("province_id"), db)
            try:
                district_index = int(user_input) - 1
                if 0 <= district_index < len(districts):
                    selected_district = districts[district_index]
                    session_data["district_id"] = selected_district["id"]
                    session_data["district"] = selected_district["district_name"]
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
            session_data = session.session_data or {}
            constituencies = self.get_constituencies(session_data.get("district_id"), db)
            try:
                constituency_index = int(user_input) - 1
                if 0 <= constituency_index < len(constituencies):
                    selected_constituency = constituencies[constituency_index]
                    session_data["constituency_id"] = selected_constituency["id"]
                    session_data["constituency"] = selected_constituency["constituency_name"]
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
            # Store ward and ask for physical address
            session_data = session.session_data or {}
            wards = self.get_wards(session_data.get("constituency_id"), db)
            try:
                ward_index = int(user_input) - 1
                if 0 <= ward_index < len(wards):
                    selected_ward = wards[ward_index]
                    session_data["ward_id"] = selected_ward["id"]
                    session_data["ward"] = selected_ward["ward_name"]
                    session.session_data = session_data
                    session.current_step = "register_address"
                    db.commit()

                    return "Enter your physical address:\n(House/plot number, street, area)", False
                else:
                    return "Invalid choice. Try again.", False
            except Exception as e:
                logger.error(f"[USSD] Registration error: {e}")
                return "Error. Please try again.", False

        elif step == "register_address":
            # Store address and create member
            if len(user_input) < 3:
                return "Address too short.\nEnter your physical address:", False

            session_data["physical_address"] = user_input
            session.session_data = session_data

            # Create member
            return self.create_member(session, db)

        return "Error in registration. Please start again.", True

    def create_member(self, session: USSDSession, db: Session) -> Tuple[str, bool]:
        """Create new member from session data"""
        try:
            session_data = session.session_data

            # Generate membership number
            import random
            import string
            while True:
                membership_number = "PM" + ''.join(random.choices(string.digits, k=8))
                if not db.query(Member).filter(Member.membership_number == membership_number).first():
                    break

            # Parse date of birth
            dob = datetime.strptime(session_data.get("date_of_birth"), "%d/%m/%Y").date()

            # Create member with all fields matching frontend registration
            new_member = Member(
                membership_number=membership_number,
                first_name=session_data.get("first_name"),
                last_name=session_data.get("last_name"),
                national_id=session_data.get("national_id"),
                voter_id_number=session_data.get("voter_id_number"),
                phone_number=session.phone_number,
                email=session_data.get("email"),
                gender=session_data.get("gender"),
                date_of_birth=dob,
                marital_status=session_data.get("marital_status"),
                constituency=session_data.get("constituency"),
                ward=session_data.get("ward"),
                branch=session_data.get("ward"),  # Use ward as branch
                physical_address=session_data.get("physical_address"),
                preferred_language=session_data.get("preferred_language", "English"),
                literacy_level=session_data.get("literacy_level", "advanced"),
                communication_preference=session_data.get("communication_preference", "sms"),
                registration_channel="ussd"
            )

            db.add(new_member)
            db.commit()
            db.refresh(new_member)

            # Send welcome notification
            try:
                notification_service.notify_new_member(new_member)
                logger.info(f"[USSD] Welcome notification sent to {membership_number}")
            except Exception as e:
                logger.error(f"[USSD] Notification error: {e}")

            # Success message
            response = f"Registration successful!\n\n"
            response += f"Your membership number:\n{membership_number}\n\n"
            response += f"Name: {new_member.first_name} {new_member.last_name}\n"
            response += f"Location: {new_member.ward}, {new_member.constituency}\n\n"
            response += f"Check your SMS for details.\n"
            response += f"Annual fee: K25\n\n"
            response += f"Thank you for joining ADD!"

            logger.info(f"[USSD] Member registered: {membership_number}")
            return response, True

        except Exception as e:
            logger.error(f"[USSD] Member creation error: {e}")
            return "Registration failed. Please try again later.", True

    # ==================== STATUS CHECK FLOW ====================

    def handle_status_check(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle membership status check"""
        session_data = session.session_data or {}

        if session.current_step == "check_membership_number":
            member = db.query(Member).filter(Member.membership_number == user_input).first()

            if not member:
                return f"Member {user_input} not found.\n\nPlease check your number and try again.", True

            # Check if member has PIN set
            if member.ussd_pin_hash:
                session_data["check_member_id"] = str(member.id)
                session.session_data = session_data
                session.current_step = "check_verify_pin"
                db.commit()
                return "Enter your PIN:", False
            else:
                # No PIN required, show status directly
                return self.show_member_status(member), True

        elif session.current_step == "check_verify_pin":
            member_id = session_data.get("check_member_id")
            member = db.query(Member).filter(Member.id == int(member_id)).first()

            if not member:
                return "Session error. Please try again.", True

            # Verify PIN
            verified, error_msg = self.verify_member_pin(member, user_input, db)

            if not verified:
                return error_msg, True

            # PIN verified, show status
            return self.show_member_status(member), True

        return "Error checking status.", True

    def show_member_status(self, member: Member) -> str:
        """Display member status details"""
        response = f"Member Details:\n\n"
        response += f"Name: {member.first_name} {member.last_name}\n"
        response += f"Number: {member.membership_number}\n"
        response += f"Status: {member.membership_status.upper()}\n"
        response += f"Location: {member.constituency}\n"

        if member.membership_status == "pending":
            response += f"\nPayment pending: K25\n"
            response += f"Pay via *303# (MTN)"

        return response

    # ==================== PAYMENT FLOW ====================

    def handle_payment(self, session: USSDSession, user_input: str, phone_number: str, db: Session) -> Tuple[str, bool]:
        """Handle payment flow"""
        session_data = session.session_data or {}

        if session.current_step == "payment_membership_number":
            member = db.query(Member).filter(Member.membership_number == user_input).first()

            if not member:
                return f"Member {user_input} not found.\n\nPlease check your number.", True

            # Store member ID in session
            session_data["payment_member_id"] = str(member.id)
            session_data["payment_member_number"] = member.membership_number
            session.session_data = session_data

            # Check if member has PIN
            if member.ussd_pin_hash:
                session.current_step = "payment_verify_pin"
                db.commit()
                return "Enter your PIN:", False
            else:
                # No PIN, proceed to payment year selection
                session.current_step = "payment_year"
                db.commit()

                current_year = datetime.now().year
                response = f"Payment for: {member.first_name} {member.last_name}\n\n"
                response += f"Select payment year:\n"
                response += f"1. {current_year}\n"
                response += f"2. {current_year + 1}\n"
                response += f"0. Cancel"

                return response, False

        elif session.current_step == "payment_verify_pin":
            member_id = session_data.get("payment_member_id")
            member = db.query(Member).filter(Member.id == int(member_id)).first()

            if not member:
                return "Session error. Please try again.", True

            # Verify PIN
            verified, error_msg = self.verify_member_pin(member, user_input, db)

            if not verified:
                return error_msg, True

            # PIN verified, proceed to payment year
            session.current_step = "payment_year"
            db.commit()

            current_year = datetime.now().year
            response = f"Payment for: {member.first_name} {member.last_name}\n\n"
            response += f"Select payment year:\n"
            response += f"1. {current_year}\n"
            response += f"2. {current_year + 1}\n"
            response += f"0. Cancel"

            return response, False

        elif session.current_step == "payment_year":
            current_year = datetime.now().year

            if user_input == "0":
                return "Payment cancelled.", True
            elif user_input == "1":
                payment_year = current_year
            elif user_input == "2":
                payment_year = current_year + 1
            else:
                return "Invalid choice.\n1. This year\n2. Next year\n0. Cancel", False

            session_data = session.session_data or {}
            session_data["payment_year"] = payment_year
            session.session_data = session_data
            session.current_step = "payment_method"
            db.commit()

            response = f"Payment year: {payment_year}\n"
            response += f"Amount: K25.00\n\n"
            response += f"Select payment method:\n"
            response += f"1. Mobile Money (MTN)\n"
            response += f"2. Mobile Money (Airtel)\n"
            response += f"3. Bank Transfer\n"
            response += f"0. Cancel"

            return response, False

        elif session.current_step == "payment_method":
            if user_input == "0":
                return "Payment cancelled.", True

            session_data = session.session_data or {}
            member_id = session_data.get("payment_member_id")
            member_number = session_data.get("payment_member_number")
            payment_year = session_data.get("payment_year")

            if user_input == "1":
                response = f"Mobile Money Payment\n\n"
                response += f"Membership: {member_number}\n"
                response += f"Year: {payment_year}\n"
                response += f"Amount: K25.00\n\n"
                response += f"Dial *303# on MTN\n"
                response += f"Or call 388 for help\n\n"
                response += f"Thank you!"
            elif user_input == "2":
                response = f"Mobile Money Payment\n\n"
                response += f"Membership: {member_number}\n"
                response += f"Year: {payment_year}\n"
                response += f"Amount: K25.00\n\n"
                response += f"Dial *115# on Airtel\n"
                response += f"Or call 388 for help\n\n"
                response += f"Thank you!"
            elif user_input == "3":
                response = f"Bank Transfer\n\n"
                response += f"Bank: [Bank Name]\n"
                response += f"Account: [Account Number]\n"
                response += f"Reference: {member_number}\n\n"
                response += f"Visit addzambia.com for details"
            else:
                return "Invalid choice.", True

            return response, True

        return "Payment processing error.", True

    # ==================== UPDATE INFORMATION FLOW ====================

    def handle_update_info(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle information update flow"""
        step = session.current_step
        session_data = session.session_data or {}

        if step == "update_menu":
            # Handle update menu choice
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            if user_input == "0":
                return "Update cancelled.", True

            elif user_input == "1":
                # Update phone number
                session.current_step = "update_phone_new"
                db.commit()
                response = "Update Phone Number\n\n"
                response += f"Current: {member.phone_number}\n\n"
                response += "Enter new phone number:\n(Format: 0971234567)"
                return response, False

            elif user_input == "2":
                # Update address
                session.current_step = "update_address"
                db.commit()
                response = "Update Address\n\n"
                response += f"Current location:\n{member.physical_address}\n\n"
                response += "Enter your new address:"
                return response, False

            else:
                response = "Invalid choice.\n\n"
                response += "What would you like to update?\n\n"
                response += "1. Phone number\n"
                response += "2. Address\n"
                response += "0. Cancel"
                return response, False

        elif step == "update_phone_new":
            # Validate and update phone number
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            # Clean phone number
            clean_phone = ''.join(c for c in user_input if c.isdigit())

            # Normalize to 260 format
            if clean_phone.startswith('0'):
                clean_phone = '260' + clean_phone[1:]
            elif not clean_phone.startswith('260'):
                clean_phone = '260' + clean_phone

            # Validate length (should be 12 digits: 260 + 9 digits)
            if len(clean_phone) != 12:
                return "Invalid phone number.\nEnter phone number:\n(Format: 0971234567)", False

            # Check if phone number is already registered to another member
            existing = db.query(Member).filter(
                Member.phone_number == clean_phone,
                Member.id != member_id
            ).first()

            if existing:
                return "Phone number already registered to another member.\nPlease try a different number.", True

            # Confirm update
            session_data["new_phone"] = clean_phone
            session.session_data = session_data
            session.current_step = "update_phone_confirm"
            db.commit()

            response = f"Confirm phone number update:\n\n"
            response += f"Old: {member.phone_number}\n"
            response += f"New: {clean_phone}\n\n"
            response += "1. Confirm\n"
            response += "0. Cancel"

            return response, False

        elif step == "update_phone_confirm":
            # Confirm and save phone number
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            if user_input == "1":
                # Confirm update
                new_phone = session_data.get("new_phone")
                old_phone = member.phone_number

                member.phone_number = new_phone
                db.commit()

                logger.info(f"[USSD] Phone number updated for member {member.membership_number}: {old_phone} -> {new_phone}")

                return f"Phone number updated successfully!\n\nNew number: {new_phone}\n\nThank you!", True

            elif user_input == "0":
                return "Update cancelled.", True

            else:
                return "Invalid choice.\n1. Confirm\n0. Cancel", False

        elif step == "update_address":
            # Update physical address
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            if len(user_input) < 5:
                return "Address too short.\nPlease enter a valid address:", False

            # Confirm update
            session_data["new_address"] = user_input
            session.session_data = session_data
            session.current_step = "update_address_confirm"
            db.commit()

            response = f"Confirm address update:\n\n"
            response += f"New address:\n{user_input}\n\n"
            response += "1. Confirm\n"
            response += "0. Cancel"

            return response, False

        elif step == "update_address_confirm":
            # Confirm and save address
            member_id = session_data.get("member_id")
            member = db.query(Member).filter(Member.id == member_id).first()

            if not member:
                return "Session error. Please try again.", True

            if user_input == "1":
                # Confirm update - retrieve new_address from session data
                new_address = session_data.get("new_address")

                # Debug logging
                logger.info(f"[USSD] Address update confirmation - session_data: {session_data}")
                logger.info(f"[USSD] Address update confirmation - new_address: {new_address}")

                if not new_address:
                    logger.error(f"[USSD] Address update failed - new_address is None in session_data")
                    return "Error: Address data lost. Please try again.", True

                old_address = member.physical_address
                member.physical_address = new_address
                db.commit()

                logger.info(f"[USSD] Address updated for member {member.membership_number}: '{old_address}' -> '{new_address}'")

                return f"Address updated successfully!\n\nThank you!", True

            elif user_input == "0":
                return "Update cancelled.", True

            else:
                return "Invalid choice.\n1. Confirm\n0. Cancel", False

        return "Update error. Please try again.", True

    # ==================== GEOGRAPHY HELPERS ====================

    def get_provinces(self, db: Session) -> list:
        """Fetch provinces from database"""
        try:
            provinces = db.query(Province).order_by(Province.province_name).all()
            return [{"id": str(p.id), "province_name": p.province_name} for p in provinces]
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
            menu += f"{idx}. {province['province_name']}\n"
        return menu

    def get_districts(self, province_id: str, db: Session) -> list:
        """Fetch districts for a province from database"""
        try:
            districts = db.query(District).filter(
                District.province_id == province_id
            ).order_by(District.district_name).all()
            return [{"id": str(d.id), "district_name": d.district_name} for d in districts]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching districts: {e}")
            return []

    def get_districts_menu(self, province_id: str, db: Session) -> str:
        """Get formatted districts menu"""
        districts = self.get_districts(province_id, db)
        if not districts:
            return "Error loading districts"

        menu = ""
        for idx, district in enumerate(districts[:10], 1):
            menu += f"{idx}. {district['district_name']}\n"
        return menu

    def get_constituencies(self, district_id: str, db: Session) -> list:
        """Fetch constituencies for a district from database"""
        try:
            constituencies = db.query(Constituency).filter(
                Constituency.district_id == district_id
            ).order_by(Constituency.constituency_name).all()
            return [{"id": str(c.id), "constituency_name": c.constituency_name} for c in constituencies]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching constituencies: {e}")
            return []

    def get_constituencies_menu(self, district_id: str, db: Session) -> str:
        """Get formatted constituencies menu"""
        constituencies = self.get_constituencies(district_id, db)
        if not constituencies:
            return "Error loading constituencies"

        menu = ""
        for idx, constituency in enumerate(constituencies[:10], 1):
            menu += f"{idx}. {constituency['constituency_name']}\n"
        return menu

    def get_wards(self, constituency_id: str, db: Session) -> list:
        """Fetch wards for a constituency from database"""
        try:
            wards = db.query(Ward).filter(
                Ward.constituency_id == constituency_id
            ).order_by(Ward.ward_name).all()
            return [{"id": str(w.id), "ward_name": w.ward_name} for w in wards]
        except Exception as e:
            logger.error(f"[USSD] Database error fetching wards: {e}")
            return []

    def get_wards_menu(self, constituency_id: str, db: Session) -> str:
        """Get formatted wards menu"""
        wards = self.get_wards(constituency_id, db)
        if not wards:
            return "Error loading wards"

        menu = ""
        for idx, ward in enumerate(wards[:10], 1):
            menu += f"{idx}. {ward['ward_name']}\n"
        return menu

    # ==================== AUTHENTICATION HANDLERS ====================

    def handle_auth_verify_pin(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle PIN verification at login"""
        session_data = session.session_data or {}
        member_id = session_data.get("member_id")
        member = db.query(Member).filter(Member.id == member_id).first()

        if not member:
            return "Session error. Please try again.", True

        # Verify PIN
        verified, error_msg = self.verify_member_pin(member, user_input, db)

        if not verified:
            return error_msg, True

        # PIN verified - show main menu
        return self.show_main_menu(session, db)

    def handle_auth_create_pin(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle PIN creation at first login"""
        # Validate PIN format
        if not user_input.isdigit() or len(user_input) != 4:
            return "PIN must be 4 digits.\nPlease enter a 4-digit PIN:\n(Example: 1234)", False

        # Store PIN temporarily
        session_data = session.session_data or {}
        session_data["new_pin"] = user_input
        session.session_data = session_data
        session.current_step = "auth_confirm_pin"
        db.commit()

        return "Confirm your PIN:\nRe-enter the 4-digit PIN:", False

    def handle_auth_confirm_pin(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle PIN confirmation at first login"""
        session_data = session.session_data or {}
        new_pin = session_data.get("new_pin")

        if user_input != new_pin:
            return "PINs do not match.\n\nPlease dial *388*3# again to try.", True

        # Save PIN
        member_id = session_data.get("member_id")
        member = db.query(Member).filter(Member.id == member_id).first()

        if not member:
            return "Session error. Please try again.", True

        member.ussd_pin_hash = self.hash_pin(new_pin)
        member.pin_attempts = 0
        member.pin_locked_until = None
        db.commit()

        logger.info(f"[USSD] PIN created for member {member.membership_number} at first login")

        # Show success message and go to main menu
        session.current_step = "main_menu"
        db.commit()

        response = f"PIN created successfully!\n\n"
        response += self.show_main_menu(session, db)[0]

        return response, False

    # ==================== PIN MANAGEMENT ====================

    def handle_pin_setup(self, session: USSDSession, user_input: str, db: Session) -> Tuple[str, bool]:
        """Handle PIN setup/change flow"""
        step = session.current_step
        session_data = session.session_data or {}

        if step == "pin_membership_number":
            # Verify membership number
            member = db.query(Member).filter(Member.membership_number == user_input).first()

            if not member:
                return f"Member {user_input} not found.\n\nPlease check your number.", True

            # Check if member already has PIN
            session_data["pin_member_id"] = str(member.id)
            session_data["has_pin"] = member.ussd_pin_hash is not None
            session.session_data = session_data

            if member.ussd_pin_hash:
                # Ask for old PIN first
                session.current_step = "pin_verify_old"
                db.commit()
                return "Enter your current PIN:", False
            else:
                # No PIN set, go directly to new PIN
                session.current_step = "pin_enter_new"
                db.commit()
                return "Create a 4-digit PIN:\n(Example: 1234)", False

        elif step == "pin_verify_old":
            # Verify old PIN before allowing change
            member_id = session_data.get("pin_member_id")
            member = db.query(Member).filter(Member.id == int(member_id)).first()

            if not member:
                return "Session error. Please try again.", True

            # Check if account is locked
            if member.pin_locked_until and member.pin_locked_until > datetime.utcnow():
                time_left = (member.pin_locked_until - datetime.utcnow()).seconds // 60
                return f"Account locked.\nTry again in {time_left} minutes.", True

            # Verify PIN
            if not self.verify_pin(user_input, member.ussd_pin_hash):
                member.pin_attempts = (member.pin_attempts or 0) + 1

                # Lock after 3 failed attempts
                if member.pin_attempts >= 3:
                    member.pin_locked_until = datetime.utcnow() + timedelta(minutes=30)
                    db.commit()
                    return "Too many failed attempts.\nAccount locked for 30 minutes.", True

                db.commit()
                attempts_left = 3 - member.pin_attempts
                return f"Incorrect PIN.\n{attempts_left} attempts remaining.", False

            # PIN verified, reset attempts
            member.pin_attempts = 0
            member.pin_locked_until = None
            db.commit()

            session.current_step = "pin_enter_new"
            db.commit()
            return "Enter your new 4-digit PIN:\n(Example: 1234)", False

        elif step == "pin_enter_new":
            # Validate PIN format
            if not user_input.isdigit() or len(user_input) != 4:
                return "PIN must be 4 digits.\nEnter your PIN:\n(Example: 1234)", False

            # Store new PIN temporarily
            session_data["new_pin"] = user_input
            session.session_data = session_data
            session.current_step = "pin_confirm"
            db.commit()

            return "Confirm your PIN:\nRe-enter the 4-digit PIN:", False

        elif step == "pin_confirm":
            # Confirm PIN matches
            new_pin = session_data.get("new_pin")

            if user_input != new_pin:
                return "PINs do not match.\n\nPlease try again from the start.", True

            # Hash and save PIN
            member_id = session_data.get("pin_member_id")
            member = db.query(Member).filter(Member.id == int(member_id)).first()

            if not member:
                return "Session error. Please try again.", True

            member.ussd_pin_hash = self.hash_pin(new_pin)
            member.pin_attempts = 0
            member.pin_locked_until = None
            db.commit()

            logger.info(f"[USSD] PIN set for member {member.membership_number}")

            was_change = session_data.get("has_pin", False)
            action = "changed" if was_change else "created"

            return f"PIN {action} successfully!\n\nYour account is now secure.\n\nThank you!", True

        return "PIN setup error. Please try again.", True

    def hash_pin(self, pin: str) -> str:
        """Hash PIN using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pin.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify PIN against hash"""
        try:
            return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
        except:
            return False

    def check_pin_lock(self, member: Member, db: Session) -> Tuple[bool, str]:
        """Check if member account is locked due to failed PIN attempts"""
        if member.pin_locked_until and member.pin_locked_until > datetime.utcnow():
            time_left = (member.pin_locked_until - datetime.utcnow()).seconds // 60
            return True, f"Account locked.\nTry again in {time_left} minutes."

        # Clear lock if time has passed
        if member.pin_locked_until and member.pin_locked_until <= datetime.utcnow():
            member.pin_locked_until = None
            member.pin_attempts = 0
            db.commit()

        return False, ""

    def verify_member_pin(self, member: Member, pin: str, db: Session) -> Tuple[bool, str]:
        """Verify member PIN with lockout mechanism"""
        # Check if locked
        is_locked, lock_msg = self.check_pin_lock(member, db)
        if is_locked:
            return False, lock_msg

        # Verify PIN
        if not member.ussd_pin_hash:
            return False, "No PIN set.\nPlease set a PIN first."

        if not self.verify_pin(pin, member.ussd_pin_hash):
            member.pin_attempts = (member.pin_attempts or 0) + 1

            if member.pin_attempts >= 3:
                member.pin_locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.commit()
                return False, "Too many failed attempts.\nAccount locked for 30 minutes."

            db.commit()
            attempts_left = 3 - member.pin_attempts
            return False, f"Incorrect PIN.\n{attempts_left} attempts remaining."

        # PIN verified, reset attempts
        member.pin_attempts = 0
        member.pin_locked_until = None
        db.commit()

        return True, ""


# Create global instance
ussd_service = USSDService()
