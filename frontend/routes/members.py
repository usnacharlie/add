"""
Member management routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import requests

members_bp = Blueprint('members', __name__)


@members_bp.route('/')
def list_members():
    """List all members"""
    api_url = current_app.config['API_BASE_URL']
    search_query = request.args.get('search', '')

    try:
        if search_query:
            response = requests.get(f"{api_url}/members/?name={search_query}")
        else:
            response = requests.get(f"{api_url}/members/")
        members = response.json() if response.status_code == 200 else []
    except:
        members = []
        flash('Error connecting to API', 'error')

    return render_template('members/list.html', members=members, search_query=search_query)


@members_bp.route('/new', methods=['GET', 'POST'])
def new_member():
    """Add new members quickly"""
    api_url = current_app.config['API_BASE_URL']

    if request.method == 'POST':
        # Collect all member data
        members_added = 0
        errors = 0

        for i in range(10):  # Support up to 10 members at once
            name = request.form.get(f'member_{i}_name')
            if name and name.strip():  # Only process if name is provided
                member_data = {
                    'name': name.strip(),
                    'gender': request.form.get(f'member_{i}_gender'),
                    'age': int(request.form.get(f'member_{i}_age')) if request.form.get(f'member_{i}_age') else None,
                    'nrc': request.form.get(f'member_{i}_nrc'),
                    'voters_id': request.form.get(f'member_{i}_voters_id'),
                    'contact': request.form.get(f'member_{i}_contact'),
                    'ward_id': int(request.form.get(f'member_{i}_ward_id'))
                }

                try:
                    response = requests.post(f"{api_url}/members/", json=member_data)
                    if response.status_code == 201:
                        members_added += 1
                    else:
                        errors += 1
                except:
                    errors += 1

        if members_added > 0:
            flash(f'Successfully added {members_added} member(s)!', 'success')
        if errors > 0:
            flash(f'{errors} member(s) failed to add. Please try again.', 'error')

        if members_added > 0:
            return redirect(url_for('members.list_members'))

    # Get location data for dropdowns
    try:
        provinces = requests.get(f"{api_url}/provinces/").json()
        districts = requests.get(f"{api_url}/districts/").json()
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        provinces, districts, constituencies, wards = [], [], [], []
        flash('Error loading location data', 'error')

    return render_template('members/new.html', provinces=provinces, districts=districts, constituencies=constituencies, wards=wards)


@members_bp.route('/<int:member_id>')
def view_member(member_id):
    """View a specific member"""
    api_url = current_app.config['API_BASE_URL']
    try:
        response = requests.get(f"{api_url}/members/{member_id}")
        member = response.json() if response.status_code == 200 else None
    except:
        member = None
        flash('Error loading member', 'error')
    
    return render_template('members/view.html', member=member)


@members_bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    """Edit a member"""
    api_url = current_app.config['API_BASE_URL']
    
    if request.method == 'POST':
        member_data = {
            'name': request.form.get('name'),
            'gender': request.form.get('gender'),
            'age': int(request.form.get('age')) if request.form.get('age') else None,
            'nrc': request.form.get('nrc'),
            'voters_id': request.form.get('voters_id'),
            'contact': request.form.get('contact'),
            'ward_id': int(request.form.get('ward_id'))
        }
        
        try:
            response = requests.put(f"{api_url}/members/{member_id}", json=member_data)
            if response.status_code == 200:
                flash('Member updated successfully!', 'success')
                return redirect(url_for('members.view_member', member_id=member_id))
            else:
                flash('Error updating member', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    try:
        member_response = requests.get(f"{api_url}/members/{member_id}")
        member = member_response.json() if member_response.status_code == 200 else None
        
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        member = None
        wards = []
        flash('Error loading data', 'error')
    
    return render_template('members/edit.html', member=member, wards=wards)
