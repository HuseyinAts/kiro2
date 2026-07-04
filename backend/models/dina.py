"""
DINA Cognitive Diagnostic Models

NanoSkill, QMatrix, DINAParameter ve StudentNanoSkillMastery modelleri.
DINA (Deterministic Input Noisy AND-gate) bilişsel tanı modeli.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class NanoSkill(Base):
    """Nano beceri — atomik bilgi noktasi."""

    __tablename__ = "nano_skills"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    knowledge_point_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<NanoSkill id={self.id} name={self.name} subject={self.subject}>"


class QMatrix(Base):
    """Q-Matrix — soru ile nano beceri arasindaki iliski."""

    __tablename__ = "q_matrix"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    nano_skill_id: Mapped[str] = mapped_column(
        String, ForeignKey("nano_skills.id", ondelete="CASCADE"), nullable=False
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "question_id", "nano_skill_id", name="uq_qmatrix_question_skill"
        ),
        Index("idx_qmatrix_pair", "question_id", "nano_skill_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<QMatrix id={self.id} question={self.question_id}"
            f" skill={self.nano_skill_id}>"
        )


class DINAParameter(Base):
    """DINA model parametreleri — kayma (slip) ve tahmin (guess) olasiliklarli."""

    __tablename__ = "dina_parameters"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    slip: Mapped[float] = mapped_column(Float, default=0.1)
    guess: Mapped[float] = mapped_column(Float, default=0.2)
    calibrated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DINAParameter id={self.id} question={self.question_id}"
            f" slip={self.slip} guess={self.guess}>"
        )


class StudentNanoSkillMastery(Base):
    """Ogrencinin nano beceri ustunluk durumu."""

    __tablename__ = "student_nano_skill_mastery"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
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

    __table_args__ = (
        UniqueConstraint("student_id", "nano_skill_id", name="uq_student_nano_skill"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentNanoSkillMastery id={self.id} student={self.student_id}"
            f" skill={self.nano_skill_id} mastery={self.mastery}>"
        )
