"""
Task 101: University Preference Advisory System - Database Models

Models for universities, departments, base scores, and quotas
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class UniversityType(str, enum.Enum):
    """University type enumeration"""

    DEVLET = "devlet"  # State university
    VAKIF = "vakif"  # Foundation/private university


class ProgramType(str, enum.Enum):
    """Program type enumeration"""

    NORMAL = "normal"
    KKTC = "kktc"  # Northern Cyprus Turkish Republic
    OZEL_YETENEK = "ozel_yetenek"  # Special talent
    IKINCI_OGRETIM = "ikinci_ogretim"  # Evening/second education


class ScoreType(str, enum.Enum):
    """Score type enumeration (YKS puan türleri)"""

    SAY = "SAY"  # Sayısal (Science/Math)
    EA = "EA"  # Eşit Ağırlık (Equal Weight)
    SOZ = "SOZ"  # Sözel (Verbal/Social Sciences)
    DIL = "DIL"  # Dil (Foreign Languages)


# ============================================================
# Task 101.1: Universities
# ============================================================


class University(Base):
    """
    Task 101.1: University database with profiles and locations
    """

    __tablename__ = "universities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(255), nullable=False, unique=True, index=True)
    short_name = Column(String(50), nullable=True)  # e.g., "İTÜ", "ODTÜ"
    university_type = Column(SQLEnum(UniversityType), nullable=False, index=True)

    # Location
    city = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String(10), nullable=True)

    # Coordinates for map display
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Contact
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)

    # Profile info
    established_year = Column(Integer, nullable=True)
    rector = Column(String(100), nullable=True)
    total_students = Column(Integer, nullable=True)
    total_faculty = Column(Integer, nullable=True)

    # Rankings and scores
    world_ranking = Column(Integer, nullable=True)
    turkey_ranking = Column(Integer, nullable=True)

    # Additional info
    description = Column(Text, nullable=True)
    campus_info = Column(JSONB, default=dict)  # {campus_name: details}
    facilities = Column(
        ARRAY(String), default=list
    )  # ["library", "sports_center", "dormitory"]

    # Social media
    social_media = Column(JSONB, default=dict)  # {twitter: url, instagram: url}

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    # NOTE: departments relationship removed - University links to Department through UniversityProgram
    # Use university.programs to access associated programs, which have department references
    programs = relationship(
        "UniversityProgram",
        back_populates="university",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<University {self.name} ({self.city})>"


# ============================================================
# Task 101.2: Departments
# ============================================================


class Department(Base):
    """
    Task 101.2: Department database with descriptions and career paths
    """

    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True)  # Department code
    faculty = Column(String(200), nullable=True)  # Faculty name

    # Education details
    degree_type = Column(String(50), nullable=False)  # Lisans, Önlisans, Yüksek Lisans
    education_language = Column(String(50), default="Türkçe")
    education_duration = Column(Integer, default=4)  # Years

    # Description
    description = Column(Text, nullable=True)
    overview = Column(Text, nullable=True)

    # Career paths
    career_opportunities = Column(ARRAY(String), default=list)
    job_titles = Column(ARRAY(String), default=list)
    average_salary = Column(Integer, nullable=True)  # Monthly TL
    employment_rate = Column(Float, nullable=True)  # Percentage

    # Prerequisites
    required_subjects = Column(ARRAY(String), default=list)  # ["matematik", "fizik"]
    recommended_skills = Column(ARRAY(String), default=list)

    # Additional info
    accreditation = Column(JSONB, default=dict)  # {mudek: true, abet: false}
    international_programs = Column(
        ARRAY(String), default=list
    )  # ["Erasmus", "Mevlana"]

    # SEO
    seo_keywords = Column(ARRAY(String), default=list)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    programs = relationship(
        "UniversityProgram",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Department {self.name} ({self.degree_type})>"


# ============================================================
# Task 101.3 & 101.4: University Programs (Base Scores + Quotas)
# ============================================================


class UniversityProgram(Base):
    """
    Task 101.3 & 101.4: University programs with base scores and quotas

    Combines university + department + year data
    """

    __tablename__ = "university_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    university_id = Column(
        UUID(as_uuid=True), ForeignKey("universities.id"), nullable=False, index=True
    )
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Program info
    program_code = Column(String(50), nullable=True, index=True)  # ÖSYM program code
    program_name = Column(String(255), nullable=False)  # Full program name
    program_type = Column(SQLEnum(ProgramType), default=ProgramType.NORMAL, index=True)

    # Year
    year = Column(Integer, nullable=False, index=True)  # 2024, 2025, etc.

    # Score type
    score_type = Column(SQLEnum(ScoreType), nullable=False, index=True)

    # Task 101.3: Base Score Data
    base_score = Column(Float, nullable=True)  # Taban puan
    top_score = Column(Float, nullable=True)  # Tavan puan
    median_score = Column(Float, nullable=True)  # Ortalama puan

    # Task 101.4: Quota Information
    total_quota = Column(Integer, nullable=True)
    general_quota = Column(Integer, nullable=True)
    special_quota = Column(Integer, nullable=True)  # Engelli, özel durum
    filled_quota = Column(Integer, nullable=True)  # Yerleşen sayısı

    # Acceptance metrics
    acceptance_rate = Column(Float, nullable=True)  # Yerleşme oranı (%)
    competition_ratio = Column(Float, nullable=True)  # Başvuru/kontenjan oranı

    # Placement statistics
    min_rank = Column(Integer, nullable=True)  # En küçük yerleşme sırası
    max_rank = Column(Integer, nullable=True)  # En büyük yerleşme sırası
    median_rank = Column(Integer, nullable=True)

    # Additional info
    scholarship = Column(Boolean, default=False)  # Burslu mu?
    scholarship_percentage = Column(Float, nullable=True)  # Burs yüzdesi
    tuition_fee = Column(Integer, nullable=True)  # Öğrenim ücreti (vakıf için)

    # Language prep
    has_language_prep = Column(Boolean, default=False)
    prep_mandatory = Column(Boolean, default=False)

    # Special conditions
    special_conditions = Column(JSONB, default=dict)  # Ek koşullar
    bonus_coefficients = Column(JSONB, default=dict)  # Katsayılar

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    university = relationship("University", back_populates="programs")
    department = relationship("Department", back_populates="programs")
    score_history = relationship(
        "ProgramScoreHistory",
        back_populates="program",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "idx_program_search", "university_id", "department_id", "year", "score_type"
        ),
        Index("idx_base_score", "year", "score_type", "base_score"),
    )

    def __repr__(self):
        return f"<UniversityProgram {self.program_name} ({self.year})>"


# ============================================================
# Historical Data
# ============================================================


class ProgramScoreHistory(Base):
    """
    Task 101.3: Historical base score trends

    Stores historical data for trend analysis and predictions
    """

    __tablename__ = "program_score_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference
    program_id = Column(
        UUID(as_uuid=True),
        ForeignKey("university_programs.id"),
        nullable=False,
        index=True,
    )

    # Year
    year = Column(Integer, nullable=False, index=True)

    # Scores
    base_score = Column(Float, nullable=True)
    top_score = Column(Float, nullable=True)
    median_score = Column(Float, nullable=True)

    # Quotas
    total_quota = Column(Integer, nullable=True)
    filled_quota = Column(Integer, nullable=True)

    # Rankings
    min_rank = Column(Integer, nullable=True)
    max_rank = Column(Integer, nullable=True)

    # Metadata
    source = Column(String(100), nullable=True)  # ÖSYM, YÖK, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    program = relationship("UniversityProgram", back_populates="score_history")

    __table_args__ = (Index("idx_history_year", "program_id", "year"),)

    def __repr__(self):
        return f"<ProgramScoreHistory {self.year} - {self.base_score}>"


# ============================================================
# User Preferences (for personalized recommendations)
# ============================================================


class UserUniversityPreference(Base):
    """
    User's university preferences for recommendation engine
    """

    __tablename__ = "user_university_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Preferences
    preferred_cities = Column(ARRAY(String), default=list)
    preferred_university_types = Column(
        ARRAY(String), default=list
    )  # ["devlet", "vakif"]
    preferred_score_types = Column(ARRAY(String), default=list)  # ["SAY", "EA"]

    # Score info
    yks_score = Column(Float, nullable=True)
    score_type = Column(String(10), nullable=True)

    # Career interests
    career_interests = Column(ARRAY(String), default=list)
    target_departments = Column(ARRAY(String), default=list)

    # Budget constraints
    max_tuition_fee = Column(Integer, nullable=True)
    needs_scholarship = Column(Boolean, default=False)

    # Additional preferences
    preferences = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UserUniversityPreference {self.user_id}>"
