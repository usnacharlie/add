"""
System Users Management Routes - For admins to create and manage system users
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
def list_users():
    """List all system users"""
    if 'user_token' not in session or session.get('user_role') != 'admin':
        flash('Admin privileges required', 'danger')
        return redirect(url_for('main.dashboard'))

    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/users")
        if response.status_code == 200:
            users = response.json()
        else:
            users = []
            flash('Error loading users', 'error')
    except:
        users = []
        flash('Error connecting to API', 'error')

    return render_template('admin/users/list.html', users=users)


@users_bp.route('/new', methods=['GET', 'POST'])
def new_user():
    """Create a new system user"""
    if 'user_token' not in session or session.get('user_role') != 'admin':
        flash('Admin privileges required', 'danger')
        return redirect(url_for('main.dashboard'))

    api_url = current_app.config['API_BASE_URL']

    if request.method == 'POST':
        user_data = {
            'full_name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone') if request.form.get('phone') else None,
            'pin': request.form.get('pin'),
            'role': request.form.get('role'),
            'member_id': int(request.form.get('member_id')) if request.form.get('member_id') else None
        }

        try:
            response = requests.post(f"{api_url}/users", json=user_data)
            if response.status_code == 201:
                flash(f'System user {user_data["full_name"]} created successfully!', 'success')
                return redirect(url_for('users.list_users'))
            else:
                error_detail = response.json().get('detail', 'Error creating user')
                flash(f'Error: {error_detail}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    # Get members list for linking
    try:
        response = requests.get(f"{api_url}/members/")
        members = response.json() if response.status_code == 200 else []
    except:
        members = []

    return render_template('admin/users/new.html', members=members)


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit a system user"""
    if 'user_token' not in session or session.get('user_role') != 'admin':
        flash('Admin privileges required', 'danger')
        return redirect(url_for('main.dashboard'))

    api_url = current_app.config['API_BASE_URL']

    if request.method == 'POST':
        user_data = {
            'full_name': request.form.get('name'),
            'role': request.form.get('role')
        }

        try:
            response = requests.put(f"{api_url}/users/{user_id}", json=user_data)
            if response.status_code == 200:
                flash('User updated successfully!', 'success')
                return redirect(url_for('users.list_users'))
            else:
                flash('Error updating user', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    # Get user data
    try:
        response = requests.get(f"{api_url}/users/{user_id}")
        if response.status_code == 200:
            user = response.json()
        else:
            flash('User not found', 'error')
            return redirect(url_for('users.list_users'))
    except:
        flash('Error loading user', 'error')
        return redirect(url_for('users.list_users'))

    return render_template('admin/users/edit.html', user=user)
