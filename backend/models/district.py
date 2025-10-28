"""
District model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    province_id = Column(Integer, ForeignKey("provinces.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    province = relationship("Province", back_populates="districts")
    constituencies = relationship("Constituency", back_populates="district", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<District(id={self.id}, name='{self.name}', province_id={self.province_id})>"
