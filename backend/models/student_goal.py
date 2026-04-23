"""
Student Goal ORM Model - Dashboard Service
Part of Mock Data Cleanup Phase 2
"""
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from .base import Base


class StudentGoal(Base):
    """Student goal tracking model for dashboard"""

    __tablename__ = "student_goals"
    __table_args__ = {'extend_existing': True}

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Goal Data
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String(20), nullable=False)  # 'gunluk', 'haftalik', 'aylik'
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Status
    status = Column(String(20), default="aktif")  # 'aktif', 'tamamlandi', 'iptal'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (optional - if User model exists)
    # user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<StudentGoal(id={self.id}, user={self.user_id}, title={self.title}, status={self.status})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate goal progress percentage"""
        target = float(self.target_value or 0)
        current = float(self.current_value or 0)
        if target == 0:
            return 0.0
        return min(100.0, (current / target) * 100)

    @property
    def is_completed(self) -> bool:
        """Check if goal is completed"""
        current = float(self.current_value or 0)
        target = float(self.target_value or 0)
        return bool(self.status == "tamamlandi" or current >= target)

    @property
    def is_active(self) -> bool:
        """Check if goal is currently active"""
        now = datetime.now(UTC)
        if self.start_date is None or self.end_date is None:
            return self.status == "aktif"
        return bool(
            self.status == "aktif"
            and self.start_date <= now <= self.end_date
        )
