"""
Authentication routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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

        # Demo users (in production, use proper auth with database)
        demo_users = {
            # Admin users
            'admin@add.org.zm': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},
            'ADD00001': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},
            '0977000001': {'pin': '1234', 'name': 'Admin User', 'role': 'admin', 'id': 1},

            'charles@ontech.co.zm': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 4},
            'ADD00004': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 4},
            '0977123400': {'pin': '9852', 'name': 'Charles Mwansa', 'role': 'admin', 'id': 4},

            # Regular members
            'ADD12345': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},
            '0977123456': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},
            'john.banda@email.com': {'pin': '5678', 'name': 'John Banda', 'role': 'member', 'id': 2},

            'ADD67890': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
            '0966987654': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
            'mary.mwansa@email.com': {'pin': '9999', 'name': 'Mary Mwansa', 'role': 'member', 'id': 3},
        }

        # Check if identifier exists and PIN matches
        if identifier in demo_users:
            user = demo_users[identifier]
            if password == user['pin']:
                session['user_token'] = 'demo-token'
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_role'] = user['role']
                flash(f"Welcome back, {user['name']}!", 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid PIN. Please try again.', 'danger')
        else:
            flash('Member not found. Please check your identifier or register.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle registration
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.index'))
