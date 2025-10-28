from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import jwt
import datetime
import re
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Backend API URL - Use environment variable or default to backend service
API_URL = os.environ.get('API_URL', 'http://backend:8000') + "/api"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # Can be email, phone, or membership_number
        password = request.form.get('password')

        # Validate input
        if not identifier or not password:
            flash('Please provide login credentials.', 'danger')
            return redirect(url_for('auth.login'))

        # Determine login type
        login_data = {'password': password}
        if '@' in identifier:
            login_data['email'] = identifier
        elif identifier.startswith('PM'):
            login_data['membership_number'] = identifier
        else:
            login_data['phone'] = identifier

        try:
            # Call backend API for authentication
            response = requests.post(
                f"{API_URL}/auth/login",
                json={'username': identifier, 'password': password},
                timeout=10
            )

            if response.status_code == 200:
                # Login successful, get token and user data
                token_data = response.json()
                access_token = token_data.get('access_token')

                # Fetch user profile using the token
                profile_response = requests.get(
                    f"{API_URL}/members/me/profile",
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10
                )

                if profile_response.status_code == 200:
                    member_data = profile_response.json()

                    # Create session
                    session['user_token'] = access_token
                    session['user_id'] = member_data.get('id')
                    session['user_name'] = f"{member_data.get('first_name', '')} {member_data.get('last_name', '')}".strip()
                    session['user_role'] = 'admin' if member_data.get('is_admin') else 'member'
                    session['membership_number'] = member_data.get('membership_number')
                    session['nrc'] = member_data.get('national_id')
                    session['phone'] = member_data.get('phone_number')
                    session['email'] = member_data.get('email')
                    session['first_name'] = member_data.get('first_name')
                    session['last_name'] = member_data.get('last_name')
                    session['constituency'] = member_data.get('constituency')
                    session['ward'] = member_data.get('ward')
                    session['branch'] = member_data.get('branch')
                    session['address'] = member_data.get('physical_address')
                    session['date_of_birth'] = str(member_data.get('date_of_birth')) if member_data.get('date_of_birth') else None
                    session['gender'] = member_data.get('gender')
                    session['occupation'] = member_data.get('occupation')
                    session['education_level'] = member_data.get('education_level')
                    session['membership_status'] = member_data.get('membership_status')

                    flash(f'Welcome back, {session["user_name"]}!', 'success')

                    # Redirect based on role
                    if session['user_role'] == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    else:
                        return redirect(url_for('member.dashboard'))
                else:
                    flash('Failed to fetch user profile. Please try again.', 'danger')
            elif response.status_code == 401:
                flash('Invalid credentials. Please check your login details and PIN.', 'danger')
            else:
                flash('Login service unavailable. Please try again later.', 'danger')

        except requests.exceptions.ConnectionError:
            flash('Unable to connect to authentication service. Please try again later.', 'danger')
            print(f"Connection error: API URL {API_URL}")
        except requests.exceptions.Timeout:
            flash('Login request timed out. Please try again.', 'danger')
        except Exception as e:
            flash('Login error. Please try again.', 'danger')
            print(f"Login error: {e}")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form data
        form_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'date_of_birth': request.form.get('date_of_birth'),
            'gender': request.form.get('gender'),
            'national_id': request.form.get('nrc_number'),
            'phone_number': request.form.get('phone'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'physical_address': request.form.get('address'),
            'occupation': request.form.get('occupation'),
            'education_level': request.form.get('education_level'),
            'registration_channel': 'web',
            'membership_type': 'ordinary'
        }

        # Set default values for required fields if not provided
        if not form_data.get('physical_address'):
            form_data['physical_address'] = 'Not Provided'

        # Fetch constituency and ward names from geography API
        try:
            if request.form.get('constituency_id'):
                resp = requests.get(f"{API_URL}/geography/constituencies/{request.form.get('constituency_id')}", timeout=5)
                if resp.status_code == 200:
                    constituency_data = resp.json()
                    form_data['constituency'] = constituency_data.get('constituency_name', 'Unknown')

            if request.form.get('ward_id'):
                resp = requests.get(f"{API_URL}/geography/wards/{request.form.get('ward_id')}", timeout=5)
                if resp.status_code == 200:
                    ward_data = resp.json()
                    form_data['ward'] = ward_data.get('ward_name', 'Unknown')
                    form_data['branch'] = ward_data.get('ward_name', 'Main')
        except Exception as e:
            print(f"Error fetching location data: {e}")

        # Ensure required location fields have defaults
        if not form_data.get('constituency'):
            form_data['constituency'] = 'Unknown'
        if not form_data.get('ward'):
            form_data['ward'] = 'Unknown'
        if not form_data.get('branch'):
            form_data['branch'] = 'Main'

        # Validate required fields
        required = ['first_name', 'last_name', 'national_id', 'phone_number', 'password']
        missing = [field for field in required if not form_data.get(field)]

        if missing:
            flash(f'Missing required fields: {", ".join(missing)}', 'danger')
            return redirect(url_for('auth.register'))

        # Validate NRC format
        nrc_pattern = r'^\d{6}/\d{2}/\d$'
        if not re.match(nrc_pattern, form_data['national_id']):
            flash('Invalid NRC format. Use format: 123456/78/9', 'danger')
            return redirect(url_for('auth.register'))

        # Validate PIN
        if not form_data['password'] or len(form_data['password']) != 4 or not form_data['password'].isdigit():
            flash('PIN must be exactly 4 digits.', 'danger')
            return redirect(url_for('auth.register'))

        confirm_password = request.form.get('confirm_password')
        if form_data['password'] != confirm_password:
            flash('PINs do not match.', 'danger')
            return redirect(url_for('auth.register'))

        try:
            # Register via backend API
            response = requests.post(
                f"{API_URL}/auth/register",
                json=form_data,
                timeout=10
            )

            if response.status_code == 200:
                member_data = response.json()
                flash(f'Registration successful! Your membership number is {member_data.get("membership_number")}', 'success')
                flash('Please login with your credentials to access your dashboard.', 'info')
                return redirect(url_for('auth.login'))
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Registration failed')
                flash(error_detail, 'danger')
            elif response.status_code == 422:
                # Validation error - show field details
                try:
                    error_data = response.json()
                    if 'detail' in error_data and isinstance(error_data['detail'], list):
                        for error in error_data['detail']:
                            field = error.get('loc', ['unknown'])[-1]
                            msg = error.get('msg', 'Invalid value')
                            flash(f'{field}: {msg}', 'danger')
                    else:
                        flash(error_data.get('detail', 'Validation failed'), 'danger')
                except:
                    flash('Registration validation failed. Please check all required fields.', 'danger')
            else:
                flash('Registration service unavailable. Please try again later.', 'danger')

        except requests.exceptions.ConnectionError:
            flash('Unable to connect to registration service. Please try again later.', 'danger')
        except requests.exceptions.Timeout:
            flash('Registration request timed out. Please try again.', 'danger')
        except Exception as e:
            flash('Registration error. Please try again.', 'danger')
            print(f"Registration error: {e}")

    # Load provinces for dropdown
    provinces = []
    try:
        response = requests.get(f"{API_URL}/geography/provinces", timeout=5)
        if response.status_code == 200:
            provinces = response.json()
    except:
        pass

    return render_template('auth/register.html', provinces=provinces)

@auth_bp.route('/register/lite', methods=['GET', 'POST'])
def register_lite():
    """Lite KYC registration - quick signup"""
    if request.method == 'POST':
        # Collect lite form data
        form_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'gender': request.form.get('gender'),
            'phone_number': request.form.get('phone'),
            'email': request.form.get('email'),
            'password': request.form.get('pin'),
            'registration_channel': 'web',
            'membership_type': 'lite',
            'national_id': f"LITE{request.form.get('phone', '000000')}",  # Temporary NRC for lite
            'physical_address': 'Not Provided',
            'constituency': 'Unknown',
            'ward': 'Unknown',
            'branch': 'Main'
        }

        # Calculate date of birth from age
        age = request.form.get('age')
        if age:
            try:
                birth_year = datetime.datetime.now().year - int(age)
                form_data['date_of_birth'] = f"{birth_year}-01-01"
            except:
                form_data['date_of_birth'] = "1990-01-01"

        # Fetch location names
        try:
            if request.form.get('constituency_id'):
                resp = requests.get(f"{API_URL}/geography/constituencies/{request.form.get('constituency_id')}", timeout=5)
                if resp.status_code == 200:
                    constituency_data = resp.json()
                    form_data['constituency'] = constituency_data.get('constituency_name', 'Unknown')

            if request.form.get('ward_id'):
                resp = requests.get(f"{API_URL}/geography/wards/{request.form.get('ward_id')}", timeout=5)
                if resp.status_code == 200:
                    ward_data = resp.json()
                    form_data['ward'] = ward_data.get('ward_name', 'Unknown')
        except Exception as e:
            print(f"Error fetching location data: {e}")

        # Validate required fields
        required = ['first_name', 'last_name', 'gender', 'phone_number', 'password']
        missing = [field for field in required if not form_data.get(field)]

        if missing:
            flash(f'Please fill in all required fields.', 'danger')
            return redirect(url_for('auth.register_lite'))

        # Validate PIN
        if not form_data['password'] or len(form_data['password']) != 4 or not form_data['password'].isdigit():
            flash('Invalid PIN. Please enter a 4-digit number.', 'danger')
            return redirect(url_for('auth.register_lite'))

        try:
            # Register via backend API
            response = requests.post(
                f"{API_URL}/auth/register",
                json=form_data,
                timeout=10
            )

            if response.status_code == 200:
                member_data = response.json()
                flash(f'Lite registration successful! Your membership number is {member_data.get("membership_number")}', 'success')
                flash('You can upgrade to full membership anytime to access more features.', 'info')
                return redirect(url_for('auth.login'))
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Registration failed')
                flash(error_detail, 'danger')
            else:
                flash('Registration service unavailable. Please try again later.', 'danger')

        except requests.exceptions.ConnectionError:
            flash('Unable to connect to registration service. Please try again later.', 'danger')
        except requests.exceptions.Timeout:
            flash('Registration request timed out. Please try again.', 'danger')
        except Exception as e:
            flash('Registration error. Please try again.', 'danger')
            print(f"Lite registration error: {e}")

    return render_template('auth/register_lite.html')

@auth_bp.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('public.index'))

# Forgot password and reset routes removed - implement when backend supports it

# AJAX endpoints for dynamic form data
@auth_bp.route('/api/provinces')
def get_provinces():
    try:
        response = requests.get(f"{API_URL}/geography/provinces")
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass
    return jsonify([])

@auth_bp.route('/api/districts/<int:province_id>')
def get_districts(province_id):
    try:
        response = requests.get(f"{API_URL}/geography/provinces/{province_id}/districts")
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass
    return jsonify([])

@auth_bp.route('/api/constituencies/<int:district_id>')
def get_constituencies(district_id):
    try:
        response = requests.get(f"{API_URL}/geography/districts/{district_id}/constituencies")
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass
    return jsonify([])

@auth_bp.route('/api/wards/<int:constituency_id>')
def get_wards(constituency_id):
    try:
        response = requests.get(f"{API_URL}/geography/constituencies/{constituency_id}/wards")
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass
    return jsonify([])