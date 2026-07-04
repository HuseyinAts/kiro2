"""
Soru Meydani (Question Plaza) Models — F1 Social Feature

Tablolar:
- forum_questions: Ogrenci tarafindan sorulan sorular
- forum_solutions: Cozum onerisi (gorsel/metin)
- forum_votes: Cozume verilen oy (helpful/not-helpful)
- forum_badges: Soru/cozum rozetleri

Kurallar:
- Soru 1 konu/alt-konu ile baglidir
- Cozum oneri eden kullanici soru sorandan FARKLI olmali
- Oy: kullanici basina cozum basina 1 kez
- Yonlendirmeli soru sablonlari (free text yok)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: forum_questions
# ---------------------------------------------------------------------------


class ForumQuestion(Base):
    """Ogrencinin sordugu soru — belirli bir konu/soru baglantili."""

    __tablename__ = "forum_questions"

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
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Hangi soru bankasi sorusu hakkinda (opsiyonel)
    question_bank_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    # Konu/alt-konu
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Sablon-bazli soru tipi
    question_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="how_to_solve"
    )
    # Soru metni (max 500 karakter, sablon + parametre)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", index=True
    )
    solution_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_solution_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # XP
    xp_awarded: Mapped[bool] = mapped_column(Boolean, default=False)
    # Moderasyon
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Table 2: forum_solutions
# ---------------------------------------------------------------------------


class ForumSolution(Base):
    """Bir forum sorusuna verilen cozum onerisi."""

    __tablename__ = "forum_solutions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    solver_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Cozum icerigi
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Oylama
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    # XP
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0)
    # Moderasyon
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 3: forum_votes
# ---------------------------------------------------------------------------


class ForumVote(Base):
    """Cozume verilen oy — kullanici basina cozum basina 1."""

    __tablename__ = "forum_votes"
    __table_args__ = (
        UniqueConstraint("voter_id", "solution_id", name="uq_forum_vote"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    voter_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    solution_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    vote_type: Mapped[str] = mapped_column(
        String(15), nullable=False
    )  # "helpful" / "not_helpful"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
