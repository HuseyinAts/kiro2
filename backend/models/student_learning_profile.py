"""
Student Learning Profile ORM Model
Stores VARK + Felder-Silverman hybrid learning style profiles
Part of Mock Data Cleanup - Phase 4
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from .base import Base


class StudentLearningProfile(Base):
    """
    Student learning style profile model
    Stores VARK + Felder-Silverman hybrid learning styles

    Replaces in-memory self.student_profiles dictionary
    """

    __tablename__ = "student_learning_profiles"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Foreign Keys
    student_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # VARK Profile (4 dimensions, 0.0-1.0 range)
    vark_visual = Column(Float, default=0.0, nullable=False)
    vark_auditory = Column(Float, default=0.0, nullable=False)
    vark_reading = Column(Float, default=0.0, nullable=False)
    vark_kinesthetic = Column(Float, default=0.0, nullable=False)

    # Felder-Silverman Profile (4 dimensions, -1.0 to +1.0 range)
    felder_active_reflective = Column(Float, default=0.0, nullable=False)  # -1 (reflective) to +1 (active)
    felder_sensing_intuitive = Column(Float, default=0.0, nullable=False)  # -1 (intuitive) to +1 (sensing)
    felder_visual_verbal = Column(Float, default=0.0, nullable=False)      # -1 (verbal) to +1 (visual)
    felder_sequential_global = Column(Float, default=0.0, nullable=False)  # -1 (global) to +1 (sequential)

    # Computed values
    hybrid_code = Column(String(20), nullable=False, index=True)  # e.g., "VR-ASVS"
    dominant_vark_style = Column(String(20), nullable=False)  # "visual", "auditory", etc.
    dominant_felder_dimension = Column(String(30), nullable=False)  # "active_reflective", etc.

    # Metadata
    confidence_score = Column(Float, default=0.0, nullable=False)  # 0.0-1.0
    profile_description = Column(Text, nullable=True)

    # Behavioral data used for calculation (JSON)
    behavioral_data_snapshot = Column(JSON, nullable=True)  # Snapshot of data used for calculation
    questionnaire_responses = Column(JSON, nullable=True)  # Survey responses if any

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (optional)
    # student = relationship("User", back_populates="learning_profile")

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
        return self.confidence_score > 0.7

    @property
    def needs_update(self) -> bool:
        """Check if profile is older than 30 days and should be recalculated"""
        from datetime import timedelta
        age = datetime.utcnow() - self.updated_at
        return age > timedelta(days=30)
