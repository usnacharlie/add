"""
Province model
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Province(Base):
    __tablename__ = "provinces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    districts = relationship("District", back_populates="province", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Province(id={self.id}, name='{self.name}')>"
