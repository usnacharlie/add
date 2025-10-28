"""
Ward model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    constituency = relationship("Constituency", back_populates="wards")
    members = relationship("Member", back_populates="ward", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ward(id={self.id}, name='{self.name}', constituency_id={self.constituency_id})>"
