"""
Task 105: Student Review Models

Database models for review system, ratings, moderation, and filtering
"""

from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from .database import Base
from enum import Enum


# ============================================================
# Enumerations
# ============================================================


class ReviewType(str, Enum):
    """Type of review"""

    UNIVERSITY = "university"
    DEPARTMENT = "department"
    PROFESSOR = "professor"
    COURSE = "course"
    DORMITORY = "dormitory"
    GENERAL = "general"


class ReviewStatus(str, Enum):
    """Review moderation status"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    REMOVED = "removed"


class ReportReason(str, Enum):
    """Reason for reporting a review"""

    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    OFFENSIVE = "offensive"
    FAKE = "fake"
    MISLEADING = "misleading"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


class RatingCategory(str, Enum):
    """Rating categories for multi-criteria reviews"""

    EDUCATION_QUALITY = "education_quality"
    FACULTY = "faculty"
    CAMPUS_FACILITIES = "campus_facilities"
    SOCIAL_LIFE = "social_life"
    CAREER_OPPORTUNITIES = "career_opportunities"
    ACCOMMODATION = "accommodation"
    FOOD_SERVICE = "food_service"
    ADMINISTRATION = "administration"
    VALUE_FOR_MONEY = "value_for_money"


# ============================================================
# Task 105.1: Review System
# ============================================================


class StudentReview(Base):
    """
    Student review model

    Stores reviews submitted by students about universities,
    departments, professors, courses, etc.
    """

    __tablename__ = "student_reviews"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Review target
    review_type = Column(SQLEnum(ReviewType), nullable=False)
    university_id = Column(
        String, ForeignKey("universities.id", ondelete="CASCADE")
    )
    department_id = Column(
        String, ForeignKey("departments.id", ondelete="CASCADE")
    )
    professor_id = Column(String)  # Could add professors table later
    course_id = Column(String)  # Could add courses table later
    dormitory_id = Column(
        String, ForeignKey("dormitory_info.id", ondelete="CASCADE")
    )

    # Review content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Overall rating (1.0 - 5.0)
    overall_rating = Column(Float, nullable=False)

    # Additional metadata
    pros = Column(JSONB, default=list)  # List of pros
    cons = Column(JSONB, default=list)  # List of cons
    tags = Column(JSONB, default=list)  # ["good-faculty", "nice-campus", etc.]

    # Student info (optional)
    student_year = Column(Integer)  # Graduation year
    enrollment_year = Column(Integer)  # Enrollment year
    is_current_student = Column(Boolean, default=True)
    is_alumni = Column(Boolean, default=False)

    # Task 105.3: Moderation
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    moderation_notes = Column(Text)
    moderated_by = Column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    moderated_at = Column(DateTime(timezone=True))

    # Spam/quality scores (0.0 - 1.0)
    spam_score = Column(Float, default=0.0)  # Higher = more likely spam
    quality_score = Column(Float, default=0.5)  # Higher = better quality

    # Auto-moderation flags
    contains_profanity = Column(Boolean, default=False)
    contains_contact_info = Column(Boolean, default=False)
    is_too_short = Column(Boolean, default=False)

    # Task 105.2: Verified reviews
    is_verified = Column(Boolean, default=False)  # Verified student
    verification_method = Column(String(100))  # "student_id", "email", etc.
    verified_at = Column(DateTime(timezone=True))

    # Engagement metrics
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Metadata
    language = Column(String(10), default="tr")
    ip_address = Column(String(50))  # For spam detection
    user_agent = Column(String(255))  # For spam detection

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at = Column(DateTime(timezone=True))

    # Relationships
    ratings = relationship(
        "ReviewRating", back_populates="review", cascade="all, delete-orphan"
    )
    votes = relationship(
        "ReviewVote", back_populates="review", cascade="all, delete-orphan"
    )
    reports = relationship(
        "ReviewReport", back_populates="review", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_student_reviews_user", "user_id"),
        Index("idx_student_reviews_type", "review_type"),
        Index("idx_student_reviews_university", "university_id"),
        Index("idx_student_reviews_department", "department_id"),
        Index("idx_student_reviews_status", "status"),
        Index("idx_student_reviews_rating", "overall_rating"),
        Index("idx_student_reviews_created", "created_at"),
        Index("idx_student_reviews_verified", "is_verified"),
    )


# ============================================================
# Task 105.2: Multi-criteria Rating System
# ============================================================


class ReviewRating(Base):
    """
    Review rating model

    Stores multi-criteria ratings for reviews
    (e.g., education quality, faculty, facilities, etc.)
    """

    __tablename__ = "review_ratings"

    id = Column(String, primary_key=True, default=uuid4)
    review_id = Column(
        String,
        ForeignKey("student_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Rating category and value
    category = Column(SQLEnum(RatingCategory), nullable=False)
    rating = Column(Float, nullable=False)  # 1.0 - 5.0

    # Optional comment for this specific category
    comment = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    review = relationship("StudentReview", back_populates="ratings")

    # Indexes
    __table_args__ = (
        Index("idx_review_ratings_review", "review_id"),
        Index("idx_review_ratings_category", "category"),
        Index("idx_review_ratings_rating", "rating"),
        # Unique constraint: one rating per category per review
        Index("idx_review_ratings_unique", "review_id", "category", unique=True),
    )


# ============================================================
# Task 105.2: Helpful Votes
# ============================================================


class ReviewVote(Base):
    """
    Review vote model

    Stores helpful/not helpful votes for reviews
    """

    __tablename__ = "review_votes"

    id = Column(String, primary_key=True, default=uuid4)
    review_id = Column(
        String,
        ForeignKey("student_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Vote type
    is_helpful = Column(Boolean, nullable=False)  # True = helpful, False = not helpful

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    review = relationship("StudentReview", back_populates="votes")

    # Indexes
    __table_args__ = (
        Index("idx_review_votes_review", "review_id"),
        Index("idx_review_votes_user", "user_id"),
        # Unique constraint: one vote per user per review
        Index("idx_review_votes_unique", "review_id", "user_id", unique=True),
    )


# ============================================================
# Task 105.3: Review Reports and Moderation
# ============================================================


class ReviewReport(Base):
    """
    Review report model

    Stores reports of inappropriate/spam reviews
    """

    __tablename__ = "review_reports"

    id = Column(String, primary_key=True, default=uuid4)
    review_id = Column(
        String,
        ForeignKey("student_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    reporter_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Report details
    reason = Column(SQLEnum(ReportReason), nullable=False)
    description = Column(Text)

    # Report status
    status = Column(
        String(50), default="pending"
    )  # "pending", "reviewed", "resolved", "dismissed"
    resolved_by = Column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    review = relationship("StudentReview", back_populates="reports")

    # Indexes
    __table_args__ = (
        Index("idx_review_reports_review", "review_id"),
        Index("idx_review_reports_reporter", "reporter_id"),
        Index("idx_review_reports_status", "status"),
        Index("idx_review_reports_reason", "reason"),
    )


# ============================================================
# Aggregate Review Statistics
# ============================================================


class ReviewStatistics(Base):
    """
    Aggregate review statistics

    Pre-computed statistics for universities, departments, etc.
    """

    __tablename__ = "review_statistics"

    id = Column(String, primary_key=True, default=uuid4)

    # Target
    review_type = Column(SQLEnum(ReviewType), nullable=False)
    university_id = Column(
        String, ForeignKey("universities.id", ondelete="CASCADE")
    )
    department_id = Column(
        String, ForeignKey("departments.id", ondelete="CASCADE")
    )
    dormitory_id = Column(
        String, ForeignKey("dormitory_info.id", ondelete="CASCADE")
    )

    # Overall statistics
    total_reviews = Column(Integer, default=0)
    verified_reviews = Column(Integer, default=0)
    average_rating = Column(Float)

    # Rating distribution (1-5 stars)
    rating_1_count = Column(Integer, default=0)
    rating_2_count = Column(Integer, default=0)
    rating_3_count = Column(Integer, default=0)
    rating_4_count = Column(Integer, default=0)
    rating_5_count = Column(Integer, default=0)

    # Category averages (JSONB for flexibility)
    category_averages = Column(
        JSONB, default=dict
    )  # {"education_quality": 4.2, "faculty": 4.5, ...}

    # Engagement
    total_helpful_votes = Column(Integer, default=0)
    total_views = Column(Integer, default=0)

    # Sentiment analysis (optional)
    positive_percentage = Column(Float)  # Percentage of positive reviews
    negative_percentage = Column(Float)  # Percentage of negative reviews

    # Common tags
    top_tags = Column(JSONB, default=list)  # Top 10 most common tags

    # Metadata
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_review_statistics_type", "review_type"),
        Index("idx_review_statistics_university", "university_id"),
        Index("idx_review_statistics_department", "department_id"),
        Index("idx_review_statistics_rating", "average_rating"),
    )


# ============================================================
# Moderation Queue
# ============================================================


class ModerationQueue(Base):
    """
    Moderation queue model

    Tracks reviews that need moderation
    """

    __tablename__ = "moderation_queue"

    id = Column(String, primary_key=True, default=uuid4)
    review_id = Column(
        String,
        ForeignKey("student_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Priority
    priority = Column(Integer, default=0)  # Higher = more urgent

    # Auto-flagged reasons
    flag_reasons = Column(JSONB, default=list)  # ["spam", "profanity", "too_short"]

    # Assignment
    assigned_to = Column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    assigned_at = Column(DateTime(timezone=True))

    # Status
    status = Column(
        String(50), default="pending"
    )  # "pending", "in_review", "completed"

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index("idx_moderation_queue_review", "review_id"),
        Index("idx_moderation_queue_status", "status"),
        Index("idx_moderation_queue_priority", "priority"),
        Index("idx_moderation_queue_assigned", "assigned_to"),
    )
