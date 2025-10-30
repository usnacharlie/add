"""
USSD Session model for tracking USSD interactions
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime
from backend.config.database import Base


class USSDSession(Base):
    """USSD Session model for managing USSD state"""
    __tablename__ = "ussd_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(50), nullable=False, index=True)
    current_step = Column(String(100), nullable=False)
    session_data = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<USSDSession {self.session_id} - {self.phone_number}>"
