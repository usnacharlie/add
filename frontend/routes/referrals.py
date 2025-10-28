"""
Referral Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests

referrals_bp = Blueprint('referrals', __name__, url_prefix='/referrals')

API_BASE_URL = "http://localhost:9500/api/v1"


@referrals_bp.route('/')
def list_referrals():
    """List all referrals"""
    try:
        # Get filter parameters from query string
        params = {
            'skip': request.args.get('skip', 0),
            'limit': request.args.get('limit', 100),
            'status': request.args.get('status'),
            'referrer_id': request.args.get('referrer_id'),
            'search': request.args.get('search')
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None and v != ''}

        # Get referrals from API
        response = requests.get(f"{API_BASE_URL}/referrals", params=params)
        response.raise_for_status()
        referrals_data = response.json()

        # Get statistics
        stats_response = requests.get(f"{API_BASE_URL}/referrals/statistics")
        stats_response.raise_for_status()
        statistics = stats_response.json()

        # Get members for filter dropdown
        members_response = requests.get(f"{API_BASE_URL}/members/")
        members = members_response.json() if members_response.ok else []

        return render_template(
            'admin/referrals/list.html',
            referrals=referrals_data.get('referrals', []),
            total=referrals_data.get('total', 0),
            statistics=statistics,
            members=members,
            filters=request.args
        )
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching referrals: {str(e)}", "danger")
        return render_template('admin/referrals/list.html', referrals=[], total=0, statistics={}, members=[])


@referrals_bp.route('/new')
def new_referral():
    """Show create referral form"""
    try:
        # Get members for dropdown
        members_response = requests.get(f"{API_BASE_URL}/members/")
        members = members_response.json() if members_response.ok else []

        return render_template('admin/referrals/new.html', members=members)
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "danger")
        return redirect(url_for('referrals.list_referrals'))


@referrals_bp.route('/create', methods=['POST'])
def create_referral():
    """Create a new referral"""
    try:
        referral_data = {
            'referrer_id': int(request.form.get('referrer_id')),
            'referred_name': request.form.get('referred_name'),
            'referred_contact': request.form.get('referred_contact'),
            'referred_email': request.form.get('referred_email') if request.form.get('referred_email') else None,
            'notes': request.form.get('notes') if request.form.get('notes') else None
        }

        # Remove None values
        referral_data = {k: v for k, v in referral_data.items() if v is not None and v != ''}

        # Create referral via API
        response = requests.post(f"{API_BASE_URL}/referrals", json=referral_data)
        response.raise_for_status()

        flash("Referral created successfully!", "success")
        return redirect(url_for('referrals.list_referrals'))
    except requests.exceptions.RequestException as e:
        flash(f"Error creating referral: {str(e)}", "danger")
        return redirect(url_for('referrals.new_referral'))


@referrals_bp.route('/<int:referral_id>')
def view_referral(referral_id):
    """View referral details"""
    try:
        response = requests.get(f"{API_BASE_URL}/referrals/{referral_id}")
        response.raise_for_status()
        referral = response.json()

        return render_template('admin/referrals/view.html', referral=referral)
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching referral: {str(e)}", "danger")
        return redirect(url_for('referrals.list_referrals'))


@referrals_bp.route('/<int:referral_id>/edit')
def edit_referral(referral_id):
    """Show edit referral form"""
    try:
        response = requests.get(f"{API_BASE_URL}/referrals/{referral_id}")
        response.raise_for_status()
        referral = response.json()

        # Get members for dropdown (if linking to registered member)
        members_response = requests.get(f"{API_BASE_URL}/members/")
        members = members_response.json() if members_response.ok else []

        return render_template('admin/referrals/edit.html', referral=referral, members=members)
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching referral: {str(e)}", "danger")
        return redirect(url_for('referrals.list_referrals'))


@referrals_bp.route('/<int:referral_id>/update', methods=['POST'])
def update_referral(referral_id):
    """Update a referral"""
    try:
        referral_data = {}

        if request.form.get('referred_name'):
            referral_data['referred_name'] = request.form.get('referred_name')
        if request.form.get('referred_contact'):
            referral_data['referred_contact'] = request.form.get('referred_contact')
        if request.form.get('referred_email'):
            referral_data['referred_email'] = request.form.get('referred_email')
        if request.form.get('status'):
            referral_data['status'] = request.form.get('status')
        if request.form.get('referred_member_id'):
            referral_data['referred_member_id'] = int(request.form.get('referred_member_id'))
        if request.form.get('notes'):
            referral_data['notes'] = request.form.get('notes')

        response = requests.put(f"{API_BASE_URL}/referrals/{referral_id}", json=referral_data)
        response.raise_for_status()

        flash("Referral updated successfully!", "success")
        return redirect(url_for('referrals.view_referral', referral_id=referral_id))
    except requests.exceptions.RequestException as e:
        flash(f"Error updating referral: {str(e)}", "danger")
        return redirect(url_for('referrals.edit_referral', referral_id=referral_id))


@referrals_bp.route('/<int:referral_id>/delete', methods=['POST'])
def delete_referral(referral_id):
    """Delete a referral"""
    try:
        response = requests.delete(f"{API_BASE_URL}/referrals/{referral_id}")
        response.raise_for_status()

        flash("Referral deleted successfully!", "success")
        return redirect(url_for('referrals.list_referrals'))
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting referral: {str(e)}", "danger")
        return redirect(url_for('referrals.view_referral', referral_id=referral_id))


@referrals_bp.route('/mark-contacted', methods=['POST'])
def mark_contacted():
    """Mark referrals as contacted"""
    try:
        referral_ids = request.form.getlist('referral_ids[]')
        mark_as_contacted = request.form.get('mark_as_contacted') == 'true'

        contact_data = {
            'referral_ids': [int(rid) for rid in referral_ids],
            'mark_as_contacted': mark_as_contacted
        }

        response = requests.post(f"{API_BASE_URL}/referrals/mark-contacted", json=contact_data)
        response.raise_for_status()
        result = response.json()

        flash(result.get('message', 'Status updated successfully!'), "success")
        return redirect(url_for('referrals.list_referrals'))
    except requests.exceptions.RequestException as e:
        flash(f"Error updating status: {str(e)}", "danger")
        return redirect(url_for('referrals.list_referrals'))


@referrals_bp.route('/top-referrers')
def top_referrers():
    """Show top referrers"""
    try:
        response = requests.get(f"{API_BASE_URL}/referrals/top-referrers?limit=20")
        response.raise_for_status()
        data = response.json()

        # Get overall statistics
        stats_response = requests.get(f"{API_BASE_URL}/referrals/statistics")
        stats_response.raise_for_status()
        statistics = stats_response.json()

        return render_template(
            'admin/referrals/top_referrers.html',
            top_referrers=data.get('top_referrers', []),
            statistics=statistics
        )
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching top referrers: {str(e)}", "danger")
        return redirect(url_for('referrals.list_referrals'))
