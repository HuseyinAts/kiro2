"""
Soru Bankası Veritabanı Modelleri
Teknofest 2025 Eğitim Eylemci Platformu

Task 70: Soru Veritabanı Tasarımı
- 70.1: Soru modeli (Question schema, metadata, relationships)
- 70.2: Konu etiketleme (Hierarchical topic taxonomy, multi-level tagging)
- 70.3: Zorluk seviyesi (5-level difficulty, IRT-based, dynamic updates)
- 70.4: IRT parametreleri (a, b, c, d storage, update mechanism, calibration history)
"""

import enum
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7

from .base import Base


class QuestionDifficultyLevel(enum.Enum):
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class TopicHierarchy(Base):
    __tablename__ = "topic_hierarchy"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("topic_hierarchy.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_tr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    meb_code: Mapped[str | None] = mapped_column(String(100))
    meb_kazanim: Mapped[dict | None] = mapped_column(JSON)
    osym_relevance: Mapped[float] = mapped_column(Float, default=0.0)
    osym_frequency: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    average_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_level: Mapped[float | None] = mapped_column(
        Float, nullable=True, server_default="0.5"
    )
    subject_area: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped[Optional["TopicHierarchy"]] = relationship(
        "TopicHierarchy", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["TopicHierarchy"]] = relationship(
        "TopicHierarchy", back_populates="parent"
    )
    questions: Mapped[list["QuestionBankItem"]] = relationship(
        "QuestionBankItem", back_populates="primary_topic"
    )

    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 5", name="check_topic_level"),
        CheckConstraint(
            "osym_relevance >= 0.0 AND osym_relevance <= 1.0",
            name="check_osym_relevance",
        ),
        Index("idx_topic_code", "code"),
        Index("idx_topic_parent", "parent_id"),
        Index("idx_topic_level", "level"),
        Index("idx_topic_meb_code", "meb_code"),
    )


class QuestionTag(Base):
    __tablename__ = "question_tags"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    tag_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tag_category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    question_associations: Mapped[list["QuestionTagAssociation"]] = relationship(
        "QuestionTagAssociation", back_populates="tag"
    )
    __table_args__ = (
        Index("idx_tag_name", "tag_name"),
        Index("idx_tag_category", "tag_category"),
    )


class IRTCalibrationHistory(Base):
    __tablename__ = "irt_calibration_history"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    calibration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    calibration_method: Mapped[str] = mapped_column(String(50), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    old_discrimination: Mapped[float | None] = mapped_column(Float)
    old_difficulty: Mapped[float | None] = mapped_column(Float)
    old_guessing: Mapped[float | None] = mapped_column(Float)
    old_upper_asymptote: Mapped[float | None] = mapped_column(Float)
    new_discrimination: Mapped[float] = mapped_column(Float, nullable=False)
    new_difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    new_guessing: Mapped[float] = mapped_column(Float, nullable=False)
    new_upper_asymptote: Mapped[float] = mapped_column(Float, nullable=False)
    standard_error: Mapped[float] = mapped_column(Float, default=0.0)
    convergence_iterations: Mapped[int] = mapped_column(Integer, default=0)
    log_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    discrimination_ci_lower: Mapped[float] = mapped_column(Float, default=0.0)
    discrimination_ci_upper: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_ci_lower: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_ci_upper: Mapped[float] = mapped_column(Float, default=0.0)
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="calibration_history"
    )


class QuestionBankItem(Base):
    """Core Question Bank Table (Stripped down God Table)"""

    __tablename__ = "question_bank"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    soru_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_topic_id: Mapped[str] = mapped_column(
        String, ForeignKey("topic_hierarchy.id", ondelete="CASCADE"), nullable=False
    )

    # `default` (Python-side) ve `server_default` (DDL) AYNI yone bakmali.
    # S229'da olculdu: SQLAlchemy Python-side `default`'u INSERT'e kolonu DAHIL
    # ETTIGI icin `server_default` HIC atesLenmez -> `default=False` iken
    # `is_active` verilmeden olusturulan her soru DB'ye False iniyordu (ogrenciye
    # gorunmez + `uq_qb_soru_hash_active` kismi indeksi -- WHERE is_active=true --
    # o satirlar icin sessizce olu). Ayrica `server_default="true"` canli DDL'de
    # HIC YOKTU (information_schema.column_default IS NULL); migration
    # `0002_is_active_server_default` onu gercek yapiyor.
    # Civi: tests/integration/test_question_bank_defaults.py
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    is_anchor: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    review_status: Mapped[str] = mapped_column(
        String(20), default="PENDING", server_default="APPROVED"
    )

    created_by: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Split relationships
    content: Mapped["QuestionContent"] = relationship(
        "QuestionContent",
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan",
    )
    metadata_info: Mapped["QuestionMetadata"] = relationship(
        "QuestionMetadata",
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan",
    )
    statistics: Mapped["QuestionStatistics"] = relationship(
        "QuestionStatistics",
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan",
    )

    primary_topic: Mapped["TopicHierarchy"] = relationship(
        "TopicHierarchy", back_populates="questions"
    )
    tag_associations: Mapped[list["QuestionTagAssociation"]] = relationship(
        "QuestionTagAssociation", back_populates="question"
    )
    calibration_history: Mapped[list["IRTCalibrationHistory"]] = relationship(
        "IRTCalibrationHistory", back_populates="question"
    )
    performance_analytics: Mapped[list["QuestionPerformanceAnalytics"]] = relationship(
        "QuestionPerformanceAnalytics", back_populates="question"
    )

    __table_args__ = (
        Index(
            "idx_qb_primary_topic",
            "primary_topic_id",
            postgresql_where=text("primary_topic_id IS NOT NULL"),
        ),
        Index("idx_qb_soru_hash", "soru_hash"),
        Index(
            "uq_qb_soru_hash_active",
            "soru_hash",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )


class QuestionContent(Base):
    """Extracted text, options, and assets"""

    __tablename__ = "question_content"
    id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), primary_key=True
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_html: Mapped[str | None] = mapped_column(Text)
    question_latex: Mapped[str | None] = mapped_column(Text)
    question_image_url: Mapped[str | None] = mapped_column(String(500))
    image_ocr_text: Mapped[str | None] = mapped_column(Text)
    image_width: Mapped[int | None] = mapped_column(Integer)
    image_height: Mapped[int | None] = mapped_column(Integer)
    question_audio_url: Mapped[str | None] = mapped_column(String(500))

    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    option_e: Mapped[str | None] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)

    explanation: Mapped[str | None] = mapped_column(Text)
    structured_explanation: Mapped[dict | None] = mapped_column(
        JSON
    )  # {"dogrulama": "", "curutme": "", "hap_bilgi": ""}
    explanation_video_url: Mapped[str | None] = mapped_column(String(500))
    alternative_solutions: Mapped[dict | None] = mapped_column(JSON)

    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="content"
    )

    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D', 'E')",
            name="check_correct_answer_content",
        ),
    )


class QuestionMetadata(Base):
    """Extracted tags, types, sources, NLP"""

    __tablename__ = "question_metadata"
    id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), primary_key=True
    )

    secondary_topics: Mapped[dict | None] = mapped_column(JSON)
    bloom_level: Mapped[int] = mapped_column(Integer, default=1)
    bloom_category: Mapped[str] = mapped_column(String(50), default="knowledge")

    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)

    osym_format_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    osym_year: Mapped[int | None] = mapped_column(Integer)

    source_book: Mapped[str | None] = mapped_column(String(300))
    source_page: Mapped[int | None] = mapped_column(Integer)
    pipeline_metadata: Mapped[dict | None] = mapped_column(JSON)

    misconception_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    pedagogical_status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", server_default="ACTIVE"
    )  # ACTIVE, DLQ_QUARANTINE, NEEDS_REVISION
    solution_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    similar_question_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    morphology_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_word_count: Mapped[int] = mapped_column(Integer, default=0)
    average_word_length: Mapped[float] = mapped_column(Float, default=0.0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)

    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="metadata_info"
    )

    __table_args__ = (
        CheckConstraint(
            "bloom_level >= 1 AND bloom_level <= 6", name="check_bloom_level"
        ),
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_grade_level"
        ),
    )


class QuestionStatistics(Base):
    """Extracted metrics, IRT, calibration"""

    __tablename__ = "question_statistics"
    id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), primary_key=True
    )

    difficulty_level: Mapped[QuestionDifficultyLevel] = mapped_column(
        Enum(QuestionDifficultyLevel),
        nullable=False,
        default=QuestionDifficultyLevel.MEDIUM,
    )
    irt_based_difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    student_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_difficulty_update: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    difficulty_update_count: Mapped[int] = mapped_column(Integer, default=0)

    irt_discrimination: Mapped[float] = mapped_column(Float, default=1.0)
    irt_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    irt_guessing: Mapped[float] = mapped_column(Float, default=0.25)
    irt_upper_asymptote: Mapped[float] = mapped_column(Float, default=1.0)

    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    calibration_sample_size: Mapped[int] = mapped_column(Integer, default=0)
    last_calibration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    calibration_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    irt_a: Mapped[float | None] = mapped_column(Numeric(6, 4))
    irt_b: Mapped[float | None] = mapped_column(Numeric(6, 4))
    irt_c: Mapped[float | None] = mapped_column(Numeric(5, 4))
    irt_calibrated: Mapped[bool] = mapped_column(Boolean, server_default="false")
    irt_calibrated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    irt_n_responses: Mapped[int] = mapped_column(Integer, server_default="0")
    irt_method: Mapped[str | None] = mapped_column(Text)
    is_calib_pool: Mapped[bool] = mapped_column(Boolean, server_default="false")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    times_asked: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)
    times_skipped: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    median_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    exposure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_used_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_review_status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="statistics"
    )

    __table_args__ = (
        CheckConstraint(
            "irt_discrimination >= 0.1 AND irt_discrimination <= 3.0",
            name="check_irt_discrim",
        ),
        CheckConstraint(
            "irt_difficulty >= -3.0 AND irt_difficulty <= 3.0", name="check_irt_diff"
        ),
        CheckConstraint(
            "irt_guessing >= 0.0 AND irt_guessing <= 1.0", name="check_irt_guess"
        ),
        CheckConstraint(
            "irt_upper_asymptote >= 0.0 AND irt_upper_asymptote <= 1.0",
            name="check_irt_upper",
        ),
        Index(
            "ix_question_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class QuestionTagAssociation(Base):
    __tablename__ = "question_tag_associations"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[str] = mapped_column(
        String, ForeignKey("question_tags.id", ondelete="CASCADE"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="tag_associations"
    )
    tag: Mapped["QuestionTag"] = relationship(
        "QuestionTag", back_populates="question_associations"
    )
    __table_args__ = (
        UniqueConstraint("question_id", "tag_id", name="uq_question_tag"),
        Index("idx_qtag_question", "question_id"),
        Index("idx_qtag_tag", "tag_id"),
    )


class QuestionPerformanceAnalytics(Base):
    __tablename__ = "question_performance_analytics"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    high_ability_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    medium_ability_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    low_ability_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="performance_analytics"
    )
    __table_args__ = (
        UniqueConstraint(
            "question_id", "analysis_date", "period_type", name="uq_question_analytics"
        ),
        Index("idx_qperf_question", "question_id"),
        Index("idx_qperf_date", "analysis_date"),
        Index("idx_qperf_period", "period_type"),
    )


def calculate_irt_based_difficulty(irt_difficulty: float) -> str:
    if irt_difficulty < -1.5:
        return "very_easy"
    if irt_difficulty < -0.5:
        return "easy"
    if irt_difficulty < 0.5:
        return "medium"
    if irt_difficulty < 1.5:
        return "hard"
    return "very_hard"


def should_update_difficulty(
    question: QuestionBankItem, min_attempts: int = 100
) -> bool:
    # Zorluk/IRT alanlari question_statistics'e tasindi; istatistik kaydi
    # yoksa guncellenecek bir sey de yok.
    stats = question.statistics
    if stats is None:
        return False
    if stats.times_asked < min_attempts:
        return False
    if stats.last_difficulty_update:
        days_since_update = (datetime.now() - stats.last_difficulty_update).days
        if days_since_update < 30:
            return False
    expected_difficulty = calculate_irt_based_difficulty(stats.irt_difficulty)
    return expected_difficulty != stats.irt_based_difficulty


# ---------------------------------------------------------------------------
# Geriye uyumluluk katmani (STRANGLER — gecici)
# ---------------------------------------------------------------------------
# 69 alan question_bank tablosundan question_content / question_metadata /
# question_statistics tablolarina tasindi (bolunmus sema canli DB ile birebir).
# Depoda bu alanlara ORNEK uzerinden erisen ~2400 cagri yeri var; hepsini tek
# seferde gocurmemek icin asagidaki devrediciler uretiliyor.
#
# SINIF duzeyi (SQL ifadesi) erisim KASITLI olarak desteklenmiyor:
#     select(QuestionBankItem.irt_difficulty)   # -> acik AttributeError
# Boyle yazilmis 108 yer (17 dosya) gercek JOIN'e cevrilmeli. Sessizce None
# dondurmek yerine yol gosteren hata veriyoruz ki bu yerler gorunur kalsin.
#
# Alan listesi ELLE TUTULMUYOR: hedef siniflarin kolonlarindan turetilir,
# boylece split ilerledikce kendini gunceller.


def _install_compat_delegates() -> None:
    """Tasinan alanlar icin QuestionBankItem uzerinde devredici tanimla."""

    def make_delegate(relationship_name: str, field: str) -> hybrid_property:
        def _get(self):
            if isinstance(self, type):
                raise AttributeError(
                    f"QuestionBankItem.{field} sinif duzeyinde kullanilamaz: "
                    f"bu alan artik {relationship_name} iliskisinde. "
                    f"Sorguda JOIN kullanin."
                )
            related = getattr(self, relationship_name, None)
            return None if related is None else getattr(related, field, None)

        def _set(self, value):
            related = getattr(self, relationship_name, None)
            if related is None:
                raise AttributeError(
                    f"'{field}' artik {relationship_name} uzerinde; "
                    f"once o iliskili kaydi olusturun."
                )
            setattr(related, field, value)

        _get.__name__ = field
        return hybrid_property(_get).setter(_set)

    sources = (
        ("content", QuestionContent),
        ("metadata_info", QuestionMetadata),
        ("statistics", QuestionStatistics),
    )
    # NOT: kurulmus devredici sinif duzeyinde AttributeError firlattigi icin
    # hasattr() onu GOREMEZ; kaynaklar arasi tekrari acik bir kume ile onluyoruz
    # (bugun cakisan ad yok, ama sessiz "son kazanir" tuzagini birakmayalim).
    installed: set[str] = set()
    for relationship_name, target in sources:
        for column in target.__table__.columns:
            field = column.name
            # 'id' FK'nin kendisi; zaten QuestionBankItem'da olan adi ezme.
            if field == "id" or field in installed or hasattr(QuestionBankItem, field):
                continue
            setattr(QuestionBankItem, field, make_delegate(relationship_name, field))
            installed.add(field)


_install_compat_delegates()
