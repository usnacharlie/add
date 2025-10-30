"""
Member Portal Routes - For individual members to view their own data
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import requests
from datetime import date, datetime
import qrcode
import io
import base64
import json
import os
from werkzeug.utils import secure_filename

member_portal_bp = Blueprint('member_portal', __name__, url_prefix='/my')


@member_portal_bp.route('/dashboard')
def dashboard():
    """Member's personal dashboard"""
    if 'user_token' not in session:
        flash('Please login to access your dashboard', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')  # Assuming user_id is stored in session

    try:
        # Get member details
        member_response = requests.get(f"{api_url}/members/{member_id}", timeout=5)
        if member_response.status_code == 200:
            member = member_response.json()
        else:
            flash(f'Error loading member profile: {member_response.status_code}', 'error')
            member = None

        # Get member's events
        events_response = requests.get(f"{api_url}/events/registrations/member/{member_id}", timeout=5)
        if events_response.status_code == 200:
            events = events_response.json()
        else:
            events = []

        # Get member's referrals
        referrals_response = requests.get(f"{api_url}/referrals/?referrer_id={member_id}", timeout=5)
        if referrals_response.status_code == 200:
            referrals_data = referrals_response.json()
            referrals = referrals_data.get('referrals', [])
        else:
            referrals = []

        # Calculate statistics
        stats = {
            'total_events': len(events),
            'upcoming_events': sum(1 for e in events if e.get('event', {}).get('status') == 'upcoming'),
            'total_referrals': len(referrals),
            'successful_referrals': sum(1 for r in referrals if r.get('status') == 'registered'),
            'pending_referrals': sum(1 for r in referrals if r.get('status') == 'pending')
        }

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        member = None
        events = []
        referrals = []
        stats = {
            'total_events': 0,
            'upcoming_events': 0,
            'total_referrals': 0,
            'successful_referrals': 0,
            'pending_referrals': 0
        }

    return render_template('member_portal/dashboard.html',
                         member=member,
                         events=events[:5],  # Latest 5 events
                         referrals=referrals[:5],  # Latest 5 referrals
                         stats=stats)


@member_portal_bp.route('/profile')
def profile():
    """View member's own profile"""
    if 'user_token' not in session:
        flash('Please login to access your profile', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    try:
        response = requests.get(f"{api_url}/members/{member_id}")
        member = response.json() if response.status_code == 200 else None
    except:
        member = None
        flash('Error loading profile', 'error')

    return render_template('member_portal/profile.html', member=member)


@member_portal_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit member's own profile"""
    if 'user_token' not in session:
        flash('Please login to edit your profile', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    if request.method == 'POST':
        member_data = {
            'name': request.form.get('name'),
            'gender': request.form.get('gender'),
            'date_of_birth': request.form.get('date_of_birth') if request.form.get('date_of_birth') else None,
            'contact': request.form.get('contact'),
            'email': request.form.get('email')
        }

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Validate file
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                if file_ext in allowed_extensions:
                    # Create uploads directory if it doesn't exist
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
                    os.makedirs(upload_folder, exist_ok=True)

                    # Generate unique filename with member_id
                    new_filename = f"member_{member_id}_{int(datetime.now().timestamp())}.{file_ext}"
                    file_path = os.path.join(upload_folder, new_filename)

                    # Save file
                    file.save(file_path)

                    # Store relative path in database
                    member_data['profile_picture'] = f'uploads/profiles/{new_filename}'
                else:
                    flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.', 'warning')

        try:
            response = requests.put(f"{api_url}/members/{member_id}", json=member_data)
            if response.status_code == 200:
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('member_portal.profile'))
            else:
                flash('Error updating profile', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    try:
        member_response = requests.get(f"{api_url}/members/{member_id}")
        member = member_response.json() if member_response.status_code == 200 else None
    except:
        member = None
        flash('Error loading profile', 'error')

    return render_template('member_portal/edit_profile.html', member=member, today=date.today().isoformat())


@member_portal_bp.route('/events')
def my_events():
    """View all events member is registered for"""
    if 'user_token' not in session:
        flash('Please login to view your events', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    try:
        response = requests.get(f"{api_url}/events/registrations/member/{member_id}")
        events = response.json() if response.status_code == 200 else []

        # Categorize events
        upcoming = [e for e in events if e.get('event', {}).get('status') == 'upcoming']
        ongoing = [e for e in events if e.get('event', {}).get('status') == 'ongoing']
        completed = [e for e in events if e.get('event', {}).get('status') == 'completed']

    except Exception as e:
        flash(f'Error loading events: {str(e)}', 'error')
        upcoming = []
        ongoing = []
        completed = []

    return render_template('member_portal/events.html',
                         upcoming=upcoming,
                         ongoing=ongoing,
                         completed=completed)


@member_portal_bp.route('/referrals')
def my_referrals():
    """View all referrals made by member"""
    if 'user_token' not in session:
        flash('Please login to view your referrals', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    try:
        # Get referrals
        response = requests.get(f"{api_url}/referrals/?referrer_id={member_id}")
        data = response.json() if response.status_code == 200 else {}
        referrals = data.get('referrals', [])

        # Calculate statistics
        total = len(referrals)
        pending = sum(1 for r in referrals if r.get('status') == 'pending')
        contacted = sum(1 for r in referrals if r.get('status') == 'contacted')
        successful = sum(1 for r in referrals if r.get('status') == 'registered')
        conversion_rate = (successful / total * 100) if total > 0 else 0

        stats = {
            'total_referrals': total,
            'pending_referrals': pending,
            'contacted_referrals': contacted,
            'successful_referrals': successful,
            'conversion_rate': round(conversion_rate, 1)
        }

    except Exception as e:
        flash(f'Error loading referrals: {str(e)}', 'error')
        referrals = []
        stats = {}

    return render_template('member_portal/referrals.html',
                         referrals=referrals,
                         stats=stats)


@member_portal_bp.route('/referrals/new', methods=['GET', 'POST'])
def new_referral():
    """Create a new referral"""
    if 'user_token' not in session:
        flash('Please login to create a referral', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    if request.method == 'POST':
        referral_data = {
            'referrer_id': member_id,
            'referred_name': request.form.get('referred_name'),
            'referred_contact': request.form.get('referred_contact'),
            'referred_email': request.form.get('referred_email'),
            'notes': request.form.get('notes')
        }

        try:
            response = requests.post(f"{api_url}/referrals", json=referral_data)
            if response.status_code == 201:
                flash('Referral created successfully!', 'success')
                return redirect(url_for('member_portal.my_referrals'))
            else:
                flash('Error creating referral', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('member_portal/new_referral.html')


@member_portal_bp.route('/membership-card')
def membership_card():
    """View member's digital membership card with QR code"""
    if 'user_token' not in session:
        flash('Please login to view your membership card', 'warning')
        return redirect(url_for('auth.login'))

    api_url = current_app.config['API_BASE_URL']
    member_id = session.get('user_id')

    try:
        # Get member details
        response = requests.get(f"{api_url}/members/{member_id}")
        if response.status_code != 200:
            flash('Error loading member details', 'error')
            return redirect(url_for('member_portal.dashboard'))

        member = response.json()

        # Generate QR code with member verification data
        qr_data = {
            'member_id': member.get('id'),
            'name': member.get('name'),
            'nrc': member.get('nrc'),
            'contact': member.get('contact'),
            'ward_id': member.get('ward_id'),
            'verification_code': f"ADD-{member.get('id'):05d}"
        }

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)

        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 for embedding in HTML
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Get ward details for display
        ward_name = "N/A"
        constituency_name = "N/A"
        district_name = "N/A"
        province_name = "N/A"

        if member.get('ward_id'):
            try:
                ward_response = requests.get(f"{api_url}/wards/{member.get('ward_id')}")
                if ward_response.status_code == 200:
                    ward = ward_response.json()
                    ward_name = ward.get('name')

                    # Get constituency
                    if ward.get('constituency_id'):
                        const_response = requests.get(f"{api_url}/constituencies/{ward.get('constituency_id')}")
                        if const_response.status_code == 200:
                            constituency = const_response.json()
                            constituency_name = constituency.get('name')

                            # Get district
                            if constituency.get('district_id'):
                                dist_response = requests.get(f"{api_url}/districts/{constituency.get('district_id')}")
                                if dist_response.status_code == 200:
                                    district = dist_response.json()
                                    district_name = district.get('name')

                                    # Get province
                                    if district.get('province_id'):
                                        prov_response = requests.get(f"{api_url}/provinces/{district.get('province_id')}")
                                        if prov_response.status_code == 200:
                                            province = prov_response.json()
                                            province_name = province.get('name')
            except:
                pass

    except Exception as e:
        flash(f'Error generating membership card: {str(e)}', 'error')
        return redirect(url_for('member_portal.dashboard'))

    return render_template('member_portal/membership_card.html',
                         member=member,
                         qr_code=qr_code_base64,
                         ward_name=ward_name,
                         constituency_name=constituency_name,
                         district_name=district_name,
                         province_name=province_name,
                         verification_code=f"ADD-{member.get('id'):05d}")
