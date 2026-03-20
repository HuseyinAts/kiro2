"""
YKS Soru Üretim DB Modelleri - Generation tracking, embeddings, human feedback.

Task 9: pgvector + YKS tabloları
- GenerationRun: Üretim çalıştırma kayıtları (audit trail)
- GeneratedQuestion: SOLO/Marzano etiketli üretilmiş sorular
- QuestionEmbedding: pgvector ile embedding benzerlik araması
- HumanFeedback: İnsan değerlendirme kayıtları
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GenerationStatus(enum.Enum):
    """Üretim durumu."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SOLOLevel(enum.Enum):
    """SOLO taxonomy seviyeleri."""

    PRESTRUCTURAL = "prestructural"
    UNISTRUCTURAL = "uni"
    MULTISTRUCTURAL = "multi"
    RELATIONAL = "relational"
    EXTENDED_ABSTRACT = "extended_abstract"


class MarzanoLevel(enum.Enum):
    """Marzano bilişsel seviyeler."""

    RETRIEVAL = "retrieval"
    COMPREHENSION = "comprehension"
    ANALYSIS = "analysis"
    UTILIZATION = "utilization"
    METACOGNITIVE = "metacognitive"
    SELF_SYSTEM = "self_system"


class FeedbackVerdict(enum.Enum):
    """İnsan değerlendirme sonucu."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


# ---------------------------------------------------------------------------
# GenerationRun - Üretim çalıştırma kayıtları
# ---------------------------------------------------------------------------


class GenerationRun(Base):
    """Soru üretim çalıştırma kaydı (audit trail)."""

    __tablename__ = "yks_generation_runs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Üretim parametreleri
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(200))
    target_difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    target_solo: Mapped[Optional[str]] = mapped_column(String(30))
    target_count: Mapped[int] = mapped_column(Integer, default=1)

    # Model bilgisi
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_params: Mapped[Optional[dict]] = mapped_column(JSON)

    # Durum
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus), default=GenerationStatus.PENDING
    )
    generated_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)

    # Maliyet
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Hata bilgisi
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Zaman
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İlişkiler
    questions: Mapped[List["GeneratedQuestion"]] = relationship(
        "GeneratedQuestion", back_populates="generation_run"
    )

    __table_args__ = (
        Index("idx_genrun_status", "status"),
        Index("idx_genrun_exam", "exam_type"),
        Index("idx_genrun_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# GeneratedQuestion - SOLO/Marzano etiketli üretilmiş sorular
# ---------------------------------------------------------------------------


class GeneratedQuestion(Base):
    """AI tarafından üretilmiş soru kaydı."""

    __tablename__ = "yks_generated_questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Üretim ilişkisi
    generation_run_id: Mapped[str] = mapped_column(
        String, ForeignKey("yks_generation_runs.id", ondelete="CASCADE"), nullable=False
    )

    # Soru bankası ilişkisi (kabul edilirse)
    question_bank_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="SET NULL")
    )

    # Soru içeriği
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"A":..,"B":..}
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Sınıflandırma
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(200))

    # Taxonomy etiketleri
    solo_label: Mapped[Optional[str]] = mapped_column(String(30))
    solo_confidence: Mapped[Optional[float]] = mapped_column(Float)
    marzano_label: Mapped[Optional[str]] = mapped_column(String(30))
    marzano_confidence: Mapped[Optional[float]] = mapped_column(Float)
    bloom_level: Mapped[Optional[int]] = mapped_column(Integer)

    # IRT parametreleri (tahmini)
    irt_difficulty: Mapped[Optional[float]] = mapped_column(Float)
    irt_discrimination: Mapped[Optional[float]] = mapped_column(Float)
    irt_guessing: Mapped[Optional[float]] = mapped_column(Float)

    # Kalite
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    judge_verdict: Mapped[Optional[str]] = mapped_column(String(20))  # accept/reject
    judge_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    copy_risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Durum
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Zaman
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İlişkiler
    generation_run: Mapped["GenerationRun"] = relationship(
        "GenerationRun", back_populates="questions"
    )
    feedbacks: Mapped[List["HumanFeedback"]] = relationship(
        "HumanFeedback", back_populates="question"
    )

    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D', 'E')",
            name="check_gen_correct_answer",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 100.0",
            name="check_gen_quality",
        ),
        CheckConstraint(
            "copy_risk_score >= 0.0 AND copy_risk_score <= 1.0",
            name="check_gen_copy_risk",
        ),
        Index("idx_genq_run", "generation_run_id"),
        Index("idx_genq_exam", "exam_type"),
        Index("idx_genq_solo", "solo_label"),
        Index("idx_genq_accepted", "is_accepted"),
        Index("idx_genq_quality", "quality_score"),
    )


# ---------------------------------------------------------------------------
# QuestionEmbedding - pgvector tabanlı benzerlik araması
# ---------------------------------------------------------------------------


class QuestionEmbedding(Base):
    """Soru embedding'leri - pgvector ile benzerlik araması.

    pgvector extension gerektirir:
        CREATE EXTENSION IF NOT EXISTS vector;

    Embedding boyutu 768 (sentence-transformers varsayılan).
    HNSW indeks ile hızlı cosine similarity araması.
    """

    __tablename__ = "yks_question_embeddings"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Kaynak soru (üretilmiş veya mevcut)
    generated_question_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("yks_generated_questions.id", ondelete="CASCADE")
    )
    question_bank_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE")
    )

    # Embedding verisi - pgvector kullanılacak
    # NOT: SQLAlchemy'de pgvector.Vector tipi kullanımı için
    # pgvector Python paketi gerekli: pip install pgvector
    # Aşağıda raw SQL ile oluşturulacak, burada metadata olarak tutuyoruz
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, default=768)

    # Metin hash (duplicate detection için)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Zaman
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_emb_gen_q", "generated_question_id"),
        Index("idx_emb_bank_q", "question_bank_id"),
        UniqueConstraint("text_hash", "embedding_model", name="uq_emb_text_model"),
    )


# ---------------------------------------------------------------------------
# HumanFeedback - İnsan değerlendirme kayıtları
# ---------------------------------------------------------------------------


class HumanFeedback(Base):
    """İnsan tarafından yapılan soru değerlendirmesi."""

    __tablename__ = "yks_human_feedback"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    question_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("yks_generated_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )

    # Değerlendirme
    verdict: Mapped[FeedbackVerdict] = mapped_column(
        Enum(FeedbackVerdict), nullable=False
    )
    quality_rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    difficulty_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5

    # Detay
    comments: Mapped[Optional[str]] = mapped_column(Text)
    suggested_edits: Mapped[Optional[dict]] = mapped_column(JSON)

    # Kategorik feedback
    issues: Mapped[Optional[dict]] = mapped_column(JSON)
    # {"grammar": false, "ambiguous": true, "wrong_answer": false, ...}

    # Zaman
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İlişkiler
    question: Mapped["GeneratedQuestion"] = relationship(
        "GeneratedQuestion", back_populates="feedbacks"
    )

    __table_args__ = (
        CheckConstraint(
            "quality_rating >= 1 AND quality_rating <= 5",
            name="check_fb_quality_rating",
        ),
        Index("idx_fb_question", "question_id"),
        Index("idx_fb_verdict", "verdict"),
    )
