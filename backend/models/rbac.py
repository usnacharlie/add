"""
Role-Based Access Control (RBAC) Models
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Role(Base):
    """Roles table for RBAC"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """Permissions table for RBAC"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)  # e.g., 'members', 'events', 'roles'
    action = Column(String(50), nullable=False, index=True)    # e.g., 'create', 'read', 'update', 'delete'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_resource_action'),
    )

    def __repr__(self):
        return f"<Permission {self.resource}.{self.action}>"


class RolePermission(Base):
    """Role-Permission mapping table"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    def __repr__(self):
        return f"<RolePermission role_id={self.role_id} permission_id={self.permission_id}>"


class UserRole(Base):
    """User-Role mapping table (for both admins and members)"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(20), nullable=False, index=True)  # 'admin' or 'member'
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(Integer, nullable=True)  # ID of user who assigned this role
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    role = relationship("Role", back_populates="user_roles")

    __table_args__ = (
        UniqueConstraint('user_id', 'user_type', 'role_id', name='uq_user_role'),
    )

    def __repr__(self):
        return f"<UserRole {self.user_type}:{self.user_id} role_id={self.role_id}>"
