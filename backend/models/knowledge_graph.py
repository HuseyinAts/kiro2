"""
Knowledge Graph Models

KnowledgePoint, QuestionKnowledgeMapping ve StudentKnowledgeState modelleri.
On kosul DAG'i ve ogrenci hakimiyet katmani.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class KnowledgePoint(Base):
    """Bilgi noktasi — on kosul DAG'inin bir dugumu."""

    __tablename__ = "knowledge_points"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # On kosul bilgi noktasi ID'leri listesi
    prerequisite_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # [min, max] zorluk araligi
    difficulty_range: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<KnowledgePoint id={self.id} name={self.name} subject={self.subject}>"


class QuestionKnowledgeMapping(Base):
    """Soru ile bilgi noktasi arasindaki iliski (many-to-many)."""

    __tablename__ = "question_knowledge_mappings"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    knowledge_point_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Sorunun bu bilgi noktasini olcme agirligi (0-1)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "question_id", "knowledge_point_id", name="uq_question_knowledge_point"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionKnowledgeMapping id={self.id}"
            f" question={self.question_id} kp={self.knowledge_point_id}>"
        )


class StudentKnowledgeState(Base):
    """Ogrencinin bir bilgi noktasindaki hakimiyet durumu."""

    __tablename__ = "student_knowledge_states"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    knowledge_point_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=0.5)
    last_assessed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "knowledge_point_id", name="uq_student_knowledge_state"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentKnowledgeState id={self.id} student={self.student_id}"
            f" kp={self.knowledge_point_id} mastery={self.mastery_level}>"
        )
