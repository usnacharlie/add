"""
User model for system authentication
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.config.database import Base


class User(Base):
    """System user model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(50), unique=True, nullable=True, index=True)
    pin_hash = Column(String(255), nullable=False)  # Hashed PIN
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="member")  # admin, coordinator, member, viewer
    is_active = Column(Boolean, default=True)

    # Optional link to member record
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    member = relationship("Member", backref="user_account")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email} - {self.role}>"
