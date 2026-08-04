"""
DEPRECATED: Student Learning Profile ORM Model

This module contains legacy student profile models that are deprecated.

Use backend.models.learning_path_models.LearningPathStudentProfile instead.

These models will be removed in v3.0.0.

Part of Mock Data Cleanup - Phase 4
"""

import warnings
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import String, JSON, Column, DateTime, Float, ForeignKey, String, Text

from .base import Base

if TYPE_CHECKING:
    from .learning_path_models import LearningPathStudentProfile


def _deprecation_warning(model_name: str) -> None:
    """Issue deprecation warning for legacy models."""
    warnings.warn(
        f"{model_name} is deprecated. Use LearningPathStudentProfile from "
        "backend.models.learning_path_models instead. "
        "This model will be removed in v3.0.0.",
        DeprecationWarning,
        stacklevel=3,
    )


class StudentLearningProfile(Base):
    """
    DEPRECATED: Use LearningPathStudentProfile instead.

    This class is kept for backward compatibility and will be removed in v3.0.0.

    Student learning style profile model
    Stores VARK + Felder-Silverman hybrid learning styles

    Replaces in-memory self.student_profiles dictionary
    """

    __tablename__ = "student_learning_profiles"

    def __init__(self, *args, **kwargs):
        """Initialize with deprecation warning."""
        _deprecation_warning("StudentLearningProfile")
        super().__init__(*args, **kwargs)

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Tenant
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )

    # Foreign Keys
    student_id = Column(
        String, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # VARK Profile (4 dimensions, 0.0-1.0 range)
    vark_visual = Column(Float, default=0.0, nullable=False)
    vark_auditory = Column(Float, default=0.0, nullable=False)
    vark_reading = Column(Float, default=0.0, nullable=False)
    vark_kinesthetic = Column(Float, default=0.0, nullable=False)

    # Felder-Silverman Profile (4 dimensions, -1.0 to +1.0 range)
    felder_active_reflective = Column(
        Float, default=0.0, nullable=False
    )  # -1 (reflective) to +1 (active)
    felder_sensing_intuitive = Column(
        Float, default=0.0, nullable=False
    )  # -1 (intuitive) to +1 (sensing)
    felder_visual_verbal = Column(
        Float, default=0.0, nullable=False
    )  # -1 (verbal) to +1 (visual)
    felder_sequential_global = Column(
        Float, default=0.0, nullable=False
    )  # -1 (global) to +1 (sequential)

    # Computed values
    hybrid_code = Column(String(20), nullable=False, index=True)  # e.g., "VR-ASVS"
    dominant_vark_style = Column(
        String(20), nullable=False
    )  # "visual", "auditory", etc.
    dominant_felder_dimension = Column(
        String(30), nullable=False
    )  # "active_reflective", etc.

    # Metadata
    confidence_score = Column(Float, default=0.0, nullable=False)  # 0.0-1.0
    profile_description = Column(Text, nullable=True)

    # Behavioral data used for calculation (JSON)
    behavioral_data_snapshot = Column(
        JSON, nullable=True
    )  # Snapshot of data used for calculation
    questionnaire_responses = Column(JSON, nullable=True)  # Survey responses if any

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships (optional)
    # student = relationship("User", back_populates="learning_profile", lazy="selectin")

    def __repr__(self):
        return f"<StudentLearningProfile(student={self.student_id}, code={self.hybrid_code}, confidence={self.confidence_score:.2f})>"

    @property
    def vark_profile_dict(self) -> dict:
        """Return VARK profile as dictionary"""
        return {
            "visual": self.vark_visual,
            "auditory": self.vark_auditory,
            "reading": self.vark_reading,
            "kinesthetic": self.vark_kinesthetic,
        }

    @property
    def felder_profile_dict(self) -> dict:
        """Return Felder-Silverman profile as dictionary"""
        return {
            "active_reflective": self.felder_active_reflective,
            "sensing_intuitive": self.felder_sensing_intuitive,
            "visual_verbal": self.felder_visual_verbal,
            "sequential_global": self.felder_sequential_global,
        }

    @property
    def is_high_confidence(self) -> bool:
        """Check if profile detection has high confidence (>0.7)"""
        return bool(self.confidence_score > 0.7)

    @property
    def needs_update(self) -> bool:
        """Check if profile is older than 30 days and should be recalculated"""
        if self.updated_at is None:
            return True

        # NAIVE/AWARE KARISIMI (gf82, 2 Agu 2026 — canli 500)
        # Bu sinifin iki yarisi celisiyordu:
        #   :113  updated_at = Column(DateTime, default=datetime.utcnow)
        #         -> tz-BILGISIZ (DateTime timezone=True DEGIL, utcnow naive)
        #   burasi datetime.now(UTC) ile cikariyor -> tz-BILGILI
        # DB'den okunan nesnede `updated_at` naive gelir ve cikarma
        # `TypeError: can't subtract offset-naive and offset-aware` atar.
        # Zincir: api/learning_style.py:219 -> service:451 -> service:89 -> burasi
        #
        # Naive deger UTC kabul edilir — kolonun varsayilani `datetime.utcnow`,
        # yani zaten UTC uretiyor; yalniz etiketi eksik.
        # KOLONUN KENDISI duzeltilmedi (timestamptz'e cevirmek migration +
        # canli veri donusumu demek, demo gunu risk alinmadi) — `GF-K6`
        # altinda acik kalem. Bekci: tests/unit/test_ogrenme_stili_profil_yasi.py
        guncelleme = self.updated_at
        if guncelleme.tzinfo is None:
            guncelleme = guncelleme.replace(tzinfo=UTC)

        age = datetime.now(UTC) - guncelleme
        return bool(age > timedelta(days=30))

    def to_canonical(self) -> "LearningPathStudentProfile":
        """
        Convert to canonical LearningPathStudentProfile.

        Returns:
            New LearningPathStudentProfile instance
        """
        from .learning_path_models import LearningPathStudentProfile

        return LearningPathStudentProfile.from_legacy_profile(self)
