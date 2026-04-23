"""
Leaderboard Entry Model - Task 91
Liderlik tablosu giriş modeli (opsiyonel - Redis kullanımı tercih edilir)
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base


class LeaderboardEntry(Base):
    """Liderlik tablosu girişi (snapshot amaçlı)"""

    __tablename__ = "leaderboard_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Liderlik tablosu bilgileri
    leaderboard_type = Column(
        String(50), nullable=False
    )  # global, weekly, monthly, etc.
    period = Column(String(50), nullable=False)  # 2025-01, 2025-W42, etc.

    # Skor bilgileri
    score = Column(Integer, nullable=False, default=0)
    rank = Column(Integer, nullable=True)

    # Zaman damgaları
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = relationship("User")

    # Composite index for efficient queries
    __table_args__ = (
        Index(
            "idx_leaderboard_type_period_score", "leaderboard_type", "period", "score"
        ),
        Index("idx_user_leaderboard_period", "user_id", "leaderboard_type", "period"),
    )

    def __repr__(self):
        return f"<LeaderboardEntry(user_id={self.user_id}, type={self.leaderboard_type}, rank={self.rank})>"

    def to_dict(self):
        """Dictionary representation"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "leaderboard_type": self.leaderboard_type,
            "period": self.period,
            "score": self.score,
            "rank": self.rank,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    class Config:
        from_attributes = True
