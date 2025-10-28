from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from functools import wraps
import requests
from datetime import datetime
import os

member_bp = Blueprint('member', __name__, url_prefix='/member')

# Backend API URL - Use environment variable or default to backend service
API_URL = os.environ.get('API_URL', 'http://backend:8000') + "/api"

# Backend uploads proxy route
@member_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Proxy uploaded files from backend"""
    try:
        response = requests.get(f"http://localhost:57021/uploads/{filename}", stream=True)
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/octet-stream')
        )
    except:
        return Response(status=404)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_token' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_member_data():
    """Helper function to get current member data"""
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Transform photo_url to use frontend proxy route
            if data.get('photo_url') and not data['photo_url'].startswith('http'):
                # Change /uploads/photos/file.jpg to /member/uploads/photos/file.jpg
                data['photo_url'] = f"/member{data['photo_url']}"
            return data
    except:
        pass
    return {}

@member_bp.route('/dashboard')
@login_required
def dashboard():
    member_data = get_member_data()

    # Parse created_at if it's a string
    if member_data.get('created_at') and isinstance(member_data.get('created_at'), str):
        try:
            # Try parsing with ISO format (most common from APIs)
            created_at_str = member_data['created_at'].replace('Z', '+00:00')
            member_data['created_at'] = datetime.fromisoformat(created_at_str)
        except:
            try:
                # Try standard format
                member_data['created_at'] = datetime.strptime(member_data['created_at'], '%Y-%m-%d %H:%M:%S')
            except:
                # If parsing fails, set to None
                member_data['created_at'] = None

    # Calculate membership days remaining (countdown from 365)
    membership_days = 365
    if member_data.get('created_at'):
        try:
            days_elapsed = (datetime.now() - member_data['created_at']).days
            membership_days = max(0, 365 - days_elapsed)  # Countdown from 365, minimum 0
        except:
            membership_days = 365

    # Get dashboard statistics
    stats = {
        'membership_status': member_data.get('membership_status', 'Active'),
        'membership_number': session.get('membership_number'),
        'joined_date': member_data.get('created_at', ''),
        'membership_days': membership_days,
        'last_payment': None,
        'upcoming_events': [],
        'recent_activities': [],
        'events_attended': 0,
        'referrals_count': 0
    }

    # Add these counts to member_data as well for template compatibility
    member_data['events_attended'] = 0
    member_data['referrals_count'] = 0

    # Get recent payments
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/payments/member/{session.get('user_id')}/recent", headers=headers)
        if response.status_code == 200:
            payments = response.json()
            if payments:
                stats['last_payment'] = payments[0]
    except:
        pass

    # Get upcoming events
    try:
        response = requests.get(f"{API_URL}/events/upcoming", headers={'Authorization': f'Bearer {session.get("user_token")}'})
        if response.status_code == 200:
            stats['upcoming_events'] = response.json().get('events', [])[:5]
    except:
        pass

    # Get events attended count (when endpoint exists)
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/activities/member/{session.get('user_id')}/count", headers=headers)
        if response.status_code == 200:
            stats['events_attended'] = response.json().get('count', 0)
            member_data['events_attended'] = stats['events_attended']
    except:
        pass

    # Get referrals count (when endpoint exists)
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}/referrals", headers=headers)
        if response.status_code == 200:
            referral_data = response.json()
            stats['referrals_count'] = referral_data.get('stats', {}).get('total', 0) if isinstance(referral_data, dict) else len(referral_data)
            member_data['referrals_count'] = stats['referrals_count']
    except:
        pass

    return render_template('member/dashboard.html', stats=stats, member_data=member_data, now=datetime.now())

@member_bp.route('/profile')
@login_required
def profile():
    member_data = get_member_data()

    # Parse created_at if it's a string
    if member_data.get('created_at') and isinstance(member_data.get('created_at'), str):
        try:
            created_at_str = member_data['created_at'].replace('Z', '+00:00')
            member_data['created_at'] = datetime.fromisoformat(created_at_str)
        except:
            try:
                member_data['created_at'] = datetime.strptime(member_data['created_at'], '%Y-%m-%d %H:%M:%S')
            except:
                member_data['created_at'] = None

    # Map API field names to template field names
    if member_data and member_data.get('first_name'):
        member_data['nrc'] = member_data.get('national_id')
        member_data['phone'] = member_data.get('phone_number')
        member_data['address'] = member_data.get('physical_address')
        # Add default values for fields not in database
        member_data['voter_registration_number'] = member_data.get('voter_registration_number', '')
        member_data['preferred_language'] = member_data.get('preferred_language', 'English')
        member_data['communication_preference'] = member_data.get('communication_preference', 'sms')
    else:
        # If API data is empty, create a basic member object from session
        temp_reg = session.get('temp_registration', {})
        member_data = {
            'first_name': session.get('user_name', '').split()[0] if session.get('user_name') else '',
            'last_name': ' '.join(session.get('user_name', '').split()[1:]) if session.get('user_name') and len(session.get('user_name').split()) > 1 else '',
            'membership_number': session.get('membership_number'),
            'membership_status': 'Active',
            'nrc': session.get('nrc') or temp_reg.get('nrc'),
            'phone': session.get('phone') or temp_reg.get('phone'),
            'email': session.get('email') or temp_reg.get('email'),
            'province': temp_reg.get('province'),
            'district': temp_reg.get('district'),
            'constituency': temp_reg.get('constituency'),
            'ward': temp_reg.get('ward'),
            'address': temp_reg.get('address'),
            'date_of_birth': temp_reg.get('date_of_birth'),
            'gender': temp_reg.get('gender'),
            'occupation': temp_reg.get('occupation'),
            'education_level': temp_reg.get('education_level'),
            'preferred_language': temp_reg.get('preferred_language', 'English'),
            'communication_preference': temp_reg.get('communication_preference', 'sms'),
            'registration_type': temp_reg.get('registration_type', 'lite')
        }
    return render_template('member/profile.html', member=member_data)

@member_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Handle photo upload first
        photo_uploaded = False
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and photo_file.filename != '':
                try:
                    # Reset stream to beginning
                    photo_file.stream.seek(0)

                    headers = {'Authorization': f'Bearer {session.get("user_token")}'}
                    files = {'photo': (photo_file.filename, photo_file.read(), photo_file.content_type)}

                    photo_response = requests.post(
                        f"{API_URL}/members/{session.get('user_id')}/upload-photo",
                        files=files,
                        headers=headers,
                        timeout=30
                    )

                    if photo_response.status_code in [200, 201]:
                        photo_uploaded = True
                        flash('Profile photo updated successfully!', 'success')
                    else:
                        error_detail = f"Status: {photo_response.status_code}"
                        try:
                            error_detail = photo_response.json().get('detail', error_detail)
                        except:
                            pass
                        flash(f'Failed to upload photo: {error_detail}', 'warning')
                        print(f"Photo upload failed: {photo_response.status_code} - {photo_response.text}")
                except Exception as e:
                    print(f"Photo upload error: {e}")
                    flash(f'Photo upload error: {str(e)}', 'warning')

        # Build update data with all editable fields
        update_data = {
            'phone_number': request.form.get('phone'),
            'email': request.form.get('email'),
            'physical_address': request.form.get('address'),
            'occupation': request.form.get('occupation'),
            'education_level': request.form.get('education_level'),
            'date_of_birth': request.form.get('date_of_birth'),
            'gender': request.form.get('gender'),
            'marital_status': request.form.get('marital_status'),
            'voter_registration_number': request.form.get('voter_registration_number')
        }

        # Fetch constituency and ward names from IDs
        try:
            constituency_id = request.form.get('constituency_id')
            ward_id = request.form.get('ward_id')

            if constituency_id:
                resp = requests.get(f"{API_URL}/geography/constituencies/{constituency_id}", timeout=5)
                if resp.status_code == 200:
                    constituency_data = resp.json()
                    update_data['constituency'] = constituency_data.get('constituency_name')

            if ward_id:
                resp = requests.get(f"{API_URL}/geography/wards/{ward_id}", timeout=5)
                if resp.status_code == 200:
                    ward_data = resp.json()
                    update_data['ward'] = ward_data.get('ward_name')
                    # Set branch to ward name if not already set
                    if not update_data.get('branch'):
                        update_data['branch'] = ward_data.get('ward_name')
        except Exception as e:
            print(f"Error fetching location data: {e}")

        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None and v != ''}

        try:
            headers = {'Authorization': f'Bearer {session.get("user_token")}'}
            response = requests.put(
                f"{API_URL}/members/{session.get('user_id')}",
                json=update_data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                # Update session data with new values
                session['phone'] = update_data.get('phone_number', session.get('phone'))
                session['email'] = update_data.get('email', session.get('email'))
                session['address'] = update_data.get('physical_address', session.get('address'))
                session['occupation'] = update_data.get('occupation', session.get('occupation'))
                session['education_level'] = update_data.get('education_level', session.get('education_level'))
                session['gender'] = update_data.get('gender', session.get('gender'))
                session['date_of_birth'] = update_data.get('date_of_birth', session.get('date_of_birth'))
                session['constituency'] = update_data.get('constituency', session.get('constituency'))
                session['ward'] = update_data.get('ward', session.get('ward'))

                if not photo_uploaded:
                    flash('Profile updated successfully!', 'success')
                return redirect(url_for('member.profile'))
            else:
                error_msg = 'Failed to update profile. Please try again.'
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg = f'Update failed: {error_detail}'
                except:
                    pass
                flash(error_msg, 'danger')
        except requests.exceptions.ConnectionError:
            flash('Unable to connect to the server. Please try again later.', 'danger')
        except requests.exceptions.Timeout:
            flash('Request timed out. Please try again.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            print(f"Profile update error: {e}")

    # GET request - load member data for form
    member_data = get_member_data()

    # Map API field names to template field names
    if member_data and member_data.get('first_name'):
        member_data['nrc'] = member_data.get('national_id')
        member_data['phone'] = member_data.get('phone_number')
        member_data['address'] = member_data.get('physical_address')
        # Add default values for fields not in database
        member_data['voter_registration_number'] = member_data.get('voter_registration_number', '')
        member_data['preferred_language'] = member_data.get('preferred_language', 'English')
        member_data['communication_preference'] = member_data.get('communication_preference', 'sms')
    else:
        # If API data is empty, create a basic member object from session
        member_data = {
            'first_name': session.get('first_name', ''),
            'last_name': session.get('last_name', ''),
            'membership_number': session.get('membership_number'),
            'membership_status': session.get('membership_status', 'Active'),
            'nrc': session.get('nrc'),
            'phone': session.get('phone'),
            'email': session.get('email'),
            'constituency': session.get('constituency'),
            'ward': session.get('ward'),
            'address': session.get('address'),
            'date_of_birth': session.get('date_of_birth'),
            'gender': session.get('gender'),
            'marital_status': session.get('marital_status'),
            'occupation': session.get('occupation'),
            'education_level': session.get('education_level'),
            'voter_registration_number': session.get('voter_registration_number')
        }

    return render_template('member/edit_profile.html', member=member_data)

@member_bp.route('/payments')
@login_required
def payments():
    payments_list = []
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/payments/member/{session.get('user_id')}", headers=headers)
        if response.status_code == 200:
            payments_list = response.json()
    except:
        pass

    return render_template('member/payments.html', payments=payments_list)

@member_bp.route('/payments/make', methods=['POST'])
@login_required
def make_payment():
    payment_data = {
        'member_id': session.get('user_id'),
        'amount': request.json.get('amount'),
        'payment_method': request.json.get('payment_method'),
        'payment_reference': request.json.get('payment_reference'),
        'payment_year': request.json.get('payment_year'),
        'payment_status': 'pending',
        'notes': request.json.get('notes'),
        'payment_phone': request.json.get('payment_phone')  # Phone number for Cgrade payments
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        print(f"DEBUG: Posting to {API_URL}/payments with data: {payment_data}")
        response = requests.post(f"{API_URL}/payments", json=payment_data, headers=headers)
        print(f"DEBUG: Response status: {response.status_code}, Response: {response.text}")

        if response.status_code in [200, 201]:
            return jsonify({'success': True, 'message': 'Payment recorded successfully'})
        else:
            error_msg = 'Payment submission failed'
            try:
                error_detail = response.json().get('detail', '')
                if error_detail:
                    error_msg = error_detail
            except:
                pass
            return jsonify({'success': False, 'message': error_msg}), 400
    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/events')
@login_required
def events():
    events_list = []
    registrations = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        # Get all events
        response = requests.get(f"{API_URL}/events", headers=headers)
        if response.status_code == 200:
            events_list = response.json().get('events', [])

        # Get member's registrations
        response = requests.get(f"{API_URL}/events/member/{session.get('user_id')}/registrations", headers=headers)
        if response.status_code == 200:
            registrations = [r['event_id'] for r in response.json()]
    except:
        pass

    return render_template('member/events.html', events=events_list, registrations=registrations)

@member_bp.route('/events/register/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        registration_data = {
            'member_id': session.get('user_id'),
            'event_id': event_id
        }

        response = requests.post(f"{API_URL}/events/{event_id}/register",
                                json=registration_data, headers=headers)

        if response.status_code == 201:
            return jsonify({'success': True, 'message': 'Successfully registered for event'})
        else:
            return jsonify({'success': False, 'message': 'Registration failed'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/events/<int:event_id>/details')
@login_required
def event_details(event_id):
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/events/{event_id}", headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'event': response.json()})
        else:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/documents')
@login_required
def documents():
    documents_list = []
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}/documents", headers=headers)
        if response.status_code == 200:
            documents_list = response.json()
    except:
        pass

    return render_template('member/documents.html', documents=documents_list)

@member_bp.route('/card')
@login_required
def membership_card():
    member_data = get_member_data()

    # Parse created_at if it's a string
    if member_data.get('created_at') and isinstance(member_data.get('created_at'), str):
        try:
            created_at_str = member_data['created_at'].replace('Z', '+00:00')
            member_data['created_at'] = datetime.fromisoformat(created_at_str)
        except:
            try:
                member_data['created_at'] = datetime.strptime(member_data['created_at'], '%Y-%m-%d %H:%M:%S')
            except:
                member_data['created_at'] = None

    # If API data is empty, create a basic member object from session
    if not member_data or not member_data.get('first_name'):
        temp_reg = session.get('temp_registration', {})
        member_data = {
            'first_name': session.get('user_name', '').split()[0] if session.get('user_name') else '',
            'last_name': ' '.join(session.get('user_name', '').split()[1:]) if session.get('user_name') and len(session.get('user_name').split()) > 1 else '',
            'membership_number': session.get('membership_number'),
            'membership_status': 'Active',
            'nrc': session.get('nrc') or temp_reg.get('nrc'),
            'phone': session.get('phone') or temp_reg.get('phone'),
            'email': session.get('email') or temp_reg.get('email'),
            'province': temp_reg.get('province'),
            'district': temp_reg.get('district'),
            'constituency': temp_reg.get('constituency'),
            'ward': temp_reg.get('ward'),
            'address': temp_reg.get('address'),
            'date_of_birth': temp_reg.get('date_of_birth'),
            'registration_type': temp_reg.get('registration_type', 'lite')
        }
    return render_template('member/card.html', member=member_data)

@member_bp.route('/card/download')
@login_required
def download_card():
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}/card", headers=headers)

        if response.status_code == 200:
            # Return the PDF file
            return response.content, 200, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'attachment; filename=membership_card_{session.get("membership_number")}.pdf'
            }
    except:
        flash('Failed to generate membership card.', 'danger')

    return redirect(url_for('member.membership_card'))

@member_bp.route('/activities')
@login_required
def activities():
    activities_list = []
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}/activities", headers=headers)
        if response.status_code == 200:
            activities_list = response.json()
    except:
        pass

    return render_template('member/activities.html', activities=activities_list)

@member_bp.route('/volunteer')
@login_required
def volunteer():
    opportunities = []
    my_volunteering = []

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        # Get volunteer opportunities
        response = requests.get(f"{API_URL}/volunteer/opportunities", headers=headers)
        if response.status_code == 200:
            opportunities = response.json()

        # Get member's volunteer history
        response = requests.get(f"{API_URL}/volunteer/member/{session.get('user_id')}", headers=headers)
        if response.status_code == 200:
            my_volunteering = response.json()
    except:
        pass

    return render_template('member/volunteer.html',
                         opportunities=opportunities,
                         my_volunteering=my_volunteering)

@member_bp.route('/volunteer/signup/<int:opportunity_id>', methods=['POST'])
@login_required
def volunteer_signup(opportunity_id):
    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        signup_data = {
            'member_id': session.get('user_id'),
            'opportunity_id': opportunity_id,
            'availability': request.json.get('availability')
        }

        response = requests.post(f"{API_URL}/volunteer/signup",
                                json=signup_data, headers=headers)

        if response.status_code == 201:
            return jsonify({'success': True, 'message': 'Successfully signed up as volunteer'})
        else:
            return jsonify({'success': False, 'message': 'Signup failed'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/referrals')
@login_required
def referrals():
    referrals_list = []
    referral_stats = {'total': 0, 'active': 0, 'pending': 0}

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.get(f"{API_URL}/members/{session.get('user_id')}/referrals", headers=headers)
        if response.status_code == 200:
            data = response.json()
            referrals_list = data.get('referrals', [])
            referral_stats = data.get('stats', referral_stats)
    except:
        pass

    return render_template('member/referrals.html',
                         referrals=referrals_list,
                         stats=referral_stats)

@member_bp.route('/referrals/invite', methods=['POST'])
@login_required
def send_referral():
    referral_data = {
        'referrer_id': session.get('user_id'),
        'name': request.json.get('name'),
        'phone_number': request.json.get('phone'),  # Backend expects 'phone_number'
        'email': request.json.get('email')
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.post(f"{API_URL}/referrals/send", json=referral_data, headers=headers)

        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                'success': result.get('success', True),
                'message': result.get('message', 'Referral invitation sent successfully'),
                'sms_sent': result.get('sms_sent', False),
                'email_sent': result.get('email_sent', False)
            })
        else:
            error_msg = 'Failed to send referral'
            try:
                error_detail = response.json().get('message', '')
                if error_detail:
                    error_msg = error_detail
            except:
                pass
            return jsonify({'success': False, 'message': error_msg}), 400
    except Exception as e:
        print(f"Referral send error: {e}")
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/settings')
@login_required
def settings():
    member_data = get_member_data()
    return render_template('member/settings.html', member=member_data)

@member_bp.route('/settings/notifications', methods=['POST'])
@login_required
def update_notifications():
    settings_data = {
        'sms_notifications': request.json.get('sms_notifications', True),
        'email_notifications': request.json.get('email_notifications', True),
        'whatsapp_notifications': request.json.get('whatsapp_notifications', False),
        'event_reminders': request.json.get('event_reminders', True),
        'payment_reminders': request.json.get('payment_reminders', True)
    }

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.put(f"{API_URL}/members/{session.get('user_id')}/notifications",
                               json=settings_data, headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Notification settings updated'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update settings'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500

@member_bp.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    password_data = {
        'old_password': request.json.get('old_password'),
        'new_password': request.json.get('new_password')
    }

    if len(password_data['new_password']) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

    try:
        headers = {'Authorization': f'Bearer {session.get("user_token")}'}
        response = requests.put(f"{API_URL}/members/{session.get('user_id')}/change-password",
                               json=password_data, headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Password changed successfully'})
        elif response.status_code == 401:
            return jsonify({'success': False, 'message': 'Incorrect old password'}), 401
        else:
            return jsonify({'success': False, 'message': 'Failed to change password'}), 400
    except:
        return jsonify({'success': False, 'message': 'Connection error'}), 500