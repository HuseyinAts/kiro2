"""
Student Goal ORM Model - Dashboard Service
Part of Mock Data Cleanup Phase 2
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base


class StudentGoal(Base):
    """Student goal tracking model for dashboard"""

    __tablename__ = "student_goals"

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
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    @property
    def is_completed(self) -> bool:
        """Check if goal is completed"""
        return self.status == "tamamlandi" or self.current_value >= self.target_value

    @property
    def is_active(self) -> bool:
        """Check if goal is currently active"""
        now = datetime.utcnow()
        return (
            self.status == "aktif"
            and self.start_date <= now <= self.end_date
        )
