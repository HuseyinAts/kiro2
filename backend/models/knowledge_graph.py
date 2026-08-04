"""
Knowledge Graph Models

KnowledgePoint, QuestionKnowledgeMapping ve StudentKnowledgeState modelleri.
On kosul DAG'i ve ogrenci hakimiyet katmani.
"""

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import (
    String,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
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

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    topic_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    name_tr: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, deferred=True)
    prerequisite_ids: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list
    , deferred=True)
    difficulty_range: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=lambda: [0.0, 1.0]
    , deferred=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<KnowledgePoint id={self.id} code={self.code} subject={self.subject}>"


class QuestionKnowledgeMapping(Base):
    """Soru ile bilgi noktasi arasindaki iliski (many-to-many)."""

    __tablename__ = "question_knowledge_mappings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    knowledge_point_id: Mapped[str] = mapped_column(String, ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "question_id", "knowledge_point_id", name="uq_question_knowledge_mapping"
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

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    student_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    knowledge_point_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float | None] = mapped_column(Float, default=0.5)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed: Mapped[datetime | None] = mapped_column(
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
