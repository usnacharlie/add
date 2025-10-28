"""
Main routes
"""
from flask import Blueprint, render_template, session, current_app
import requests

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page"""
    api_url = current_app.config.get('API_BASE_URL', 'http://localhost:9500/api/v1')

    try:
        # Fetch real data from API
        members_response = requests.get(f"{api_url}/members/", timeout=2)
        provinces_response = requests.get(f"{api_url}/provinces/", timeout=2)

        total_members = len(members_response.json()) if members_response.status_code == 200 else 0
        provinces_count = len(provinces_response.json()) if provinces_response.status_code == 200 else 0

        stats = {
            'total_members': f"{total_members:,}",
            'provinces_covered': str(provinces_count),
            'total_events': '0',
            'active_campaigns': '0'
        }
    except:
        # Fallback if API is not available
        stats = {
            'total_members': '0',
            'provinces_covered': '0',
            'total_events': '0',
            'active_campaigns': '0'
        }

    return render_template('landing.html', stats=stats)


@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_token' not in session:
        return index()

    api_url = current_app.config.get('API_BASE_URL', 'http://localhost:9500/api/v1')

    try:
        # Fetch real data from API
        members_response = requests.get(f"{api_url}/members/", timeout=2)
        provinces_response = requests.get(f"{api_url}/provinces/", timeout=2)
        districts_response = requests.get(f"{api_url}/districts/", timeout=2)
        wards_response = requests.get(f"{api_url}/wards/", timeout=2)

        members = members_response.json() if members_response.status_code == 200 else []
        provinces = provinces_response.json() if provinces_response.status_code == 200 else []
        districts = districts_response.json() if districts_response.status_code == 200 else []
        wards = wards_response.json() if wards_response.status_code == 200 else []

        # Calculate statistics
        total_members = len(members)
        total_provinces = len(provinces)
        total_districts = len(districts)
        total_wards = len(wards)

        # Gender breakdown
        male_count = sum(1 for m in members if m.get('gender') == 'Male')
        female_count = sum(1 for m in members if m.get('gender') == 'Female')

        # Count members by province (using ward relationships)
        province_counts = {}
        for member in members:
            ward_id = member.get('ward_id')
            if ward_id:
                # Find the ward
                ward = next((w for w in wards if w['id'] == ward_id), None)
                if ward:
                    district_id = ward.get('district_id')
                    district = next((d for d in districts if d['id'] == district_id), None)
                    if district:
                        province_id = district.get('province_id')
                        province = next((p for p in provinces if p['id'] == province_id), None)
                        if province:
                            province_name = province.get('name')
                            province_counts[province_name] = province_counts.get(province_name, 0) + 1

        # Sort provinces by member count (descending)
        sorted_provinces = sorted(province_counts.items(), key=lambda x: x[1], reverse=True)

        stats = {
            'total_members': total_members,
            'total_provinces': total_provinces,
            'total_districts': total_districts,
            'total_wards': total_wards,
            'male_count': male_count,
            'female_count': female_count,
            'province_counts': sorted_provinces
        }

    except Exception as e:
        # Fallback if API is not available
        stats = {
            'total_members': 0,
            'total_provinces': 0,
            'total_districts': 0,
            'total_wards': 0,
            'male_count': 0,
            'female_count': 0,
            'province_counts': []
        }

    return render_template('dashboard.html', stats=stats)
