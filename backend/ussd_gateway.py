#!/usr/bin/env python3
"""
USSD Gateway Service for Political Party Membership System
Following BYouth USSD flow structure for ADD membership
Compatible with standard USSD gateways using sessionId, msisdn, text format
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import os
import re
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
USSD_CODE = "*388*3#"  # ADD membership USSD code
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:57021')
SESSION_TIMEOUT = 180  # 3 minutes

# In-memory session storage
sessions = {}

# ============= ZAMBIAN DATA =============

ZAMBIAN_PROVINCES = {
    '1': {'name': 'Central', 'districts': ['Kabwe', 'Mumbwa', 'Chibombo', 'Kapiri Mposhi', 'Serenje', 'Mkushi']},
    '2': {'name': 'Copperbelt', 'districts': ['Ndola', 'Kitwe', 'Chingola', 'Mufulira', 'Luanshya', 'Chililabombwe']},
    '3': {'name': 'Eastern', 'districts': ['Chipata', 'Petauke', 'Katete', 'Lundazi', 'Nyimba', 'Chadiza']},
    '4': {'name': 'Luapula', 'districts': ['Mansa', 'Samfya', 'Kawambwa', 'Nchelenge', 'Mwense', 'Chipili']},
    '5': {'name': 'Lusaka', 'districts': ['Lusaka', 'Kafue', 'Chongwe', 'Luangwa', 'Chilanga', 'Rufunsa']},
    '6': {'name': 'Northern', 'districts': ['Kasama', 'Mbala', 'Mpika', 'Chinsali', 'Luwingu', 'Mungwi']},
    '7': {'name': 'North-Western', 'districts': ['Solwezi', 'Kasempa', 'Zambezi', 'Mwinilunga', 'Chavuma', 'Kabompo']},
    '8': {'name': 'Southern', 'districts': ['Livingstone', 'Choma', 'Monze', 'Mazabuka', 'Kalomo', 'Namwala']},
    '9': {'name': 'Western', 'districts': ['Mongu', 'Senanga', 'Kaoma', 'Sesheke', 'Lukulu', 'Kalabo']},
    '10': {'name': 'Muchinga', 'districts': ['Chama', 'Isoka', 'Nakonde', 'Mafinga', 'Mpika', 'Shiwangandu']}
}

LANGUAGES = {
    '1': 'English',
    '2': 'Bemba',
    '3': 'Nyanja',
    '4': 'Tonga',
    '5': 'Lozi',
    '6': 'Kaonde',
    '7': 'Lunda',
    '8': 'Luvale'
}

MEMBERSHIP_TYPES = {
    '1': 'Regular Member',
    '2': 'Youth Wing',
    '3': 'Women\'s League',
    '4': 'Student Member',
    '5': 'Diaspora Member'
}

# ============= SESSION MANAGEMENT =============

class USSDSession:
    """Manages USSD session data"""

    def __init__(self, session_id: str, msisdn: str):
        self.session_id = session_id
        self.msisdn = msisdn
        self.state = 'start'
        self.data = {}
        self.registration_data = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.language = 'en'

    def update_activity(self):
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        return (datetime.now() - self.last_activity).seconds > SESSION_TIMEOUT

    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'msisdn': self.msisdn,
            'state': self.state,
            'data': self.data,
            'registration_data': self.registration_data,
            'language': self.language
        }

def get_session(session_id: str) -> Optional[USSDSession]:
    """Get session or None if expired"""
    if session_id in sessions:
        session = sessions[session_id]
        if session.is_expired():
            del sessions[session_id]
            return None
        session.update_activity()
        return session
    return None

def create_session(session_id: str, msisdn: str) -> USSDSession:
    """Create new session"""
    session = USSDSession(session_id, msisdn)
    sessions[session_id] = session
    logger.info(f"Created session: {session_id} for {msisdn}")
    return session

def update_session(session_id: str, state: str = None, data: Dict = None):
    """Update session state and data"""
    session = get_session(session_id)
    if session:
        if state:
            session.state = state
        if data:
            session.data.update(data)
        logger.info(f"Updated session {session_id}: state={state}")

def delete_session(session_id: str):
    """Delete session"""
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"Deleted session: {session_id}")

# ============= USSD HANDLERS =============

def format_phone_number(msisdn: str) -> str:
    """Format phone number to standard format"""
    clean = ''.join(filter(str.isdigit, str(msisdn)))

    if clean.startswith('260') and len(clean) == 12:
        return '+' + clean
    elif clean.startswith('0') and len(clean) == 10:
        return '+260' + clean[1:]
    elif len(clean) == 9:
        return '+260' + clean
    else:
        if not clean.startswith('260'):
            return '+260' + clean
        return '+' + clean

def check_member_exists(phone: str) -> Dict:
    """Check if member exists in backend"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/members/check",
            params={'phone': phone},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {'exists': False}
    except Exception as e:
        logger.error(f"Backend check failed: {e}")
        return {'exists': False}

def start_welcome(session_id: str) -> str:
    """Show initial welcome with terms"""
    update_session(session_id, state='terms')

    # Ultra-compact terms under 140 characters - BYouth style
    terms = "Welcome to ADD!\n"
    terms += "Alliance for Democracy\n"
    terms += "& Development\n"
    terms += "UPND Partner\n"
    terms += "K50/year membership\n"
    terms += "1. Accept\n"
    terms += "2. Decline"

    return terms

def handle_terms(session_id: str, user_input: str) -> tuple:
    """Handle terms acceptance"""
    if user_input == '1':
        update_session(session_id, state='language')
        menu = "Select Language:\n"
        for key, lang in LANGUAGES.items():
            menu += f"{key}. {lang}\n"
        return menu, True
    elif user_input == '2':
        delete_session(session_id)
        return "Registration cancelled.\nThank you!", False
    else:
        return start_welcome(session_id), True

def handle_language(session_id: str, user_input: str) -> tuple:
    """Handle language selection"""
    if user_input in LANGUAGES:
        session = get_session(session_id)
        session.language = LANGUAGES[user_input]
        update_session(session_id, state='first_name')
        return "First name:", True
    else:
        menu = "Invalid. Select Language:\n"
        for key, lang in LANGUAGES.items():
            menu += f"{key}. {lang}\n"
        return menu, True

def handle_first_name(session_id: str, user_input: str) -> tuple:
    """Handle first name input"""
    first_name = user_input.strip()

    if not first_name:
        return "Enter your first name:", True

    # Allow letters, spaces, hyphens, apostrophes
    allowed_chars = first_name.replace(' ', '').replace('-', '').replace("'", '').replace('.', '')
    if not allowed_chars.isalpha():
        return "Letters only please.\nFirst name:", True

    session = get_session(session_id)
    session.registration_data['first_name'] = first_name.title()
    update_session(session_id, state='last_name')

    return f"Hi {first_name.title()}!\nLast name:", True

def handle_last_name(session_id: str, user_input: str) -> tuple:
    """Handle last name input"""
    last_name = user_input.strip()

    if not last_name:
        return "Enter your last name:", True

    allowed_chars = last_name.replace(' ', '').replace('-', '').replace("'", '').replace('.', '')
    if not allowed_chars.isalpha():
        return "Letters only please.\nLast name:", True

    session = get_session(session_id)
    session.registration_data['last_name'] = last_name.title()
    update_session(session_id, state='gender')

    return "Gender:\n1. Male\n2. Female", True

def handle_gender(session_id: str, user_input: str) -> tuple:
    """Handle gender selection"""
    genders = {'1': 'Male', '2': 'Female'}

    if user_input not in genders:
        return "Invalid selection.\nGender:\n1. Male\n2. Female", True

    session = get_session(session_id)
    session.registration_data['gender'] = genders[user_input]
    update_session(session_id, state='nrc')

    return "NRC Number:\n(Format: 123456/12/1)\n(or 0 to skip)", True

def handle_nrc(session_id: str, user_input: str) -> tuple:
    """Handle NRC input"""
    nrc = user_input.strip().upper()

    if nrc != '0' and not re.match(r'^\d{6}/\d{2}/\d$', nrc):
        return "Format: 123456/12/1\nNRC (0=skip):", True

    session = get_session(session_id)
    if nrc != '0':
        session.registration_data['nrc'] = nrc

    update_session(session_id, state='province')

    menu = "Province:\n"
    for key, province in ZAMBIAN_PROVINCES.items():
        if len(key) == 1:
            menu += f"{key}. {province['name']}\n"
    menu += "0. Muchinga"

    return menu, True

def handle_province(session_id: str, user_input: str) -> tuple:
    """Handle province selection"""
    # Map '0' to '10' for Muchinga
    if user_input == '0':
        user_input = '10'

    if user_input not in ZAMBIAN_PROVINCES:
        menu = "Invalid. Select Province:\n"
        for key, province in ZAMBIAN_PROVINCES.items():
            if len(key) == 1:
                menu += f"{key}. {province['name']}\n"
        menu += "0. Muchinga"
        return menu, True

    session = get_session(session_id)
    selected_province = ZAMBIAN_PROVINCES[user_input]
    session.registration_data['province'] = selected_province['name']
    session.data['province_key'] = user_input
    update_session(session_id, state='district')

    menu = f"District in {selected_province['name']}:\n"
    for i, district in enumerate(selected_province['districts'][:6], 1):
        menu += f"{i}. {district}\n"

    return menu, True

def handle_district(session_id: str, user_input: str) -> tuple:
    """Handle district selection"""
    session = get_session(session_id)
    province_key = session.data.get('province_key')
    districts = ZAMBIAN_PROVINCES[province_key]['districts']

    try:
        district_index = int(user_input) - 1
        if 0 <= district_index < len(districts):
            selected_district = districts[district_index]
            session.registration_data['district'] = selected_district
            update_session(session_id, state='constituency')

            return f"Constituency/Ward in {selected_district}:", True
    except (ValueError, IndexError):
        pass

    province = ZAMBIAN_PROVINCES[province_key]
    menu = f"Invalid. District in {province['name']}:\n"
    for i, district in enumerate(districts[:6], 1):
        menu += f"{i}. {district}\n"

    return menu, True

def handle_constituency(session_id: str, user_input: str) -> tuple:
    """Handle constituency input"""
    constituency = user_input.strip()

    if len(constituency) < 2:
        return "Enter constituency/ward:", True

    session = get_session(session_id)
    session.registration_data['constituency'] = constituency
    update_session(session_id, state='membership_type')

    menu = "Membership Type:\n"
    for key, mtype in MEMBERSHIP_TYPES.items():
        menu += f"{key}. {mtype}\n"

    return menu, True

def handle_membership_type(session_id: str, user_input: str) -> tuple:
    """Handle membership type selection"""
    if user_input not in MEMBERSHIP_TYPES:
        menu = "Invalid. Membership Type:\n"
        for key, mtype in MEMBERSHIP_TYPES.items():
            menu += f"{key}. {mtype}\n"
        return menu, True

    session = get_session(session_id)
    session.registration_data['membership_type'] = MEMBERSHIP_TYPES[user_input]
    update_session(session_id, state='pin')

    return "Create 4-digit PIN:", True

def handle_pin(session_id: str, user_input: str) -> tuple:
    """Handle PIN creation"""
    pin = user_input.strip()

    if not re.match(r'^\d{4}$', pin):
        return "4 digits only.\nCreate PIN:", True

    session = get_session(session_id)
    session.registration_data['pin'] = pin
    update_session(session_id, state='pin_confirm')

    return "Confirm PIN:", True

def handle_pin_confirm(session_id: str, user_input: str) -> tuple:
    """Handle PIN confirmation"""
    session = get_session(session_id)
    original_pin = session.registration_data.get('pin')

    if user_input.strip() != original_pin:
        update_session(session_id, state='pin')
        return "PINs don't match.\nCreate 4-digit PIN:", True

    update_session(session_id, state='payment_method')

    return "Payment Method:\n1. Mobile Money\n2. Bank Transfer\n3. Pay Later", True

def handle_payment_method(session_id: str, user_input: str) -> tuple:
    """Handle payment method selection"""
    if user_input == '1':  # Mobile Money
        session = get_session(session_id)
        session.registration_data['payment_method'] = 'mobile_money'
        update_session(session_id, state='mobile_provider')

        return "Select Provider:\n1. MTN\n2. Airtel\n3. Zamtel\n4. Zanaco", True

    elif user_input == '2':  # Bank Transfer
        session = get_session(session_id)
        session.registration_data['payment_method'] = 'bank_transfer'
        update_session(session_id, state='confirm')
        return show_confirmation(session_id), True

    elif user_input == '3':  # Pay Later
        session = get_session(session_id)
        session.registration_data['payment_method'] = 'pay_later'
        update_session(session_id, state='confirm')
        return show_confirmation(session_id), True

    else:
        return "Invalid.\nPayment Method:\n1. Mobile Money\n2. Bank Transfer\n3. Pay Later", True

def handle_mobile_provider(session_id: str, user_input: str) -> tuple:
    """Handle mobile provider selection"""
    providers = {'1': 'MTN', '2': 'Airtel', '3': 'Zamtel', '4': 'Zanaco'}

    if user_input not in providers:
        return "Invalid.\n1. MTN\n2. Airtel\n3. Zamtel\n4. Zanaco", True

    session = get_session(session_id)
    session.registration_data['mobile_provider'] = providers[user_input]
    update_session(session_id, state='mobile_number')

    return "Mobile Money Number:\n(e.g. 0977123456)", True

def handle_mobile_number(session_id: str, user_input: str) -> tuple:
    """Handle mobile money number input"""
    mobile = user_input.strip()

    # Basic validation
    clean = ''.join(filter(str.isdigit, mobile))
    if len(clean) < 9:
        return "Invalid number.\nMobile Money Number:", True

    session = get_session(session_id)
    session.registration_data['mobile_number'] = clean
    update_session(session_id, state='confirm')

    return show_confirmation(session_id), True

def show_confirmation(session_id: str) -> str:
    """Show registration confirmation"""
    session = get_session(session_id)
    reg_data = session.registration_data

    confirm = "Confirm Registration:\n"
    confirm += f"{reg_data.get('first_name', '')} {reg_data.get('last_name', '')}\n"
    confirm += f"NRC: {reg_data.get('nrc', 'Not provided')}\n"
    confirm += f"{reg_data.get('province', '')}\n"
    confirm += f"Type: {reg_data.get('membership_type', '')}\n"
    confirm += "1. Confirm\n"
    confirm += "2. Cancel"

    return confirm

def handle_confirmation(session_id: str, user_input: str) -> tuple:
    """Handle registration confirmation"""
    if user_input == '1':
        session = get_session(session_id)
        reg_data = session.registration_data
        reg_data['phone'] = format_phone_number(session.msisdn)

        # Here you would save to backend
        try:
            # Save to backend
            response = requests.post(
                f"{BACKEND_URL}/api/v1/members/register",
                json=reg_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                member_id = result.get('member_id', 'ADD' + str(datetime.now().timestamp())[:8])
            else:
                member_id = 'ADD' + str(datetime.now().timestamp())[:8]
        except:
            # Generate local member ID if backend fails
            member_id = 'ADD' + str(datetime.now().timestamp())[:8]

        delete_session(session_id)

        success = f"Welcome to ADD!\n"
        success += f"Member ID: {member_id}\n"
        success += f"Thank you for joining\n"
        success += f"the movement!"

        return success, False

    elif user_input == '2':
        delete_session(session_id)
        return "Registration cancelled.\nThank you!", False

    else:
        return show_confirmation(session_id) + "\n1. Confirm\n2. Cancel", True

def process_ussd_request(session_id: str, msisdn: str, user_input: str, is_new: bool) -> Dict:
    """Main USSD request processor"""

    # Clean phone number
    msisdn = format_phone_number(msisdn)

    if is_new:
        # Check if member exists
        member_check = check_member_exists(msisdn)
        if member_check.get('exists'):
            # Member exists - go to login
            session = create_session(session_id, msisdn)
            session.state = 'login_pin'
            return {
                'response': 'Welcome back!\nEnter your PIN:',
                'continue': True
            }
        else:
            # New member - start registration
            session = create_session(session_id, msisdn)
            return {
                'response': start_welcome(session_id),
                'continue': True
            }

    # Get existing session
    session = get_session(session_id)
    if not session:
        # Session expired - restart
        session = create_session(session_id, msisdn)
        return {
            'response': start_welcome(session_id),
            'continue': True
        }

    # Route based on state
    state = session.state
    response_text = ""
    continue_session = True

    if state == 'terms':
        response_text, continue_session = handle_terms(session_id, user_input)
    elif state == 'language':
        response_text, continue_session = handle_language(session_id, user_input)
    elif state == 'first_name':
        response_text, continue_session = handle_first_name(session_id, user_input)
    elif state == 'last_name':
        response_text, continue_session = handle_last_name(session_id, user_input)
    elif state == 'gender':
        response_text, continue_session = handle_gender(session_id, user_input)
    elif state == 'nrc':
        response_text, continue_session = handle_nrc(session_id, user_input)
    elif state == 'province':
        response_text, continue_session = handle_province(session_id, user_input)
    elif state == 'district':
        response_text, continue_session = handle_district(session_id, user_input)
    elif state == 'constituency':
        response_text, continue_session = handle_constituency(session_id, user_input)
    elif state == 'membership_type':
        response_text, continue_session = handle_membership_type(session_id, user_input)
    elif state == 'pin':
        response_text, continue_session = handle_pin(session_id, user_input)
    elif state == 'pin_confirm':
        response_text, continue_session = handle_pin_confirm(session_id, user_input)
    elif state == 'payment_method':
        response_text, continue_session = handle_payment_method(session_id, user_input)
    elif state == 'mobile_provider':
        response_text, continue_session = handle_mobile_provider(session_id, user_input)
    elif state == 'mobile_number':
        response_text, continue_session = handle_mobile_number(session_id, user_input)
    elif state == 'confirm':
        response_text, continue_session = handle_confirmation(session_id, user_input)
    elif state == 'login_pin':
        # Handle existing member login
        if len(user_input) == 4 and user_input.isdigit():
            delete_session(session_id)
            response_text = f"Welcome back!\nServices coming soon.\nThank you!"
            continue_session = False
        else:
            response_text = "Invalid PIN.\nEnter 4-digit PIN:"
            continue_session = True
    else:
        response_text = start_welcome(session_id)
        continue_session = True

    # Ensure response is under 160 characters
    if len(response_text) > 160:
        response_text = response_text[:157] + "..."

    return {
        'response': response_text,
        'continue': continue_session
    }

# ============= API ENDPOINTS =============

@app.route('/ussd', methods=['POST'])
def ussd_handler():
    """Main USSD endpoint - BYouth compatible format"""
    try:
        # Get request data
        data = request.get_json() or request.form.to_dict()

        # Extract parameters - BYouth format
        session_id = data.get('sessionId') or data.get('session_id')
        msisdn = data.get('msisdn') or data.get('phoneNumber') or data.get('phone')
        user_input = data.get('text', '') or data.get('input', '')

        # Check if it's a new session
        is_new = user_input == '' or data.get('is_new_request', False)

        logger.info(f"USSD Request - Session: {session_id}, Phone: {msisdn}, Input: '{user_input}', New: {is_new}")

        # Process request
        result = process_ussd_request(session_id, msisdn, user_input, is_new)

        # Return response in expected format
        response = {
            "response_string": result['response'],
            "continue_session": result['continue'],
            "session_id": session_id
        }

        logger.info(f"USSD Response - Continue: {result['continue']}, Text: {result['response'][:50]}...")

        return jsonify(response)

    except Exception as e:
        logger.error(f"USSD handler error: {e}")
        return jsonify({
            "response_string": "Service error. Please try again.",
            "continue_session": False
        }), 500

@app.route('/ussd/callback', methods=['POST'])
def callback_handler():
    """Callback URL endpoint for notifications"""
    try:
        data = request.get_json()
        logger.info(f"Callback received: {data}")

        # Process callback based on event type
        event_type = data.get('event_type')

        if event_type == 'payment_success':
            # Handle successful payment
            logger.info(f"Payment successful for member: {data.get('member_id')}")
        elif event_type == 'registration_complete':
            # Handle completed registration
            logger.info(f"Registration complete for: {data.get('phone')}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Callback error: {e}")
        return jsonify({"error": "Callback processing failed"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    active_sessions = len(sessions)
    return jsonify({
        "status": "healthy",
        "service": "ADD USSD Gateway",
        "active_sessions": active_sessions,
        "ussd_code": USSD_CODE
    }), 200

@app.route('/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get count of active sessions"""
    # Clean expired sessions
    expired = []
    for sid, session in sessions.items():
        if session.is_expired():
            expired.append(sid)

    for sid in expired:
        del sessions[sid]

    return jsonify({
        "active_sessions": len(sessions),
        "sessions": [s.to_dict() for s in sessions.values()]
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Serve the web-based USSD simulator"""
    return render_template('ussd_simulator.html')

@app.route('/simulator', methods=['GET'])
def simulator():
    """Alternative route for the simulator"""
    return render_template('ussd_simulator.html')

# ============= MAIN =============

if __name__ == '__main__':
    port = int(os.getenv('USSD_PORT', 57023))

    logger.info(f"Starting ADD USSD Gateway on port {port}")
    logger.info(f"USSD Code: {USSD_CODE}")
    logger.info(f"Backend URL: {BACKEND_URL}")

    app.run(host='0.0.0.0', port=port, debug=True)