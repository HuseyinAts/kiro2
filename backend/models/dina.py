"""
DINA Model Tables — F11
Deterministic Input, Noisy "And" gate cognitive diagnostic model.
Tables: nano_skills, q_matrix, dina_parameters
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class NanoSkill(Base):
    """A fine-grained skill node within a knowledge point."""

    __tablename__ = "nano_skills"
    __table_args__ = (
        Index("idx_nano_skill_kp", "knowledge_point_id"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    knowledge_point_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QMatrix(Base):
    """Q-Matrix: maps questions to required nano-skills."""

    __tablename__ = "q_matrix"
    __table_args__ = (
        Index("idx_qmatrix_question", "question_id"),
        Index("idx_qmatrix_skill", "nano_skill_id"),
        Index("idx_qmatrix_pair", "question_id", "nano_skill_id", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    nano_skill_id: Mapped[str] = mapped_column(
        String, ForeignKey("nano_skills.id", ondelete="CASCADE"), nullable=False
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DINAParameter(Base):
    """DINA item parameters: slip and guess probabilities."""

    __tablename__ = "dina_parameters"
    __table_args__ = (
        Index("idx_dina_question", "question_id", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    slip: Mapped[float] = mapped_column(Float, default=0.1)
    guess: Mapped[float] = mapped_column(Float, default=0.2)

    calibrated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StudentNanoSkillMastery(Base):
    """Per-student mastery estimate for each nano-skill."""

    __tablename__ = "student_nano_skill_mastery"
    __table_args__ = (
        Index("idx_snsm_student", "student_id"),
        Index("idx_snsm_skill", "nano_skill_id"),
        Index("idx_snsm_pair", "student_id", "nano_skill_id", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    nano_skill_id: Mapped[str] = mapped_column(
        String, ForeignKey("nano_skills.id", ondelete="CASCADE"), nullable=False
    )
    mastery: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    response_count: Mapped[int] = mapped_column(Integer, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
