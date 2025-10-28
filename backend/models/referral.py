"""
Referral Management Models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base


class Referral(Base):
    """Referrals table - tracks member referrals"""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=True, index=True)

    # Referral details
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    referred_name = Column(String(200), nullable=False)
    referred_contact = Column(String(50), nullable=False)
    referred_email = Column(String(100), nullable=True)

    # Status tracking
    status = Column(String(20), default='pending', index=True)  # 'pending', 'contacted', 'registered', 'expired', 'declined'
    notes = Column(Text, nullable=True)

    # Timestamps
    referred_date = Column(DateTime(timezone=True), server_default=func.now())
    contacted_date = Column(DateTime(timezone=True), nullable=True)
    registered_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    referrer = relationship("Member", foreign_keys=[referrer_id], backref="referrals_made")
    referred_member = relationship("Member", foreign_keys=[referred_member_id], backref="referred_by")

    def __repr__(self):
        return f"<Referral referrer_id={self.referrer_id} referred={self.referred_name}>"
