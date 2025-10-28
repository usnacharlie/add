"""
Roles management routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import requests

roles_bp = Blueprint('roles', __name__, url_prefix='/admin/roles')

# Backend API URL
BACKEND_URL = "http://localhost:9500/api/v1"


@roles_bp.route('/')
def list_roles():
    """List all roles"""
    try:
        response = requests.get(f"{BACKEND_URL}/roles")
        response.raise_for_status()
        data = response.json()

        return render_template('admin/roles/list.html',
                             roles=data.get('roles', []),
                             total=data.get('total', 0))
    except Exception as e:
        flash(f'Error loading roles: {str(e)}', 'danger')
        return render_template('admin/roles/list.html', roles=[], total=0)


@roles_bp.route('/new', methods=['GET', 'POST'])
def create_role():
    """Create new role"""
    if request.method == 'POST':
        try:
            role_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description')
            }

            response = requests.post(f"{BACKEND_URL}/roles", json=role_data)
            response.raise_for_status()

            flash('Role created successfully!', 'success')
            return redirect(url_for('roles.list_roles'))

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Error creating role: {error_detail}', 'danger')
        except Exception as e:
            flash(f'Error creating role: {str(e)}', 'danger')

    return render_template('admin/roles/new.html')


@roles_bp.route('/<int:role_id>')
def view_role(role_id):
    """View role details with permissions"""
    try:
        response = requests.get(f"{BACKEND_URL}/roles/{role_id}")
        response.raise_for_status()
        role = response.json()

        return render_template('admin/roles/view.html', role=role)
    except Exception as e:
        flash(f'Error loading role: {str(e)}', 'danger')
        return redirect(url_for('roles.list_roles'))


@roles_bp.route('/<int:role_id>/edit', methods=['GET', 'POST'])
def edit_role(role_id):
    """Edit role"""
    if request.method == 'POST':
        try:
            role_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description')
            }

            response = requests.put(f"{BACKEND_URL}/roles/{role_id}", json=role_data)
            response.raise_for_status()

            flash('Role updated successfully!', 'success')
            return redirect(url_for('roles.view_role', role_id=role_id))

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Error updating role: {error_detail}', 'danger')
        except Exception as e:
            flash(f'Error updating role: {str(e)}', 'danger')

    # Get role data
    try:
        response = requests.get(f"{BACKEND_URL}/roles/{role_id}")
        response.raise_for_status()
        role = response.json()

        return render_template('admin/roles/edit.html', role=role)
    except Exception as e:
        flash(f'Error loading role: {str(e)}', 'danger')
        return redirect(url_for('roles.list_roles'))


@roles_bp.route('/<int:role_id>/delete', methods=['POST'])
def delete_role(role_id):
    """Delete role"""
    try:
        response = requests.delete(f"{BACKEND_URL}/roles/{role_id}")
        response.raise_for_status()

        flash('Role deleted successfully!', 'success')
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get('detail', str(e))
        flash(f'Error deleting role: {error_detail}', 'danger')
    except Exception as e:
        flash(f'Error deleting role: {str(e)}', 'danger')

    return redirect(url_for('roles.list_roles'))


@roles_bp.route('/<int:role_id>/permissions', methods=['GET', 'POST'])
def manage_permissions(role_id):
    """Manage role permissions"""
    if request.method == 'POST':
        try:
            # Get selected permission IDs
            permission_ids = request.form.getlist('permissions')
            permission_ids = [int(pid) for pid in permission_ids]

            # Get current role permissions
            role_response = requests.get(f"{BACKEND_URL}/roles/{role_id}")
            role_response.raise_for_status()
            role = role_response.json()

            current_permission_ids = [p['id'] for p in role.get('permissions', [])]

            # Determine which permissions to add and remove
            to_add = [pid for pid in permission_ids if pid not in current_permission_ids]
            to_remove = [pid for pid in current_permission_ids if pid not in permission_ids]

            # Add new permissions
            if to_add:
                add_response = requests.post(
                    f"{BACKEND_URL}/roles/{role_id}/permissions",
                    json={'permission_ids': to_add}
                )
                add_response.raise_for_status()

            # Remove permissions
            for pid in to_remove:
                remove_response = requests.delete(
                    f"{BACKEND_URL}/roles/{role_id}/permissions/{pid}"
                )
                remove_response.raise_for_status()

            flash('Permissions updated successfully!', 'success')
            return redirect(url_for('roles.view_role', role_id=role_id))

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get('detail', str(e))
            flash(f'Error updating permissions: {error_detail}', 'danger')
        except Exception as e:
            flash(f'Error updating permissions: {str(e)}', 'danger')

    # Get role and all permissions
    try:
        # Get role with current permissions
        role_response = requests.get(f"{BACKEND_URL}/roles/{role_id}")
        role_response.raise_for_status()
        role = role_response.json()

        # Get all available permissions
        perms_response = requests.get(f"{BACKEND_URL}/permissions?limit=500")
        perms_response.raise_for_status()
        all_permissions = perms_response.json().get('permissions', [])

        # Group permissions by resource
        permissions_by_resource = {}
        for perm in all_permissions:
            resource = perm['resource']
            if resource not in permissions_by_resource:
                permissions_by_resource[resource] = []
            permissions_by_resource[resource].append(perm)

        # Get current permission IDs
        current_permission_ids = [p['id'] for p in role.get('permissions', [])]

        return render_template('admin/roles/permissions.html',
                             role=role,
                             permissions_by_resource=permissions_by_resource,
                             current_permission_ids=current_permission_ids)
    except Exception as e:
        flash(f'Error loading permissions: {str(e)}', 'danger')
        return redirect(url_for('roles.list_roles'))
