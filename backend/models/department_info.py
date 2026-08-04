"""
Task 103: Department Information Models

Models for curriculum, career opportunities, salary expectations, and sector analysis
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


class ExperienceLevel(str, enum.Enum):
    """Experience level enumeration"""

    ENTRY = "entry"  # 0-2 years
    JUNIOR = "junior"  # 2-5 years
    MID = "mid"  # 5-10 years
    SENIOR = "senior"  # 10-15 years
    EXPERT = "expert"  # 15+ years


class IndustryType(str, enum.Enum):
    """Industry type enumeration"""

    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    CONSULTING = "consulting"
    GOVERNMENT = "government"
    STARTUP = "startup"
    OTHER = "other"


# ============================================================
# Task 103.1: Curriculum Information
# ============================================================


class DepartmentCurriculum(Base):
    """
    Task 103.1: Department curriculum details

    Stores curriculum information, course listings, and specialization options
    """

    __tablename__ = "department_curricula"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Department reference
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Basic info
    total_credits = Column(Integer, nullable=True)  # Total ECTS/credits
    duration_years = Column(Integer, default=4)
    duration_semesters = Column(Integer, default=8)

    # Curriculum structure
    core_courses = Column(JSONB, default=list)  # [{code, name, credits, semester}, ...]
    elective_courses = Column(JSONB, default=list)
    specialization_tracks = Column(
        ARRAY(String), default=list
    )  # ["Yapay Zeka", "Siber Güvenlik"]

    # Course distribution
    major_courses_credits = Column(Integer, nullable=True)
    minor_courses_credits = Column(Integer, nullable=True)
    general_education_credits = Column(Integer, nullable=True)

    # Learning outcomes
    learning_outcomes = Column(ARRAY(Text), default=list)
    skills_gained = Column(ARRAY(String), default=list)

    # Prerequisites
    required_equipment = Column(ARRAY(String), default=list)  # ["Laptop", "Tablet"]
    software_requirements = Column(ARRAY(String), default=list)

    # Additional info
    internship_required = Column(Boolean, default=False)
    internship_duration_weeks = Column(Integer, nullable=True)
    thesis_required = Column(Boolean, default=False)
    capstone_project = Column(Boolean, default=True)

    # Updated
    last_updated = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    department = relationship("Department", lazy="selectin")

    def __repr__(self):
        return f"<DepartmentCurriculum {self.department_id}>"


# ============================================================
# Task 103.2: Career Opportunities
# ============================================================


class CareerOpportunity(Base):
    """
    Task 103.2: Career opportunities after graduation

    Stores career paths, job titles, employment statistics
    """

    __tablename__ = "career_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Department reference
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Job info
    job_title = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)
    industry_type = Column(SQLEnum(IndustryType), nullable=True, index=True)

    # Employment statistics
    employment_rate = Column(Float, nullable=True)  # Percentage
    average_hiring_time_days = Column(Integer, nullable=True)  # Days to get hired
    demand_level = Column(String(20), nullable=True)  # "high", "medium", "low"

    # Required skills
    required_skills = Column(ARRAY(String), default=list)
    preferred_certifications = Column(ARRAY(String), default=list)

    # Growth potential
    career_growth_potential = Column(
        String(20), nullable=True
    )  # "high", "medium", "low"
    promotion_timeline_years = Column(Integer, nullable=True)

    # Top employers
    top_employers = Column(ARRAY(String), default=list)  # ["Google", "Microsoft", ...]

    # Updated
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    department = relationship("Department", lazy="selectin")

    def __repr__(self):
        return f"<CareerOpportunity {self.job_title}>"


# ============================================================
# Task 103.3: Salary Expectations
# ============================================================


class SalaryExpectation(Base):
    """
    Task 103.3: Salary expectations by experience level and region

    Stores salary ranges, career progression, regional variations
    """

    __tablename__ = "salary_expectations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Department/Career reference
    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    career_opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("career_opportunities.id"),
        nullable=True,
        index=True,
    )

    # Experience level
    experience_level = Column(SQLEnum(ExperienceLevel), nullable=False, index=True)

    # Salary range (monthly TL)
    min_salary = Column(Integer, nullable=False)
    max_salary = Column(Integer, nullable=False)
    average_salary = Column(Integer, nullable=False)
    median_salary = Column(Integer, nullable=True)

    # Regional variations
    region = Column(
        String(50), nullable=True
    )  # "İstanbul", "Ankara", "İzmir", "National"
    city = Column(String(100), nullable=True, index=True)

    # Industry variations
    industry_type = Column(SQLEnum(IndustryType), nullable=True, index=True)

    # Additional benefits
    average_bonus_percentage = Column(Float, nullable=True)  # % of annual salary
    stock_options_common = Column(Boolean, default=False)
    remote_work_percentage = Column(Float, nullable=True)  # % of jobs offering remote

    # Data source
    year = Column(Integer, nullable=False, default=2024, index=True)
    sample_size = Column(Integer, nullable=True)  # Number of data points
    data_source = Column(String(100), nullable=True)  # "LinkedIn", "Glassdoor", etc.

    # Updated
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    department = relationship("Department", lazy="selectin")
    career_opportunity = relationship("CareerOpportunity", lazy="selectin")

    __table_args__ = (
        Index("idx_salary_dept_exp", "department_id", "experience_level", "year"),
        Index("idx_salary_city", "city", "experience_level"),
    )

    def __repr__(self):
        return (
            f"<SalaryExpectation {self.experience_level.value} - {self.average_salary}>"
        )


# ============================================================
# Task 103.4: Sector Analysis
# ============================================================


class SectorAnalysis(Base):
    """
    Task 103.4: Industry sector analysis

    Stores industry trends, job market analysis, future outlook
    """

    __tablename__ = "sector_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Sector info
    industry_type = Column(SQLEnum(IndustryType), nullable=False, index=True)
    sector_name = Column(String(200), nullable=False)

    # Related departments (many-to-many via JSONB)
    related_department_ids = Column(ARRAY(String), default=list)

    # Market size
    market_size_billion_tl = Column(Float, nullable=True)
    total_employment = Column(Integer, nullable=True)

    # Growth metrics
    year = Column(Integer, nullable=False, default=2024, index=True)
    annual_growth_rate = Column(Float, nullable=True)  # Percentage
    job_growth_rate = Column(Float, nullable=True)  # Percentage
    growth_trend = Column(
        String(20), nullable=True
    )  # "increasing", "stable", "decreasing"

    # Job market
    total_job_openings = Column(Integer, nullable=True)
    unemployment_rate = Column(Float, nullable=True)  # Percentage
    competition_level = Column(String(20), nullable=True)  # "high", "medium", "low"

    # Skills demand
    in_demand_skills = Column(ARRAY(String), default=list)
    emerging_technologies = Column(ARRAY(String), default=list)

    # Future outlook (5-year)
    future_outlook = Column(Text, nullable=True)
    future_demand_prediction = Column(
        String(20), nullable=True
    )  # "high", "medium", "low"
    automation_risk = Column(String(20), nullable=True)  # "high", "medium", "low"

    # Regional distribution
    regional_distribution = Column(
        JSONB, default=dict
    )  # {İstanbul: 40%, Ankara: 25%, ...}

    # Key trends
    key_trends = Column(ARRAY(Text), default=list)
    challenges = Column(ARRAY(Text), default=list)
    opportunities = Column(ARRAY(Text), default=list)

    # Data source
    data_source = Column(String(100), nullable=True)
    last_analyzed = Column(DateTime(timezone=True), default=datetime.now)

    # Updated
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self):
        return f"<SectorAnalysis {self.sector_name} ({self.year})>"


# ============================================================
# Department Statistics (Aggregate)
# ============================================================


class DepartmentStatistics(Base):
    """
    Aggregate statistics for a department

    Combines employment, salary, and career data
    """

    __tablename__ = "department_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Department reference
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Employment statistics
    overall_employment_rate = Column(Float, nullable=True)  # Percentage
    average_hiring_time_days = Column(Integer, nullable=True)
    graduates_employed_in_field = Column(Float, nullable=True)  # Percentage

    # Salary statistics (entry level)
    entry_level_avg_salary = Column(Integer, nullable=True)
    entry_level_min_salary = Column(Integer, nullable=True)
    entry_level_max_salary = Column(Integer, nullable=True)

    # Career progression
    mid_career_avg_salary = Column(Integer, nullable=True)
    senior_avg_salary = Column(Integer, nullable=True)
    salary_growth_rate = Column(Float, nullable=True)  # Annual % increase

    # Industry distribution
    top_industries = Column(
        JSONB, default=list
    )  # [{industry: "Technology", percentage: 60}, ...]
    top_job_titles = Column(
        JSONB, default=list
    )  # [{title: "Software Engineer", count: 1200}, ...]

    # Geographic distribution
    top_cities = Column(
        JSONB, default=list
    )  # [{city: "İstanbul", percentage: 45}, ...]

    # Demand metrics
    job_market_demand = Column(String(20), nullable=True)  # "high", "medium", "low"
    future_growth_potential = Column(String(20), nullable=True)

    # Year
    year = Column(Integer, nullable=False, default=2024, index=True)

    # Updated
    last_updated = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    department = relationship("Department", lazy="selectin")

    def __repr__(self):
        return f"<DepartmentStatistics {self.department_id} ({self.year})>"
