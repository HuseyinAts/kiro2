"""
Task 92.3: Streak Tracking Model
Ardışık doğru cevap takibi
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class StreakTracking(Base):
    """Seri takip modeli"""

    __tablename__ = "streak_tracking"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Current streak
    current_streak = Column(Integer, default=0, nullable=False)
    best_streak = Column(Integer, default=0, nullable=False)

    # Streak metadata
    streak_start_date = Column(DateTime, nullable=True)
    last_correct_answer = Column(DateTime, nullable=True)

    # Milestones reached
    milestones_reached = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="streak_tracking")

    def __repr__(self):
        return f"<StreakTracking(user_id={self.user_id}, current={self.current_streak}, best={self.best_streak})>"

    def to_dict(self):
        """Dictionary representation"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "streak_start_date": self.streak_start_date.isoformat()
            if self.streak_start_date
            else None,
            "last_correct_answer": self.last_correct_answer.isoformat()
            if self.last_correct_answer
            else None,
            "milestones_reached": self.milestones_reached or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PerformanceHistory(Base):
    """Performans geçmişi modeli"""

    __tablename__ = "performance_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Performance data
    score = Column(Integer, nullable=False)  # 0-100
    questions_answered = Column(Integer, default=1)
    correct_answers = Column(Integer, default=0)

    # Context
    subject = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True)

    # Streak at time
    streak_at_time = Column(Integer, default=0)

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="performance_history")

    def __repr__(self):
        return f"<PerformanceHistory(user_id={self.user_id}, score={self.score})>"

    def to_dict(self):
        """Dictionary representation"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "score": self.score,
            "questions_answered": self.questions_answered,
            "correct_answers": self.correct_answers,
            "subject": self.subject,
            "difficulty": self.difficulty,
            "streak_at_time": self.streak_at_time,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
