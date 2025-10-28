"""
Permissions API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.config.database import get_db
from backend.models import Permission
from backend.schemas.rbac import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionListResponse
)

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):
    """
    Create a new permission
    """
    # Check if permission already exists
    existing = db.query(Permission).filter(
        Permission.resource == permission.resource,
        Permission.action == permission.action
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission '{permission.resource}.{permission.action}' already exists"
        )

    # Create new permission
    db_permission = Permission(
        name=permission.name,
        resource=permission.resource,
        action=permission.action,
        description=permission.description
    )

    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)

    return db_permission


@router.get("", response_model=PermissionListResponse)
def list_permissions(
    skip: int = 0,
    limit: int = 500,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all permissions with optional filters
    """
    query = db.query(Permission)

    # Apply filters
    if resource:
        query = query.filter(Permission.resource == resource)
    if action:
        query = query.filter(Permission.action == action)

    total = query.count()
    permissions = query.order_by(Permission.resource, Permission.action).offset(skip).limit(limit).all()

    return {"total": total, "permissions": permissions}


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(permission_id: int, db: Session = Depends(get_db)):
    """
    Get permission details
    """
    permission = db.query(Permission).filter(Permission.id == permission_id).first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with id {permission_id} not found"
        )

    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update permission description
    """
    db_permission = db.query(Permission).filter(Permission.id == permission_id).first()

    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with id {permission_id} not found"
        )

    if permission_update.description is not None:
        db_permission.description = permission_update.description

    db.commit()
    db.refresh(db_permission)

    return db_permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: int, db: Session = Depends(get_db)):
    """
    Delete a permission
    """
    db_permission = db.query(Permission).filter(Permission.id == permission_id).first()

    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with id {permission_id} not found"
        )

    db.delete(db_permission)
    db.commit()

    return None


@router.get("/resources/list", response_model=List[str])
def list_resources(db: Session = Depends(get_db)):
    """
    Get list of unique resources
    """
    resources = db.query(Permission.resource).distinct().all()
    return [r[0] for r in resources]


@router.get("/actions/list", response_model=List[str])
def list_actions(db: Session = Depends(get_db)):
    """
    Get list of unique actions
    """
    actions = db.query(Permission.action).distinct().all()
    return [a[0] for a in actions]
