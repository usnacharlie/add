from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import requests
from datetime import datetime, timedelta
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Backend API URL - Use environment variable or default to backend service
API_URL = os.environ.get('API_URL', 'http://backend:8000') + "/api/v1"

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

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'total_members': 0,
        'active_members': 0,
        'new_members_month': 0,
        'total_revenue': 0,
        'pending_approvals': 0,
        'upcoming_events': 0,
        'recent_registrations': [],
        'revenue_chart': [],
        'membership_growth': []
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}

        # Get dashboard statistics
        response = requests.get(f"{API_URL}/admin/dashboard/stats", headers=headers)
        if response.status_code == 200:
            stats.update(response.json())

        # Get recent registrations
        response = requests.get(f"{API_URL}/members?limit=10&sort=created_at_desc", headers=headers)
        if response.status_code == 200:
            stats['recent_registrations'] = response.json().get('members', [])

    except:
        pass

    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/members')
@admin_required
def members():
    members_list = []
    filters = {
        'search': request.args.get('search', ''),
        'status': request.args.get('status', ''),
        'province': request.args.get('province', ''),
        'page': request.args.get('page', 1, type=int),
        'per_page': 20
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members", params=filters, headers=headers)
        if response.status_code == 200:
            data = response.json()
            members_list = data.get('members', [])
            pagination = data.get('pagination', {})
    except:
        pagination = {}

    return render_template('admin/members.html', members=members_list, filters=filters, pagination=pagination)

@admin_bp.route('/members/<int:member_id>')
@admin_required
def member_detail(member_id):
    member = None
    activities = []
    payments = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}

        # Get member details
        response = requests.get(f"{API_URL}/members/{member_id}", headers=headers)
        if response.status_code == 200:
            member = response.json()

        # Get member activities
        response = requests.get(f"{API_URL}/members/{member_id}/activities", headers=headers)
        if response.status_code == 200:
            activities = response.json()

        # Get member payments
        response = requests.get(f"{API_URL}/payments/member/{member_id}", headers=headers)
        if response.status_code == 200:
            payments = response.json()

    except:
        pass

    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_detail.html', member=member, activities=activities, payments=payments)

@admin_bp.route('/members/<int:member_id>/approve', methods=['POST'])
@admin_required
def approve_member(member_id):
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/admin/members/{member_id}/approve", headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Member approved successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to approve member'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/members/<int:member_id>/suspend', methods=['POST'])
@admin_required
def suspend_member(member_id):
    reason = request.json.get('reason', '')

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/admin/members/{member_id}/suspend",
                                json={'reason': reason}, headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Member suspended successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to suspend member'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/payments')
@admin_required
def payments():
    payments_list = []
    stats = {
        'total_revenue': 0,
        'monthly_revenue': 0,
        'pending_payments': 0,
        'failed_payments': 0
    }

    filters = {
        'status': request.args.get('status', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'page': request.args.get('page', 1, type=int)
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}

        # Get payment statistics
        response = requests.get(f"{API_URL}/admin/payments/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()

        # Get payments list
        response = requests.get(f"{API_URL}/payments", params=filters, headers=headers)
        if response.status_code == 200:
            payments_list = response.json().get('payments', [])

    except:
        pass

    return render_template('admin/payments.html', payments=payments_list, stats=stats, filters=filters)

@admin_bp.route('/payments/<int:payment_id>/verify', methods=['POST'])
@admin_required
def verify_payment(payment_id):
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/admin/payments/{payment_id}/verify", headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Payment verified successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to verify payment'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/events')
@admin_required
def events():
    events_list = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/events", headers=headers)
        if response.status_code == 200:
            events_list = response.json().get('events', [])
    except:
        pass

    return render_template('admin/events.html', events=events_list)

@admin_bp.route('/events/create', methods=['GET', 'POST'])
@admin_required
def create_event():
    if request.method == 'POST':
        event_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'event_type': request.form.get('event_type'),
            'date': request.form.get('date'),
            'time': request.form.get('time'),
            'location': request.form.get('location'),
            'province_id': request.form.get('province_id'),
            'district_id': request.form.get('district_id'),
            'max_attendees': request.form.get('max_attendees', type=int),
            'registration_fee': request.form.get('registration_fee', 0, type=float),
            'is_virtual': 'is_virtual' in request.form,
            'virtual_link': request.form.get('virtual_link')
        }

        try:
            headers = {'Authorization': f'Bearer {session.get("user_token")}'}
            response = requests.post(f"{API_URL}/events", json=event_data, headers=headers)

            if response.status_code == 201:
                flash('Event created successfully!', 'success')
                return redirect(url_for('admin.events'))
            else:
                flash('Failed to create event.', 'danger')
        except:
            flash('Connection error.', 'danger')

    # Get provinces for dropdown
    provinces = []
    try:
        response = requests.get(f"{API_URL}/demographics/provinces")
        if response.status_code == 200:
            provinces = response.json()
    except:
        pass

    return render_template('admin/create_event.html', provinces=provinces)

@admin_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    if request.method == 'POST':
        event_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'date': request.form.get('date'),
            'time': request.form.get('time'),
            'location': request.form.get('location'),
            'max_attendees': request.form.get('max_attendees', type=int),
            'registration_fee': request.form.get('registration_fee', 0, type=float)
        }

        try:
            headers = {'Authorization': f'Bearer {session.get("user_token")}'}
            response = requests.put(f"{API_URL}/events/{event_id}", json=event_data, headers=headers)

            if response.status_code == 200:
                flash('Event updated successfully!', 'success')
                return redirect(url_for('admin.events'))
            else:
                flash('Failed to update event.', 'danger')
        except:
            flash('Connection error.', 'danger')

    # Get event details
    event = None
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/events/{event_id}", headers=headers)
        if response.status_code == 200:
            event = response.json()
    except:
        pass

    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('admin.events'))

    return render_template('admin/edit_event.html', event=event)

@admin_bp.route('/communications')
@admin_required
def communications():
    campaigns = []
    templates = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}

        # Get communication campaigns
        response = requests.get(f"{API_URL}/communications/campaigns", headers=headers)
        if response.status_code == 200:
            campaigns = response.json()

        # Get message templates
        response = requests.get(f"{API_URL}/communications/templates", headers=headers)
        if response.status_code == 200:
            templates = response.json()

    except:
        pass

    return render_template('admin/communications.html', campaigns=campaigns, templates=templates)

@admin_bp.route('/communications/broadcast', methods=['POST'])
@admin_required
def broadcast_message():
    message_data = {
        'title': request.json.get('title'),
        'message': request.json.get('message'),
        'channels': request.json.get('channels', ['sms']),
        'target_group': request.json.get('target_group', 'all'),
        'filters': request.json.get('filters', {})
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/communications/broadcast",
                                json=message_data, headers=headers)

        if response.status_code == 201:
            return jsonify({'success': True, 'message': 'Broadcast sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send broadcast'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/reports')
@admin_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/generate', methods=['POST'])
@admin_required
def generate_report():
    report_type = request.json.get('report_type')
    date_from = request.json.get('date_from')
    date_to = request.json.get('date_to')
    format_type = request.json.get('format', 'pdf')

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/admin/reports/generate",
                                json={
                                    'report_type': report_type,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'format': format_type
                                }, headers=headers)

        if response.status_code == 200:
            report_data = response.json()
            return jsonify({'success': True, 'report_url': report_data.get('url')})
        else:
            return jsonify({'success': False, 'message': 'Failed to generate report'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/settings')
@admin_required
def settings():
    settings_data = {}

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/admin/settings", headers=headers)
        if response.status_code == 200:
            settings_data = response.json()
    except:
        pass

    return render_template('admin/settings.html', settings=settings_data)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
def update_settings():
    settings_data = request.json

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.put(f"{API_URL}/admin/settings",
                               json=settings_data, headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update settings'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/users')
@admin_required
def users():
    users_list = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/admin/users", headers=headers)
        if response.status_code == 200:
            users_list = response.json()
    except:
        pass

    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    user_data = {
        'username': request.json.get('username'),
        'email': request.json.get('email'),
        'password': request.json.get('password'),
        'role': request.json.get('role'),
        'permissions': request.json.get('permissions', [])
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/admin/users",
                                json=user_data, headers=headers)

        if response.status_code == 201:
            return jsonify({'success': True, 'message': 'User created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to create user'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@admin_bp.route('/profile')
@admin_required
def profile():
    return render_template('admin/profile.html')