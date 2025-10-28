"""
Member model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from backend.config.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    gender = Column(String(10), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)  # Keep for backward compatibility, can be calculated
    nrc = Column(String(50), nullable=True, index=True)  # National Registration Card
    voters_id = Column(String(50), nullable=True, index=True)
    contact = Column(String(50), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ward = relationship("Ward", back_populates="members")

    @property
    def calculated_age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        return self.age  # Fallback to stored age if no DOB

    def __repr__(self):
        return f"<Member(id={self.id}, name='{self.name}', nrc='{self.nrc}')>"
