"""
Event Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from datetime import datetime

events_bp = Blueprint('events', __name__, url_prefix='/events')

API_BASE_URL = "http://localhost:9500/api/v1"


@events_bp.route('/')
def list_events():
    """List all events"""
    try:
        # Get filter parameters from query string
        params = {
            'skip': request.args.get('skip', 0),
            'limit': request.args.get('limit', 100),
            'status': request.args.get('status'),
            'event_type': request.args.get('event_type'),
            'province_id': request.args.get('province_id'),
            'district_id': request.args.get('district_id'),
            'constituency_id': request.args.get('constituency_id'),
            'ward_id': request.args.get('ward_id'),
            'search': request.args.get('search')
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None and v != ''}

        # Get events from API
        response = requests.get(f"{API_BASE_URL}/events", params=params)
        response.raise_for_status()
        events_data = response.json()

        # Get statistics
        stats_response = requests.get(f"{API_BASE_URL}/events/statistics")
        stats_response.raise_for_status()
        statistics = stats_response.json()

        # Get locations for filters
        provinces_response = requests.get(f"{API_BASE_URL}/provinces")
        provinces = provinces_response.json() if provinces_response.ok else []

        return render_template(
            'admin/events/list.html',
            events=events_data.get('events', []),
            total=events_data.get('total', 0),
            statistics=statistics,
            provinces=provinces,
            filters=request.args
        )
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching events: {str(e)}", "danger")
        return render_template('admin/events/list.html', events=[], total=0, statistics={}, provinces=[])


@events_bp.route('/new')
def new_event():
    """Show create event form"""
    try:
        # Get locations for dropdowns
        provinces_response = requests.get(f"{API_BASE_URL}/provinces")
        provinces = provinces_response.json() if provinces_response.ok else []

        return render_template('admin/events/new.html', provinces=provinces)
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "danger")
        return redirect(url_for('events.list_events'))


@events_bp.route('/create', methods=['POST'])
def create_event():
    """Create a new event"""
    try:
        # Get form data
        event_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'event_type': request.form.get('event_type'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date') if request.form.get('end_date') else None,
            'location': request.form.get('location'),
            'venue': request.form.get('venue'),
            'max_attendees': int(request.form.get('max_attendees')) if request.form.get('max_attendees') else None,
            'province_id': int(request.form.get('province_id')) if request.form.get('province_id') else None,
            'district_id': int(request.form.get('district_id')) if request.form.get('district_id') else None,
            'constituency_id': int(request.form.get('constituency_id')) if request.form.get('constituency_id') else None,
            'ward_id': int(request.form.get('ward_id')) if request.form.get('ward_id') else None,
            'created_by': session.get('user_id', 1)  # Default to 1 for now
        }

        # Remove None values
        event_data = {k: v for k, v in event_data.items() if v is not None and v != ''}

        # Create event via API
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        response.raise_for_status()

        flash("Event created successfully!", "success")
        return redirect(url_for('events.list_events'))
    except requests.exceptions.RequestException as e:
        flash(f"Error creating event: {str(e)}", "danger")
        return redirect(url_for('events.new_event'))


@events_bp.route('/<int:event_id>')
def view_event(event_id):
    """View event details"""
    try:
        # Get event details
        response = requests.get(f"{API_BASE_URL}/events/{event_id}")
        response.raise_for_status()
        event = response.json()

        # Get attendees
        attendees_response = requests.get(f"{API_BASE_URL}/events/{event_id}/attendees")
        attendees_data = attendees_response.json() if attendees_response.ok else {'total': 0, 'registrations': []}

        return render_template(
            'admin/events/view.html',
            event=event,
            attendees=attendees_data.get('registrations', []),
            total_attendees=attendees_data.get('total', 0)
        )
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching event: {str(e)}", "danger")
        return redirect(url_for('events.list_events'))


@events_bp.route('/<int:event_id>/edit')
def edit_event(event_id):
    """Show edit event form"""
    try:
        # Get event details
        response = requests.get(f"{API_BASE_URL}/events/{event_id}")
        response.raise_for_status()
        event = response.json()

        # Get locations for dropdowns
        provinces_response = requests.get(f"{API_BASE_URL}/provinces")
        provinces = provinces_response.json() if provinces_response.ok else []

        return render_template('admin/events/edit.html', event=event, provinces=provinces)
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching event: {str(e)}", "danger")
        return redirect(url_for('events.list_events'))


@events_bp.route('/<int:event_id>/update', methods=['POST'])
def update_event(event_id):
    """Update an event"""
    try:
        # Get form data
        event_data = {}

        if request.form.get('title'):
            event_data['title'] = request.form.get('title')
        if request.form.get('description'):
            event_data['description'] = request.form.get('description')
        if request.form.get('event_type'):
            event_data['event_type'] = request.form.get('event_type')
        if request.form.get('start_date'):
            event_data['start_date'] = request.form.get('start_date')
        if request.form.get('end_date'):
            event_data['end_date'] = request.form.get('end_date')
        if request.form.get('location'):
            event_data['location'] = request.form.get('location')
        if request.form.get('venue'):
            event_data['venue'] = request.form.get('venue')
        if request.form.get('max_attendees'):
            event_data['max_attendees'] = int(request.form.get('max_attendees'))
        if request.form.get('status'):
            event_data['status'] = request.form.get('status')
        if request.form.get('province_id'):
            event_data['province_id'] = int(request.form.get('province_id'))
        if request.form.get('district_id'):
            event_data['district_id'] = int(request.form.get('district_id'))
        if request.form.get('constituency_id'):
            event_data['constituency_id'] = int(request.form.get('constituency_id'))
        if request.form.get('ward_id'):
            event_data['ward_id'] = int(request.form.get('ward_id'))

        # Update event via API
        response = requests.put(f"{API_BASE_URL}/events/{event_id}", json=event_data)
        response.raise_for_status()

        flash("Event updated successfully!", "success")
        return redirect(url_for('events.view_event', event_id=event_id))
    except requests.exceptions.RequestException as e:
        flash(f"Error updating event: {str(e)}", "danger")
        return redirect(url_for('events.edit_event', event_id=event_id))


@events_bp.route('/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event"""
    try:
        response = requests.delete(f"{API_BASE_URL}/events/{event_id}")
        response.raise_for_status()

        flash("Event deleted successfully!", "success")
        return redirect(url_for('events.list_events'))
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting event: {str(e)}", "danger")
        return redirect(url_for('events.view_event', event_id=event_id))


@events_bp.route('/<int:event_id>/register', methods=['GET', 'POST'])
def register_for_event(event_id):
    """Register member for event"""
    if request.method == 'POST':
        try:
            registration_data = {
                'member_id': int(request.form.get('member_id')),
                'notes': request.form.get('notes')
            }

            response = requests.post(
                f"{API_BASE_URL}/events/{event_id}/register",
                json=registration_data
            )
            response.raise_for_status()

            flash("Member registered successfully!", "success")
            return redirect(url_for('events.view_event', event_id=event_id))
        except requests.exceptions.RequestException as e:
            flash(f"Error registering member: {str(e)}", "danger")
            return redirect(url_for('events.register_for_event', event_id=event_id))

    # GET request - show registration form
    try:
        # Get event details
        event_response = requests.get(f"{API_BASE_URL}/events/{event_id}")
        event_response.raise_for_status()
        event = event_response.json()

        # Get members for dropdown
        members_response = requests.get(f"{API_BASE_URL}/members")
        members = members_response.json() if members_response.ok else []

        return render_template('admin/events/register.html', event=event, members=members)
    except requests.exceptions.RequestException as e:
        flash(f"Error loading registration form: {str(e)}", "danger")
        return redirect(url_for('events.view_event', event_id=event_id))


@events_bp.route('/<int:event_id>/mark-attendance', methods=['POST'])
def mark_attendance(event_id):
    """Mark attendance for members"""
    try:
        member_ids = request.form.getlist('member_ids[]')
        mark_as_attended = request.form.get('mark_as_attended') == 'true'

        attendance_data = {
            'member_ids': [int(mid) for mid in member_ids],
            'mark_as_attended': mark_as_attended
        }

        response = requests.post(
            f"{API_BASE_URL}/events/{event_id}/mark-attendance",
            json=attendance_data
        )
        response.raise_for_status()
        result = response.json()

        flash(result.get('message', 'Attendance marked successfully!'), "success")
        return redirect(url_for('events.view_event', event_id=event_id))
    except requests.exceptions.RequestException as e:
        flash(f"Error marking attendance: {str(e)}", "danger")
        return redirect(url_for('events.view_event', event_id=event_id))


@events_bp.route('/<int:event_id>/cancel-registration/<int:member_id>', methods=['POST'])
def cancel_registration(event_id, member_id):
    """Cancel event registration"""
    try:
        response = requests.delete(f"{API_BASE_URL}/events/{event_id}/register/{member_id}")
        response.raise_for_status()

        flash("Registration cancelled successfully!", "success")
        return redirect(url_for('events.view_event', event_id=event_id))
    except requests.exceptions.RequestException as e:
        flash(f"Error cancelling registration: {str(e)}", "danger")
        return redirect(url_for('events.view_event', event_id=event_id))
