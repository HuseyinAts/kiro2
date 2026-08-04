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
import uuid
from uuid6 import uuid7
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    String,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

# ============================================================================
# TASK 70.3: 5-Level Difficulty Scale
# ============================================================================


class QuestionDifficultyLevel(enum.Enum):
    """5 seviyeli zorluk ölçeği"""

    VERY_EASY = "very_easy"  # Çok Kolay
    EASY = "easy"  # Kolay
    MEDIUM = "medium"  # Orta
    HARD = "hard"  # Zor
    VERY_HARD = "very_hard"  # Çok Zor


# ============================================================================
# TASK 70.2: Hierarchical Topic Taxonomy
# ============================================================================


class TopicHierarchy(Base):
    """
    Hiyerarşik konu taksonomisi
    Örnek: Matematik > Geometri > Üçgenler > Pisagor Teoremi
    """

    __tablename__ = "topic_hierarchy"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Hiyerarşi bilgileri
    level: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1: Ana konu, 2: Alt konu, 3: Detay konu
    parent_id: Mapped[str | None] = mapped_column(String, ForeignKey("topic_hierarchy.id", ondelete="CASCADE")
    )

    # Konu bilgileri
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )  # MAT.GEO.UCG.PIS
    name_tr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # MEB müfredat uyumu
    meb_code: Mapped[str | None] = mapped_column(String(100))
    meb_kazanim: Mapped[dict | None] = mapped_column(JSON)  # MEB kazanım kodları

    # ÖSYM uyumu
    osym_relevance: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0-1 arası ÖSYM'de çıkma olasılığı
    osym_frequency: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Son 10 yılda kaç kez çıktı

    # İstatistikler
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    average_difficulty: Mapped[float] = mapped_column(Float, default=0.0)

    # DB-only legacy kolonlar — alembic dışı eklendi, korunuyor
    difficulty_level: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        server_default="0.5",
        comment="Legacy difficulty (DB-only)",
    )
    subject_area: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Legacy subject_area (DB-only)"
    )

    # Sistem alanları
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    parent: Mapped[Optional["TopicHierarchy"]] = relationship(
        "TopicHierarchy", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["TopicHierarchy"]] = relationship(
        "TopicHierarchy", back_populates="parent"
    )
    questions: Mapped[list["QuestionBankItem"]] = relationship(
        "QuestionBankItem", back_populates="primary_topic"
    )

    # İndeksler ve kısıtlamalar
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
    """
    Soru etiketleri - çoklu etiketleme desteği
    """

    __tablename__ = "question_tags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Etiket bilgileri
    tag_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tag_category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # skill, concept, difficulty, format
    description: Mapped[str | None] = mapped_column(Text)

    # İstatistikler
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İlişkiler
    question_associations: Mapped[list["QuestionTagAssociation"]] = relationship(
        "QuestionTagAssociation", back_populates="tag"
    )

    # İndeksler
    __table_args__ = (
        Index("idx_tag_name", "tag_name"),
        Index("idx_tag_category", "tag_category"),
    )


# ============================================================================
# TASK 70.4: IRT Parameters Storage and Calibration History
# ============================================================================


class IRTCalibrationHistory(Base):
    """
    IRT parametre kalibrasyon geçmişi
    Her kalibrasyon sonrası parametrelerin nasıl değiştiğini takip eder
    """

    __tablename__ = "irt_calibration_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    question_id: Mapped[str] = mapped_column(String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )

    # Kalibrasyon bilgileri
    calibration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    calibration_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # EM, MLE, Bayesian
    sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Kaç öğrenci yanıtı kullanıldı

    # Eski IRT parametreleri
    old_discrimination: Mapped[float | None] = mapped_column(Float)  # a parametresi
    old_difficulty: Mapped[float | None] = mapped_column(Float)  # b parametresi
    old_guessing: Mapped[float | None] = mapped_column(Float)  # c parametresi
    old_upper_asymptote: Mapped[float | None] = mapped_column(Float)  # d parametresi

    # Yeni IRT parametreleri
    new_discrimination: Mapped[float] = mapped_column(Float, nullable=False)
    new_difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    new_guessing: Mapped[float] = mapped_column(Float, nullable=False)
    new_upper_asymptote: Mapped[float] = mapped_column(Float, nullable=False)

    # Kalibrasyon kalitesi
    standard_error: Mapped[float] = mapped_column(Float, default=0.0)
    convergence_iterations: Mapped[int] = mapped_column(Integer, default=0)
    log_likelihood: Mapped[float] = mapped_column(Float, default=0.0)

    # Güven aralıkları
    discrimination_ci_lower: Mapped[float] = mapped_column(Float, default=0.0)
    discrimination_ci_upper: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_ci_lower: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_ci_upper: Mapped[float] = mapped_column(Float, default=0.0)

    # İlişkiler
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="calibration_history"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        CheckConstraint("sample_size >= 30", name="check_calibration_sample_size"),
        CheckConstraint(
            "new_discrimination >= 0.1 AND new_discrimination <= 3.0",
            name="check_new_discrimination",
        ),
        CheckConstraint(
            "new_difficulty >= -3.0 AND new_difficulty <= 3.0",
            name="check_new_difficulty",
        ),
        CheckConstraint(
            "new_guessing >= 0.0 AND new_guessing <= 1.0", name="check_new_guessing"
        ),
        CheckConstraint(
            "new_upper_asymptote >= 0.0 AND new_upper_asymptote <= 1.0",
            name="check_new_upper_asymptote",
        ),
        Index("idx_calibration_question", "question_id"),
        Index("idx_calibration_date", "calibration_date"),
    )


# ============================================================================
# TASK 70.1: Enhanced Question Model
# ============================================================================


class QuestionBankItem(Base):
    """
    Gelişmiş soru bankası modeli
    10,000+ soru için optimize edilmiş yapı
    """

    __tablename__ = "question_bank"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # ========================================================================
    # Soru İçeriği
    # ========================================================================
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_html: Mapped[str | None] = mapped_column(Text)  # HTML formatında soru
    question_latex: Mapped[str | None] = mapped_column(
        Text
    )  # LaTeX formatında matematik
    question_image_url: Mapped[str | None] = mapped_column(String(500))
    image_ocr_text: Mapped[str | None] = mapped_column(Text)
    image_width: Mapped[int | None] = mapped_column(Integer)
    image_height: Mapped[int | None] = mapped_column(Integer)
    question_audio_url: Mapped[str | None] = mapped_column(String(500))

    # Seçenekler
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    option_e: Mapped[str | None] = mapped_column(Text)

    correct_answer: Mapped[str] = mapped_column(
        String(1), nullable=False
    )  # A, B, C, D, E

    # Açıklamalar
    explanation: Mapped[str | None] = mapped_column(Text)
    explanation_video_url: Mapped[str | None] = mapped_column(String(500))
    alternative_solutions: Mapped[dict | None] = mapped_column(
        JSON
    )  # Alternatif çözüm yolları

    # ========================================================================
    # TASK 70.2: Konu Etiketleme
    # ========================================================================
    primary_topic_id: Mapped[str] = mapped_column(String, ForeignKey("topic_hierarchy.id"), nullable=False
    )
    secondary_topics: Mapped[dict | None] = mapped_column(
        JSON
    )  # İkincil konular listesi

    # Bloom taksonomisi seviyesi
    bloom_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-6 arası
    bloom_category: Mapped[str] = mapped_column(String(50), default="knowledge")

    # ========================================================================
    # TASK 70.3: 5-Level Difficulty Scale
    # ========================================================================
    difficulty_level: Mapped[QuestionDifficultyLevel] = mapped_column(
        Enum(QuestionDifficultyLevel),
        nullable=False,
        default=QuestionDifficultyLevel.MEDIUM,
    )

    # IRT bazlı zorluk (otomatik hesaplanır)
    irt_based_difficulty: Mapped[str] = mapped_column(String(20), default="medium")

    # Dinamik zorluk güncellemesi için metrikler
    student_success_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1 arası
    last_difficulty_update: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    difficulty_update_count: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================================================
    # TASK 70.4: IRT Parameters (4PL Model)
    # ========================================================================
    # a: Discrimination (ayırt edicilik) - Sorunun yetenek seviyelerini ne kadar iyi ayırt ettiği
    irt_discrimination: Mapped[float] = mapped_column(Float, default=1.0)

    # b: Difficulty (zorluk) - Sorunun zorluk seviyesi
    irt_difficulty: Mapped[float] = mapped_column(Float, default=0.0)

    # c: Guessing (tahmin) - Şans eseri doğru cevaplama olasılığı
    irt_guessing: Mapped[float] = mapped_column(Float, default=0.25)

    # d: Upper Asymptote (üst asimptot) - Maksimum doğru cevaplama olasılığı
    irt_upper_asymptote: Mapped[float] = mapped_column(Float, default=1.0)

    # IRT kalibrasyon durumu
    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    calibration_sample_size: Mapped[int] = mapped_column(Integer, default=0)
    last_calibration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    calibration_quality_score: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0-1 arası

    # ========================================================================
    # DB-ONLY LEGACY IRT KOLONLARI — ALEMBIC DIŞI EKLENDI, KORUMADA
    # CAT engine bu kolonları kullanıyor — DOKUNMA / DO NOT DROP
    # ========================================================================
    # 3PL IRT parametreleri (CAT kalibrasyonu için)
    irt_a: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True, comment="3PL discrimination param (CAT)"
    )
    irt_b: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True, comment="3PL difficulty param (CAT)"
    )
    irt_c: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="3PL guessing param (CAT)"
    )
    # Kalibrasyon durumu (360 kalibreli soru bu kolonla işaretlendi)
    irt_calibrated: Mapped[bool] = mapped_column(
        Boolean, server_default="false", comment="3PL kalibrasyonu tamamlandı mı"
    )
    irt_calibrated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Kalibrasyon tarihi"
    )
    irt_n_responses: Mapped[int] = mapped_column(
        Integer, server_default="0", comment="Kalibrasyon için kullanılan yanıt sayısı"
    )
    irt_method: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Kalibrasyon yöntemi (EM, MLE, Bayesian)"
    )
    # CAT kalibrasyon havuzu (598 soru bu kolonla işaretlendi — KRİTİK)
    is_calib_pool: Mapped[bool] = mapped_column(
        Boolean, server_default="false", comment="CAT kalibrasyon havuzu üyesi mi"
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True, comment="HNSW indexli Soru Embedding vektörü"
    )

    # ========================================================================
    # Türkçe Morfoloji Analizi
    # ========================================================================
    morphology_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_word_count: Mapped[int] = mapped_column(Integer, default=0)
    average_word_length: Mapped[float] = mapped_column(Float, default=0.0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)

    # ========================================================================
    # İstatistikler ve Performans
    # ========================================================================
    times_asked: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)
    times_skipped: Mapped[int] = mapped_column(Integer, default=0)

    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)  # saniye
    median_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Exposure control (soru maruziyeti kontrolü)
    exposure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_used_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ========================================================================
    # Metadata ve Sınıflandırma
    # ========================================================================
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)  # TYT, AYT, YDT
    # Denormalized for fast string filtering. Canonical hierarchy: primary_topic_id -> topic_hierarchy
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 9-12

    # ÖSYM uyumu
    osym_format_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    osym_year: Mapped[int | None] = mapped_column(
        Integer
    )  # Hangi yılın ÖSYM sorusuna benziyor

    # Kalite skoru
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 arası
    quality_review_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # Convention v2 (15 May 2026): pending, unverified, legacy_v3_unaudited,
    # human_verified, auto_judged_high, rejected, archived.
    # 'approved' YASAK — hardcoded literal yalanıydı, %87 hata.
    # Bkz: docs/quality_review_status_convention.md

    # ========================================================================
    # Pipeline Source Tracking (d-dataset import)
    # ========================================================================
    source_book: Mapped[str | None] = mapped_column(String(300))
    source_page: Mapped[int | None] = mapped_column(Integer)
    pipeline_metadata: Mapped[dict | None] = mapped_column(JSON)

    # ========================================================================
    # Phase 5 Metadata Pipeline (Session 178+, DB-only kolonlar)
    # ========================================================================
    # P1 metadata pipeline tarafından doldurulur (Gemini Flash batch).
    # Curator UI (Faz 3.1) bu alanları queue/verdict ekranında gösterir.
    #
    # @WARN S179 fix (B-P0-17 + B-P0-18): pre-fix the rationale + steps
    # data was 0% populated on `auto_judged_high` (Gold) and 90%
    # populated on `rejected`/`pending` (audit content_quality_llm_review).
    # ALSO: gemini-flash-latest reproduces Hemingway/Stendhal /
    # Pürranameler hallucinations. UI MUST NOT display these columns to
    # students until the regen pipeline (B-P0-17) runs against Gold AND
    # the Opus second-pass judge (B-P0-18) validates non-hallucination.
    misconception_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    solution_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    similar_question_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ========================================================================
    # Curator Audit Trail (Faz 3.6, Session 179)
    # ========================================================================
    # Curator verdict ne zaman verildi? reviewed_by zaten yukarıda tanımlı.
    # pipeline_metadata.curator_verdict.reviewed_at ile redundant ama
    # column-level erişim hızlı stats sorguları için gerekli.
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ========================================================================
    # Sistem Alanları
    # ========================================================================
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE")
    )
    reviewed_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE")
    )

    soru_hash: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="Soru hash değeri"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ========================================================================
    # İlişkiler
    # ========================================================================
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

    # ========================================================================
    # İndeksler ve Kısıtlamalar
    # ========================================================================
    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D', 'E')",
            name="check_correct_answer_bank",
        ),
        CheckConstraint(
            "bloom_level >= 1 AND bloom_level <= 6", name="check_bloom_level"
        ),
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_grade_level_bank"
        ),
        # IRT parameter constraints
        CheckConstraint(
            "irt_discrimination >= 0.1 AND irt_discrimination <= 3.0",
            name="check_irt_discrimination_bank",
        ),
        CheckConstraint(
            "irt_difficulty >= -3.0 AND irt_difficulty <= 3.0",
            name="check_irt_difficulty_bank",
        ),
        CheckConstraint(
            "irt_guessing >= 0.0 AND irt_guessing <= 1.0",
            name="check_irt_guessing_bank",
        ),
        CheckConstraint(
            "irt_upper_asymptote >= 0.0 AND irt_upper_asymptote <= 1.0",
            name="check_irt_upper_asymptote_bank",
        ),
        # Performance constraints
        CheckConstraint(
            "student_success_rate >= 0.0 AND student_success_rate <= 1.0",
            name="check_success_rate",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 100.0",
            name="check_quality_score",
        ),
        CheckConstraint(
            "exposure_rate >= 0.0 AND exposure_rate <= 1.0", name="check_exposure_rate"
        ),
        # Composite indexes for common query patterns
        Index("idx_qbank_topic", "primary_topic_id"),
        Index("idx_qbank_difficulty", "difficulty_level"),
        Index("idx_qbank_irt_difficulty", "irt_difficulty"),
        Index("idx_qbank_exam_type", "exam_type"),
        Index("idx_qbank_subject", "subject_area"),
        Index("idx_qbank_grade", "grade_level"),
        Index("idx_qbank_calibrated", "is_calibrated"),
        Index("idx_qbank_quality", "quality_score"),
        Index("idx_qbank_active", "is_active"),
        Index(
            "ix_question_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # Composite indexes for adaptive test selection
        Index(
            "idx_qbank_exam_subject_difficulty",
            "exam_type",
            "subject_area",
            "irt_difficulty",
        ),
        Index("idx_qbank_topic_difficulty", "primary_topic_id", "difficulty_level"),
        Index(
            "idx_qbank_calibrated_active", "is_calibrated", "is_active", "quality_score"
        ),
        Index(
            "idx_qb_primary_topic",
            "primary_topic_id",
            postgresql_where=text("primary_topic_id IS NOT NULL")
        ),
        Index(
            "idx_qb_calib_pool",
            "is_calib_pool",
            postgresql_where=text("is_calib_pool = true")
        ),
        Index(
            "idx_qb_cat_subject_active",
            func.lower(text("subject_area")),
            "is_active",
            postgresql_where=text("is_active = true")
        ),
        Index("idx_qb_soru_hash", "soru_hash"),
        Index(
            "uq_qb_soru_hash_active",
            "soru_hash",
            unique=True,
            postgresql_where=text("is_active = true")
        ),
    )


class QuestionTagAssociation(Base):
    """
    Soru-etiket ilişki tablosu (many-to-many)
    """

    __tablename__ = "question_tag_associations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    question_id: Mapped[str] = mapped_column(String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[str] = mapped_column(String, ForeignKey("question_tags.id", ondelete="CASCADE"), nullable=False
    )

    # Etiket ağırlığı (bazı etiketler daha önemli olabilir)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İlişkiler
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="tag_associations"
    )
    tag: Mapped["QuestionTag"] = relationship(
        "QuestionTag", back_populates="question_associations"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint("question_id", "tag_id", name="uq_question_tag"),
        Index("idx_qtag_question", "question_id"),
        Index("idx_qtag_tag", "tag_id"),
    )


class QuestionPerformanceAnalytics(Base):
    """
    Soru performans analitiği - zaman bazlı performans takibi
    """

    __tablename__ = "question_performance_analytics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    question_id: Mapped[str] = mapped_column(String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )

    # Analiz dönemi
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # daily, weekly, monthly

    # Performans metrikleri
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)

    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Öğrenci segmentasyonu
    high_ability_success_rate: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Yüksek yetenek öğrenciler
    medium_ability_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    low_ability_success_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # İlişkiler
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", back_populates="performance_analytics"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint(
            "question_id", "analysis_date", "period_type", name="uq_question_analytics"
        ),
        Index("idx_qperf_question", "question_id"),
        Index("idx_qperf_date", "analysis_date"),
        Index("idx_qperf_period", "period_type"),
    )


# ============================================================================
# Yardımcı Fonksiyonlar
# ============================================================================


def calculate_irt_based_difficulty(irt_difficulty: float) -> str:
    """
    IRT difficulty parametresinden 5-level difficulty hesapla

    Args:
        irt_difficulty: IRT b parametresi (-3 ile +3 arası)

    Returns:
        str: very_easy, easy, medium, hard, very_hard
    """
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
    """
    Sorunun zorluk seviyesinin güncellenmesi gerekip gerekmediğini kontrol et

    Args:
        question: Soru nesnesi
        min_attempts: Minimum deneme sayısı

    Returns:
        bool: Güncelleme gerekiyorsa True
    """
    # Yeterli veri yoksa güncelleme yapma
    if question.times_asked < min_attempts:
        return False

    # Son güncelleme 30 günden eskiyse güncelle
    if question.last_difficulty_update:
        days_since_update = (datetime.now() - question.last_difficulty_update).days
        if days_since_update < 30:
            return False

    # Başarı oranı ile IRT zorluk uyumsuzsa güncelle
    expected_difficulty = calculate_irt_based_difficulty(question.irt_difficulty)
    if expected_difficulty != question.irt_based_difficulty:
        return True

    return True
