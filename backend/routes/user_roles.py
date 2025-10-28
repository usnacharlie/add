"""
User Roles API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from backend.config.database import get_db
from backend.models import UserRole, Role, RolePermission, Permission
from backend.schemas.rbac import (
    UserRoleCreate, UserRoleResponse, UserRoleAssign,
    UserPermissionsResponse, UserRoleListResponse
)

router = APIRouter(prefix="/user-roles", tags=["User Roles"])


@router.post("", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def assign_role_to_user(user_role: UserRoleCreate, db: Session = Depends(get_db)):
    """
    Assign a role to a user
    """
    # Verify role exists
    role = db.query(Role).filter(Role.id == user_role.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {user_role.role_id} not found"
        )

    # Check if assignment already exists
    existing = db.query(UserRole).filter(
        UserRole.user_id == user_role.user_id,
        UserRole.user_type == user_role.user_type,
        UserRole.role_id == user_role.role_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has this role assigned"
        )

    # Create assignment
    db_user_role = UserRole(
        user_id=user_role.user_id,
        user_type=user_role.user_type,
        role_id=user_role.role_id,
        assigned_by=user_role.assigned_by
    )

    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)

    # Load role relationship
    db_user_role = db.query(UserRole).options(joinedload(UserRole.role)).filter(
        UserRole.id == db_user_role.id
    ).first()

    return db_user_role


@router.get("/user/{user_id}/{user_type}", response_model=UserRoleListResponse)
def get_user_roles(user_id: int, user_type: str, db: Session = Depends(get_db)):
    """
    Get all roles assigned to a user
    """
    if user_type not in ['admin', 'member']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_type must be 'admin' or 'member'"
        )

    user_roles = db.query(UserRole).options(joinedload(UserRole.role)).filter(
        UserRole.user_id == user_id,
        UserRole.user_type == user_type
    ).all()

    return {"total": len(user_roles), "user_roles": user_roles}


@router.get("/user/{user_id}/{user_type}/permissions", response_model=UserPermissionsResponse)
def get_user_permissions(user_id: int, user_type: str, db: Session = Depends(get_db)):
    """
    Get all effective permissions for a user (from all their roles)
    """
    if user_type not in ['admin', 'member']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_type must be 'admin' or 'member'"
        )

    # Get user's roles
    user_roles = db.query(UserRole).options(joinedload(UserRole.role)).filter(
        UserRole.user_id == user_id,
        UserRole.user_type == user_type
    ).all()

    if not user_roles:
        return {
            "user_id": user_id,
            "user_type": user_type,
            "roles": [],
            "permissions": []
        }

    # Get all role IDs
    role_ids = [ur.role_id for ur in user_roles]

    # Get all permissions for these roles
    role_permissions = db.query(RolePermission).options(
        joinedload(RolePermission.permission)
    ).filter(RolePermission.role_id.in_(role_ids)).all()

    # Deduplicate permissions
    permissions_dict = {}
    for rp in role_permissions:
        if rp.permission_id not in permissions_dict:
            permissions_dict[rp.permission_id] = rp.permission

    return {
        "user_id": user_id,
        "user_type": user_type,
        "roles": [ur.role for ur in user_roles],
        "permissions": list(permissions_dict.values())
    }


@router.delete("/user/{user_id}/{user_type}/role/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role_from_user(user_id: int, user_type: str, role_id: int, db: Session = Depends(get_db)):
    """
    Remove a role from a user
    """
    if user_type not in ['admin', 'member']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_type must be 'admin' or 'member'"
        )

    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.user_type == user_type,
        UserRole.role_id == role_id
    ).first()

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role assignment not found"
        )

    db.delete(user_role)
    db.commit()

    return None


@router.post("/user/{user_id}/{user_type}/assign", response_model=UserRoleResponse)
def quick_assign_role(
    user_id: int,
    user_type: str,
    role_assign: UserRoleAssign,
    assigned_by: int = None,
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to assign a role to a user
    """
    user_role_data = UserRoleCreate(
        user_id=user_id,
        user_type=user_type,
        role_id=role_assign.role_id,
        assigned_by=assigned_by
    )

    return assign_role_to_user(user_role_data, db)
