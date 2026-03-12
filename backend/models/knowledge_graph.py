"""
Knowledge Graph Models — F4
Granular knowledge points with prerequisite DAG structure.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class KnowledgePoint(Base):
    """A granular knowledge node, e.g. 'MAT.FUNC.LIM.01' (limit of a function).

    prerequisite_ids stores a JSON list of other KnowledgePoint ids that must be
    mastered before this one — forming a directed acyclic prerequisite graph.
    """

    __tablename__ = "knowledge_points"
    __table_args__ = (
        Index("idx_kp_topic", "topic_id"),
        Index("idx_kp_subject", "subject"),
        Index("idx_kp_code", "code", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Soft FK — no constraint because topics table structure varies across legacy models
    topic_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Dot-notation code: "MAT.FUNC.LIM.01"
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name_tr: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    # JSON list of KnowledgePoint ids that are prerequisites
    prerequisite_ids: Mapped[list] = mapped_column(JSON, default=list)
    # [min_difficulty, max_difficulty] in IRT theta scale
    difficulty_range: Mapped[list] = mapped_column(JSON, default=lambda: [0.0, 1.0])
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QuestionKnowledgeMapping(Base):
    """Maps a question to the knowledge points it assesses.

    A question may require multiple knowledge points; is_primary marks the
    dominant one used for adaptive routing.
    """

    __tablename__ = "question_knowledge_mappings"
    __table_args__ = (
        Index("idx_qkm_question", "question_id"),
        Index("idx_qkm_knowledge_point", "knowledge_point_id"),
        UniqueConstraint(
            "question_id", "knowledge_point_id",
            name="uq_question_knowledge_mapping",
        ),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    knowledge_point_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StudentKnowledgeState(Base):
    """Per-student mastery estimate for each knowledge point.

    mastery_level (0–1) and confidence are updated after each response.
    """

    __tablename__ = "student_knowledge_states"
    __table_args__ = (
        Index("idx_sks_student", "student_id"),
        Index("idx_sks_knowledge_point", "knowledge_point_id"),
        UniqueConstraint(
            "student_id", "knowledge_point_id",
            name="uq_student_knowledge_state",
        ),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    knowledge_point_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)  # 0–1 range
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
