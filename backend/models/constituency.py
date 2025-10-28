"""
Constituency model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Constituency(Base):
    __tablename__ = "constituencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    district = relationship("District", back_populates="constituencies")
    wards = relationship("Ward", back_populates="constituency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Constituency(id={self.id}, name='{self.name}', district_id={self.district_id})>"
