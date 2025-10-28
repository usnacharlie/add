"""
RBAC (Role-Based Access Control) Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Permission Schemas ==============

class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Role Schemas ==============

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleWithPermissions(RoleResponse):
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True


# ============== Role-Permission Schemas ==============

class RolePermissionAssign(BaseModel):
    permission_ids: List[int] = Field(..., min_items=1)


class RolePermissionRemove(BaseModel):
    permission_id: int


# ============== User-Role Schemas ==============

class UserRoleBase(BaseModel):
    user_id: int
    user_type: str = Field(..., pattern="^(admin|member)$")
    role_id: int


class UserRoleCreate(UserRoleBase):
    assigned_by: Optional[int] = None


class UserRoleResponse(UserRoleBase):
    id: int
    assigned_by: Optional[int] = None
    assigned_at: datetime
    role: RoleResponse

    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    role_id: int


class UserPermissionsResponse(BaseModel):
    user_id: int
    user_type: str
    roles: List[RoleResponse]
    permissions: List[PermissionResponse]


# ============== List Response Schemas ==============

class RoleListResponse(BaseModel):
    total: int
    roles: List[RoleResponse]


class PermissionListResponse(BaseModel):
    total: int
    permissions: List[PermissionResponse]


class UserRoleListResponse(BaseModel):
    total: int
    user_roles: List[UserRoleResponse]
