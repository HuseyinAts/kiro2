"""Student question flag model — Faz 7.2 beta feedback mechanism.

Öğrencinin hatalı/tuhaf soru raporu. Beta launch sonrası gerçek student
feedback ile LLM-circular risk mitigasyonu için kullanılır.

Migration: alembic/versions/20260517_student_question_flags.py
API: api/student_feedback_api.py
"""

from __future__ import annotations

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class StudentQuestionFlag(Base):
    """Öğrenci tarafından raporlanmış soru hatası."""

    __tablename__ = "student_question_flags"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "question_id",
            "flag_type",
            name="uq_student_flags_user_question_type",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    flag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True, deferred=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
