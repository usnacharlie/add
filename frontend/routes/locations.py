"""
Location management routes (Provinces, Districts, Wards)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
import requests

locations_bp = Blueprint('locations', __name__)


@locations_bp.route('/provinces')
def provinces():
    """List all provinces"""
    api_url = current_app.config['API_BASE_URL']
    try:
        provinces = requests.get(f"{api_url}/provinces/").json()
        districts = requests.get(f"{api_url}/districts/").json()
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        provinces = []
        districts = []
        constituencies = []
        wards = []
        flash('Error connecting to API', 'error')

    return render_template('locations/provinces.html',
                         provinces=provinces,
                         districts=districts,
                         constituencies=constituencies,
                         wards=wards)


@locations_bp.route('/provinces/new', methods=['GET', 'POST'])
def new_province():
    """Create a new province"""
    api_url = current_app.config['API_BASE_URL']

    if request.method == 'POST':
        province_data = {'name': request.form.get('name')}

        try:
            response = requests.post(f"{api_url}/provinces/", json=province_data)
            if response.status_code == 201:
                flash('Province created successfully!', 'success')
                return redirect(url_for('locations.provinces'))
            else:
                flash('Error creating province', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('locations/new_province.html')


@locations_bp.route('/districts/create', methods=['POST'])
def create_district():
    """Create a new district"""
    api_url = current_app.config['API_BASE_URL']
    province_id = request.form.get('province_id')

    district_data = {
        'name': request.form.get('name'),
        'province_id': int(province_id)
    }

    try:
        response = requests.post(f"{api_url}/districts/", json=district_data)
        if response.status_code == 201:
            flash('District created successfully!', 'success')
        else:
            flash('Error creating district', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.districts', province_id=province_id))


@locations_bp.route('/districts/<int:district_id>/edit', methods=['POST'])
def edit_district(district_id):
    """Edit a district"""
    api_url = current_app.config['API_BASE_URL']

    # Get current district to find province_id
    district_response = requests.get(f"{api_url}/districts/{district_id}")
    if district_response.status_code != 200:
        flash('District not found', 'error')
        return redirect(url_for('locations.provinces'))

    district = district_response.json()
    province_id = district['province_id']

    district_data = {
        'name': request.form.get('name'),
        'province_id': province_id
    }

    try:
        response = requests.put(f"{api_url}/districts/{district_id}", json=district_data)
        if response.status_code == 200:
            flash('District updated successfully!', 'success')
        else:
            flash('Error updating district', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.districts', province_id=province_id))


@locations_bp.route('/districts/<int:district_id>/delete', methods=['POST'])
def delete_district(district_id):
    """Delete a district"""
    api_url = current_app.config['API_BASE_URL']

    # Get district to find province_id before deletion
    district_response = requests.get(f"{api_url}/districts/{district_id}")
    if district_response.status_code != 200:
        flash('District not found', 'error')
        return redirect(url_for('locations.provinces'))

    district = district_response.json()
    province_id = district['province_id']

    try:
        response = requests.delete(f"{api_url}/districts/{district_id}")
        if response.status_code == 204:
            flash('District deleted successfully!', 'success')
        else:
            flash('Error deleting district', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.districts', province_id=province_id))


@locations_bp.route('/districts/<int:province_id>')
def districts(province_id):
    """List districts by province"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/districts/province/{province_id}")
        districts = response.json() if response.status_code == 200 else []

        province_response = requests.get(f"{api_url}/provinces/{province_id}")
        province = province_response.json() if province_response.status_code == 200 else None

        # Get all constituencies and wards for stats
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        districts = []
        province = None
        constituencies = []
        wards = []
        flash('Error connecting to API', 'error')

    return render_template('locations/districts.html',
                         districts=districts,
                         province=province,
                         constituencies=constituencies,
                         wards=wards)


@locations_bp.route('/constituencies/create', methods=['POST'])
def create_constituency():
    """Create a new constituency"""
    api_url = current_app.config['API_BASE_URL']
    district_id = request.form.get('district_id')

    constituency_data = {
        'name': request.form.get('name'),
        'district_id': int(district_id)
    }

    try:
        response = requests.post(f"{api_url}/constituencies/", json=constituency_data)
        if response.status_code == 201:
            flash('Constituency created successfully!', 'success')
        else:
            flash('Error creating constituency', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.constituencies', district_id=district_id))


@locations_bp.route('/constituencies/<int:constituency_id>/edit', methods=['POST'])
def edit_constituency(constituency_id):
    """Edit a constituency"""
    api_url = current_app.config['API_BASE_URL']

    # Get current constituency to find district_id
    constituency_response = requests.get(f"{api_url}/constituencies/{constituency_id}")
    if constituency_response.status_code != 200:
        flash('Constituency not found', 'error')
        return redirect(url_for('locations.provinces'))

    constituency = constituency_response.json()
    district_id = constituency['district_id']

    constituency_data = {
        'name': request.form.get('name'),
        'district_id': district_id
    }

    try:
        response = requests.put(f"{api_url}/constituencies/{constituency_id}", json=constituency_data)
        if response.status_code == 200:
            flash('Constituency updated successfully!', 'success')
        else:
            flash('Error updating constituency', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.constituencies', district_id=district_id))


@locations_bp.route('/constituencies/<int:constituency_id>/delete', methods=['POST'])
def delete_constituency(constituency_id):
    """Delete a constituency"""
    api_url = current_app.config['API_BASE_URL']

    # Get constituency to find district_id before deletion
    constituency_response = requests.get(f"{api_url}/constituencies/{constituency_id}")
    if constituency_response.status_code != 200:
        flash('Constituency not found', 'error')
        return redirect(url_for('locations.provinces'))

    constituency = constituency_response.json()
    district_id = constituency['district_id']

    try:
        response = requests.delete(f"{api_url}/constituencies/{constituency_id}")
        if response.status_code == 204:
            flash('Constituency deleted successfully!', 'success')
        else:
            flash('Error deleting constituency', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.constituencies', district_id=district_id))


@locations_bp.route('/constituencies/<int:district_id>')
def constituencies(district_id):
    """List constituencies by district"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/constituencies/district/{district_id}")
        constituencies = response.json() if response.status_code == 200 else []

        district_response = requests.get(f"{api_url}/districts/{district_id}")
        district = district_response.json() if district_response.status_code == 200 else None

        # Get wards for stats
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        constituencies = []
        district = None
        wards = []
        flash('Error connecting to API', 'error')

    return render_template('locations/constituencies.html',
                         constituencies=constituencies,
                         district=district,
                         wards=wards)


@locations_bp.route('/wards/create', methods=['POST'])
def create_ward():
    """Create a new ward"""
    api_url = current_app.config['API_BASE_URL']
    constituency_id = request.form.get('constituency_id')

    ward_data = {
        'name': request.form.get('name'),
        'constituency_id': int(constituency_id)
    }

    try:
        response = requests.post(f"{api_url}/wards/", json=ward_data)
        if response.status_code == 201:
            flash('Ward created successfully!', 'success')
        else:
            flash('Error creating ward', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.wards', constituency_id=constituency_id))


@locations_bp.route('/wards/<int:ward_id>/edit', methods=['POST'])
def edit_ward(ward_id):
    """Edit a ward"""
    api_url = current_app.config['API_BASE_URL']

    # Get current ward to find constituency_id
    ward_response = requests.get(f"{api_url}/wards/{ward_id}")
    if ward_response.status_code != 200:
        flash('Ward not found', 'error')
        return redirect(url_for('locations.provinces'))

    ward = ward_response.json()
    constituency_id = ward['constituency_id']

    ward_data = {
        'name': request.form.get('name'),
        'constituency_id': constituency_id
    }

    try:
        response = requests.put(f"{api_url}/wards/{ward_id}", json=ward_data)
        if response.status_code == 200:
            flash('Ward updated successfully!', 'success')
        else:
            flash('Error updating ward', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.wards', constituency_id=constituency_id))


@locations_bp.route('/wards/<int:ward_id>/delete', methods=['POST'])
def delete_ward(ward_id):
    """Delete a ward"""
    api_url = current_app.config['API_BASE_URL']

    # Get ward to find constituency_id before deletion
    ward_response = requests.get(f"{api_url}/wards/{ward_id}")
    if ward_response.status_code != 200:
        flash('Ward not found', 'error')
        return redirect(url_for('locations.provinces'))

    ward = ward_response.json()
    constituency_id = ward['constituency_id']

    try:
        response = requests.delete(f"{api_url}/wards/{ward_id}")
        if response.status_code == 204:
            flash('Ward deleted successfully!', 'success')
        else:
            flash('Error deleting ward', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('locations.wards', constituency_id=constituency_id))


@locations_bp.route('/wards/<int:constituency_id>')
def wards(constituency_id):
    """List wards by constituency"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/wards/constituency/{constituency_id}")
        wards = response.json() if response.status_code == 200 else []

        constituency_response = requests.get(f"{api_url}/constituencies/{constituency_id}")
        constituency = constituency_response.json() if constituency_response.status_code == 200 else None
    except:
        wards = []
        constituency = None
        flash('Error connecting to API', 'error')

    return render_template('locations/wards.html', wards=wards, constituency=constituency)


# API endpoints for dynamic loading (AJAX)
@locations_bp.route('/api/districts/<int:province_id>')
def api_get_districts(province_id):
    """API endpoint to get districts for a province"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/districts/province/{province_id}")
        return jsonify(response.json() if response.status_code == 200 else [])
    except:
        return jsonify([])


@locations_bp.route('/api/wards/<int:district_id>')
def api_get_wards(district_id):
    """API endpoint to get wards for a district"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/wards/district/{district_id}")
        return jsonify(response.json() if response.status_code == 200 else [])
    except:
        return jsonify([])
