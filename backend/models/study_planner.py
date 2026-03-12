"""
Study Planner Models — F7
DB tables: study_plans, weekly_goals

StudyPlan: YKS hedef tarihi + olusturma/guncelleme zamanları
WeeklyGoal: Plan icindeki haftalik konu hedefleri ve ilerleme
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class StudyPlan(Base):
    """Student study plan linked to a YKS target date."""

    __tablename__ = "study_plans"
    __table_args__ = (
        Index("idx_study_plans_student", "student_id"),
        Index("idx_study_plans_active", "student_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    yks_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Plan metadata
    total_weeks = Column(Integer, default=0)
    target_net = Column(Float, nullable=True)  # optional target score

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    weekly_goals = relationship(
        "WeeklyGoal", back_populates="plan", cascade="all, delete-orphan"
    )


class WeeklyGoal(Base):
    """Per-week goal inside a study plan."""

    __tablename__ = "weekly_goals"
    __table_args__ = (
        Index("idx_weekly_goals_plan", "plan_id"),
        Index("idx_weekly_goals_week", "plan_id", "week_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(
        Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False
    )
    week_number = Column(Integer, nullable=False)  # 1-based

    # Goal definition
    topics = Column(JSON, default=list)  # list of topic IDs / names
    target_questions = Column(Integer, default=0)
    target_reviews = Column(Integer, default=0)

    # Progress tracking
    completed_questions = Column(Integer, default=0)
    completed_reviews = Column(Integer, default=0)
    accuracy_rate = Column(Float, nullable=True)  # 0.0–1.0
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plan = relationship("StudyPlan", back_populates="weekly_goals")
