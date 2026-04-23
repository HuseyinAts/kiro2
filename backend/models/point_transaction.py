"""
Point Transaction Model - Puan İşlem Kaydı

Bu model, kullanıcıların puan kazanma işlemlerini kaydeder.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class PointTransaction(Base):
    """Puan işlem kaydı modeli"""

    __tablename__ = "point_transactions"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    meta_data = Column(JSON, nullable=True)  # Ek bilgiler için
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="point_transactions")

    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id={self.user_id}, points={self.points}, reason='{self.reason}')>"

    def to_dict(self):
        """Model'i dictionary'ye çevir"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "points": self.points,
            "reason": self.reason,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
