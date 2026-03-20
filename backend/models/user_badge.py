"""
User Badge Model - Task 91
Kullanıcı rozet ilişkisi modeli
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import Base


class UserBadge(Base):
    """Kullanıcı rozet ilişkisi"""

    __tablename__ = "user_badges"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(String(100), nullable=False, index=True)  # Badge definition ID

    # Kazanılma bilgileri
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    auto_awarded = Column(Boolean, default=True)  # Otomatik mi kazanıldı

    # İlişkiler
    user = relationship("User", back_populates="badges")

    def __repr__(self):
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id})>"

    def to_dict(self):
        """Dictionary representation"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "badge_id": self.badge_id,
            "earned_at": self.earned_at.isoformat() if self.earned_at else None,
            "auto_awarded": self.auto_awarded,
        }

    class Config:
        from_attributes = True
