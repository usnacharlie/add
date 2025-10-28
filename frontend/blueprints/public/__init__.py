from flask import Blueprint, render_template, redirect, url_for, session, request, current_app
import requests
import os

public_bp = Blueprint('public', __name__)

# Backend API URL - Use environment variable or default to backend service
API_URL = os.environ.get('API_URL', 'http://backend:8000') + "/api/v1"
GEOGRAPHY_API_URL = os.environ.get('API_URL', 'http://backend:8000') + "/api/geography"

@public_bp.route('/')
def index():
    # If user is logged in, redirect to appropriate dashboard
    if 'user_token' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('member.dashboard'))

    # Get public statistics
    stats = {
        'total_members': 0,
        'total_events': 0,
        'provinces_covered': 10,
        'active_campaigns': 0
    }

    try:
        response = requests.get(f"{API_URL}/public/stats")
        if response.status_code == 200:
            stats.update(response.json())
    except:
        pass

    return render_template('public/index.html', stats=stats)

@public_bp.route('/about')
def about():
    return render_template('public/about.html')

@public_bp.route('/contact')
def contact():
    return render_template('public/contact.html')

@public_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html')

@public_bp.route('/terms')
def terms():
    return render_template('public/terms.html')

@public_bp.route('/set-language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('public.index'))

@public_bp.route('/ussd-info')
def ussd_info():
    return render_template('public/ussd_info.html')

@public_bp.route('/mobile-app')
def mobile_app():
    return render_template('public/mobile_app.html')

@public_bp.route('/voter-info')
def voter_info():
    # Get voter education information
    voter_data = {
        'registration_centers': [],
        'requirements': [],
        'deadlines': []
    }

    try:
        response = requests.get(f"{API_URL}/public/voter-info")
        if response.status_code == 200:
            voter_data = response.json()
    except:
        pass

    return render_template('public/voter_info.html', voter_data=voter_data)

@public_bp.route('/news')
def news():
    news_items = []

    try:
        response = requests.get(f"{API_URL}/public/news")
        if response.status_code == 200:
            news_items = response.json().get('news', [])
    except:
        pass

    return render_template('public/news.html', news=news_items)

@public_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    article = None

    try:
        response = requests.get(f"{API_URL}/public/news/{news_id}")
        if response.status_code == 200:
            article = response.json()
    except:
        pass

    if not article:
        return redirect(url_for('public.news'))

    return render_template('public/news_detail.html', article=article)

@public_bp.route('/events')
def public_events():
    events = []

    try:
        response = requests.get(f"{API_URL}/public/events")
        if response.status_code == 200:
            events = response.json().get('events', [])
    except:
        pass

    return render_template('public/events.html', events=events)

@public_bp.route('/party-structure')
def party_structure():
    structure_data = {
        'leadership': [],
        'committees': [],
        'regional_offices': []
    }

    try:
        response = requests.get(f"{API_URL}/public/party-structure")
        if response.status_code == 200:
            structure_data = response.json()
    except:
        pass

    return render_template('public/party_structure.html', structure=structure_data)

@public_bp.route('/manifesto')
def manifesto():
    manifesto_data = {
        'vision': '',
        'mission': '',
        'pillars': [],
        'policies': []
    }

    try:
        response = requests.get(f"{API_URL}/public/manifesto")
        if response.status_code == 200:
            manifesto_data = response.json()
    except:
        pass

    return render_template('public/manifesto.html', manifesto=manifesto_data)

@public_bp.route('/donate')
def donate():
    donation_options = []

    try:
        response = requests.get(f"{API_URL}/public/donation-options")
        if response.status_code == 200:
            donation_options = response.json()
    except:
        pass

    return render_template('public/donate.html', options=donation_options)

@public_bp.route('/faq')
def faq():
    faqs = []

    try:
        response = requests.get(f"{API_URL}/public/faqs")
        if response.status_code == 200:
            faqs = response.json()
    except:
        pass

    return render_template('public/faq.html', faqs=faqs)

@public_bp.route('/social-media')
def social_media():
    return render_template('public/social_media.html')

# Geography API Proxy Routes
@public_bp.route('/api/geography/provinces')
def get_provinces():
    try:
        response = requests.get(f"{GEOGRAPHY_API_URL}/provinces")
        if response.status_code == 200:
            return response.json()
        return [], response.status_code
    except Exception as e:
        print(f"Error fetching provinces: {e}")
        return [], 500

@public_bp.route('/api/geography/districts')
def get_districts():
    province_id = request.args.get('province_id')
    if not province_id:
        return {'error': 'province_id is required'}, 400

    try:
        response = requests.get(f"{GEOGRAPHY_API_URL}/districts?province_id={province_id}")
        if response.status_code == 200:
            return response.json()
        return [], response.status_code
    except Exception as e:
        print(f"Error fetching districts: {e}")
        return [], 500

@public_bp.route('/api/geography/constituencies')
def get_constituencies():
    district_id = request.args.get('district_id')
    if not district_id:
        return {'error': 'district_id is required'}, 400

    try:
        response = requests.get(f"{GEOGRAPHY_API_URL}/constituencies?district_id={district_id}")
        if response.status_code == 200:
            return response.json()
        return [], response.status_code
    except Exception as e:
        print(f"Error fetching constituencies: {e}")
        return [], 500

@public_bp.route('/api/geography/wards')
def get_wards():
    constituency_id = request.args.get('constituency_id')
    if not constituency_id:
        return {'error': 'constituency_id is required'}, 400

    try:
        response = requests.get(f"{GEOGRAPHY_API_URL}/wards?constituency_id={constituency_id}")
        if response.status_code == 200:
            return response.json()
        return [], response.status_code
    except Exception as e:
        print(f"Error fetching wards: {e}")
        return [], 500

@public_bp.route('/verify/<membership_number>')
def verify_member(membership_number):
    """Public endpoint to verify member authenticity via QR code scan"""
    member_data = None
    error = None

    try:
        response = requests.get(f"http://localhost:57021/api/members/verify/{membership_number}")
        if response.status_code == 200:
            member_data = response.json()
            # Photo URL is already correct - just use it as-is from backend
            # The /uploads/ route below will proxy it
        elif response.status_code == 404:
            error = "Member not found"
        else:
            error = "Verification failed"
    except Exception as e:
        print(f"Error verifying member: {e}")
        error = "Service unavailable"

    return render_template('public/verify_member.html', member=member_data, error=error)

@public_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Proxy uploaded files from backend for public access"""
    try:
        response = requests.get(f"http://localhost:57021/uploads/{filename}", stream=True)
        from flask import Response
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/octet-stream')
        )
    except:
        from flask import abort
        abort(404)