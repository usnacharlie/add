"""
Authentication routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Demo users (in production, use proper auth with database)
demo_users = {
    # Admin users
    'admin@add.org.zm': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},
    'ADD00001': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},
    '0977000001': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},

    'charles@ontech.co.zm': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 11},
    'ADD00004': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 11},
    '0977123400': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 11},

    # Regular members
    'ADD12345': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},
    '0977123456': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},
    'john.banda@email.com': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},

    'ADD67890': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
    '0966987654': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
    'mary.mwansa@email.com': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
}

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
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier') or request.form.get('username')
        password = request.form.get('password')

        # Call backend API for authentication
        api_url = 'http://localhost:9500/api/v1'
        try:
            response = requests.post(
                f"{api_url}/auth/login",
                json={'identifier': identifier, 'pin': password}
            )

            if response.status_code == 200:
                data = response.json()
                user_data = data['user']

                # Store session data
                session['user_token'] = data['access_token']
                session['user_id'] = user_data['member_id'] if user_data['member_id'] else user_data['id']
                session['user_name'] = user_data['full_name']
                session['user_role'] = user_data['role']
                session['user_email'] = user_data['email']

                flash(f"Welcome back, {user_data['full_name']}!", 'success')
                return redirect(url_for('main.dashboard'))
            elif response.status_code == 401:
                flash('Invalid credentials. Please check your identifier and PIN.', 'danger')
            elif response.status_code == 403:
                flash('Your account is inactive. Please contact an administrator.', 'warning')
            else:
                flash('Login failed. Please try again.', 'danger')

        except requests.exceptions.ConnectionError:
            flash('Cannot connect to authentication server. Please try again later.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from datetime import date
    api_url = 'http://localhost:9500/api/v1'

    if request.method == 'POST':
        # Collect form data
        member_data = {
            'name': request.form.get('name'),
            'gender': request.form.get('gender'),
            'date_of_birth': request.form.get('date_of_birth') if request.form.get('date_of_birth') else None,
            'voters_id': request.form.get('voters_id'),
            'nrc': request.form.get('nrc') if request.form.get('nrc') else None,
            'contact': request.form.get('contact') if request.form.get('contact') else None,
            'ward_id': int(request.form.get('ward_id'))
        }

        try:
            # Create member via API
            response = requests.post(f"{api_url}/members/", json=member_data)

            if response.status_code == 201:
                flash('Registration successful! Member has been created.', 'success')
                return redirect(url_for('members.list_members'))
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Registration failed')
                flash(f'Registration failed: {error_detail}', 'danger')
            else:
                flash('Registration failed. Please try again.', 'danger')

        except requests.exceptions.ConnectionError:
            flash('Cannot connect to server. Please try again later.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    # Fetch all location data for client-side filtering
    try:
        provinces_response = requests.get(f"{api_url}/provinces/")
        provinces = provinces_response.json() if provinces_response.status_code == 200 else []

        districts_response = requests.get(f"{api_url}/districts/")
        districts = districts_response.json() if districts_response.status_code == 200 else []

        constituencies_response = requests.get(f"{api_url}/constituencies/")
        constituencies = constituencies_response.json() if constituencies_response.status_code == 200 else []

        wards_response = requests.get(f"{api_url}/wards/")
        wards = wards_response.json() if wards_response.status_code == 200 else []
    except:
        provinces = []
        districts = []
        constituencies = []
        wards = []

    return render_template('register.html',
        provinces=provinces,
        districts=districts,
        constituencies=constituencies,
        wards=wards,
        today=date.today().isoformat())

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.index'))
