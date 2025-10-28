"""
Roles API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from backend.config.database import get_db
from backend.models import Role, Permission, RolePermission
from backend.schemas.rbac import (
    RoleCreate, RoleUpdate, RoleResponse, RoleWithPermissions,
    RoleListResponse, RolePermissionAssign
)

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """
    Create a new role
    """
    # Check if role name already exists
    existing_role = db.query(Role).filter(Role.name == role.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role.name}' already exists"
        )

    # Create new role
    db_role = Role(
        name=role.name,
        description=role.description,
        is_system_role=False
    )

    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    return db_role


@router.get("", response_model=RoleListResponse)
def list_roles(
    skip: int = 0,
    limit: int = 100,
    include_system: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all roles
    """
    query = db.query(Role)

    if not include_system:
        query = query.filter(Role.is_system_role == False)

    total = query.count()
    roles = query.offset(skip).limit(limit).all()

    return {"total": total, "roles": roles}


@router.get("/{role_id}", response_model=RoleWithPermissions)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """
    Get role details with permissions
    """
    role = db.query(Role).options(
        joinedload(Role.permissions).joinedload(RolePermission.permission)
    ).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )

    # Format response with permissions
    role_data = {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "created_at": role.created_at,
        "updated_at": role.updated_at,
        "permissions": [rp.permission for rp in role.permissions]
    }

    return role_data


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_update: RoleUpdate, db: Session = Depends(get_db)):
    """
    Update role details
    """
    db_role = db.query(Role).filter(Role.id == role_id).first()

    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )

    # Prevent updating system roles
    if db_role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system roles"
        )

    # Check if new name conflicts with existing role
    if role_update.name and role_update.name != db_role.name:
        existing = db.query(Role).filter(Role.name == role_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_update.name}' already exists"
            )
        db_role.name = role_update.name

    if role_update.description is not None:
        db_role.description = role_update.description

    db.commit()
    db.refresh(db_role)

    return db_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """
    Delete a role
    """
    db_role = db.query(Role).filter(Role.id == role_id).first()

    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )

    # Prevent deleting system roles
    if db_role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles"
        )

    db.delete(db_role)
    db.commit()

    return None


@router.post("/{role_id}/permissions", response_model=RoleWithPermissions)
def assign_permissions_to_role(
    role_id: int,
    permission_data: RolePermissionAssign,
    db: Session = Depends(get_db)
):
    """
    Assign permissions to a role
    """
    db_role = db.query(Role).filter(Role.id == role_id).first()

    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )

    # Prevent modifying system roles
    if db_role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system role permissions"
        )

    # Verify all permissions exist
    permissions = db.query(Permission).filter(
        Permission.id.in_(permission_data.permission_ids)
    ).all()

    if len(permissions) != len(permission_data.permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permission IDs are invalid"
        )

    # Add permissions (skip duplicates)
    for permission_id in permission_data.permission_ids:
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()

        if not existing:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            db.add(role_permission)

    db.commit()

    # Return updated role with permissions
    return get_role(role_id, db)


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a permission from a role
    """
    db_role = db.query(Role).filter(Role.id == role_id).first()

    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )

    # Prevent modifying system roles
    if db_role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system role permissions"
        )

    role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()

    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission {permission_id} not assigned to role {role_id}"
        )

    db.delete(role_permission)
    db.commit()

    return None
