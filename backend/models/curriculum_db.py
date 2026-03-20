"""
SQLAlchemy ORM Curriculum Models
MEB ve OSYM mufredat standartlari icin veritabani modelleri

Bu modeller curriculum_compliance_service.py icin olusturuldu.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class SubjectTypeDB(str):
    """Subject type enum values for database"""
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    GEOMETRI = "geometri"
    YABANCI_DIL = "yabanci_dil"


class ExamTypeDB(str):
    """Exam type enum values for database"""
    TYT = "tyt"
    AYT = "ayt"
    YDT = "ydt"
    LGS = "lgs"


class GradeLevelDB(str):
    """Grade level enum values for database"""
    GRADE_9 = "9"
    GRADE_10 = "10"
    GRADE_11 = "11"
    GRADE_12 = "12"


class MEBCurriculumStandardDB(Base):
    """MEB Mufredat Standardi veritabani modeli"""

    __tablename__ = "meb_curriculum_standards"
    __table_args__ = (
        Index("idx_meb_subject", "subject"),
        Index("idx_meb_grade_level", "grade_level"),
        Index("idx_meb_subject_grade", "subject", "grade_level"),
        Index("idx_meb_active", "is_active"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(10), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(200), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # JSON fields for list data
    learning_outcomes: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    key_concepts: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    prerequisites: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    assessment_criteria: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    duration_hours: Mapped[int] = mapped_column(Integer, default=0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    learning_outcomes_rel: Mapped[List["LearningOutcomeDB"]] = relationship(
        "LearningOutcomeDB", back_populates="meb_standard"
    )
    curriculum_alignments: Mapped[List["CurriculumAlignmentDB"]] = relationship(
        "CurriculumAlignmentDB", back_populates="meb_standard"
    )


class OSYMStandardDB(Base):
    """OSYM Sinav Standardi veritabani modeli"""

    __tablename__ = "osym_standards"
    __table_args__ = (
        Index("idx_osym_exam_type", "exam_type"),
        Index("idx_osym_subject", "subject"),
        Index("idx_osym_priority", "priority_level"),
        Index("idx_osym_active", "is_active"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_code: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    priority_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # JSON fields for complex data
    question_count_range: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    difficulty_distribution: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    cognitive_levels: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    exam_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    last_exam_appearance: Mapped[Optional[str]] = mapped_column(String(50))

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    curriculum_alignments: Mapped[List["CurriculumAlignmentDB"]] = relationship(
        "CurriculumAlignmentDB", back_populates="osym_standard"
    )


class LearningOutcomeDB(Base):
    """Ogrenme Kazanimi veritabani modeli"""

    __tablename__ = "learning_outcomes"
    __table_args__ = (
        Index("idx_outcome_meb_standard", "meb_standard_id"),
        Index("idx_outcome_code", "code"),
        Index("idx_outcome_subject", "subject"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(10), nullable=False)
    cognitive_level: Mapped[str] = mapped_column(String(50), nullable=False)
    bloom_taxonomy: Mapped[str] = mapped_column(String(20), nullable=False)
    meb_standard_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("meb_curriculum_standards.id", ondelete="CASCADE"), nullable=False
    )

    # JSON fields for list data
    assessment_methods: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    sample_activities: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    meb_standard: Mapped["MEBCurriculumStandardDB"] = relationship(
        "MEBCurriculumStandardDB", back_populates="learning_outcomes_rel"
    )


class CurriculumAlignmentDB(Base):
    """Mufredat Uyumluluk Eslestirmesi veritabani modeli"""

    __tablename__ = "curriculum_alignments"
    __table_args__ = (
        CheckConstraint(
            "alignment_score >= 0.0 AND alignment_score <= 1.0",
            name="check_alignment_score"
        ),
        Index("idx_alignment_meb", "meb_standard_id"),
        Index("idx_alignment_osym", "osym_standard_id"),
        Index("idx_alignment_score", "alignment_score"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    meb_standard_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("meb_curriculum_standards.id", ondelete="CASCADE"), nullable=False
    )
    osym_standard_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("osym_standards.id", ondelete="CASCADE"), nullable=False
    )
    alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    alignment_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # JSON fields for list data
    gaps_identified: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    verified_by: Mapped[Optional[str]] = mapped_column(String(100))
    verification_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    meb_standard: Mapped["MEBCurriculumStandardDB"] = relationship(
        "MEBCurriculumStandardDB", back_populates="curriculum_alignments"
    )
    osym_standard: Mapped["OSYMStandardDB"] = relationship(
        "OSYMStandardDB", back_populates="curriculum_alignments"
    )


class CurriculumUpdateRequestDB(Base):
    """Mufredat Guncelleme Talebi veritabani modeli"""

    __tablename__ = "curriculum_update_requests"
    __table_args__ = (
        Index("idx_update_req_status", "status"),
        Index("idx_update_req_subject", "subject"),
        Index("idx_update_req_type", "update_type"),
    )

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    update_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)

    # JSON fields for list data
    affected_standards: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    changes_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_document: Mapped[Optional[str]] = mapped_column(String(500))
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    implementation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
