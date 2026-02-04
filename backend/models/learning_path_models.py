"""
Learning Path Database Models
Teknofest 2025 - P0 Fix: Database Integration

SQLAlchemy models for Learning Path system
- Student profiles
- Learning paths
- Completion status
- Quiz results
- Progress tracking
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from database.connection import Base

# Learning Path Models


class LearningPathStudentProfile(Base):
    """Student profile for learning path (renamed to avoid conflict with models.database.StudentProfile)"""

    __tablename__ = "learning_path_student_profiles"
    __table_args__ = {"extend_existing": True}

    # Primary Key
    student_id = Column(String(100), primary_key=True, index=True)
    user_id = Column(
        String(100), ForeignKey("users.kullanici_id"), nullable=True, index=True
    )

    # Profile Info
    name = Column(String(200), nullable=False)
    grade = Column(String(20), nullable=False)  # "9", "10", "11", "12"
    exam_target = Column(String(50), nullable=False)  # "LGS", "YKS"

    # Learning Preferences
    learning_style = Column(
        String(50), nullable=False, default="mixed"
    )  # visual, auditory, reading, kinesthetic, mixed
    knowledge_level = Column(
        String(50), nullable=False, default="beginner"
    )  # beginner, elementary, intermediate, advanced, expert
    interests = Column(JSON, nullable=False, default=list)  # List[str]
    goals = Column(JSON, nullable=False, default=list)  # List[str]
    available_time = Column(Integer, nullable=False, default=60)  # Daily minutes

    # Metadata
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    learning_paths = relationship(
        "LearningPath", back_populates="student", cascade="all, delete-orphan"
    )
    completion_statuses = relationship(
        "TopicCompletion", back_populates="student", cascade="all, delete-orphan"
    )
    quiz_submissions = relationship(
        "QuizSubmission", back_populates="student", cascade="all, delete-orphan"
    )
    progress_updates = relationship(
        "TopicProgress", back_populates="student", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_student_grade", "grade"),
        Index("idx_student_exam_target", "exam_target"),
        Index("idx_student_learning_style", "learning_style"),
    )


class LearningPath(Base):
    """Generated learning path"""

    __tablename__ = "learning_paths"

    # Primary Key
    path_id = Column(String(100), primary_key=True, index=True)
    student_id = Column(
        String(100),
        ForeignKey("learning_path_student_profiles.student_id"),
        nullable=False,
        index=True,
    )

    # Path Info
    subject = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(String(50), nullable=False, default="intermediate")
    duration_weeks = Column(Integer, nullable=False, default=4)
    target_date = Column(DateTime, nullable=True)

    # Path Content (JSON)
    modules = Column(
        JSON, nullable=False, default=list
    )  # List[Dict] - Module structure
    phases = Column(JSON, nullable=False, default=list)  # List[Dict] - Phase structure
    resources = Column(JSON, nullable=False, default=list)  # List[Dict] - Resource list

    # AI Generation Info
    ai_generated = Column(Boolean, nullable=False, default=True)
    reasoning = Column(Text, nullable=True)  # Why this path was generated
    agent_metadata = Column(JSON, nullable=False, default=dict)

    # Progress
    total_modules = Column(Integer, nullable=False, default=0)
    completed_modules = Column(Integer, nullable=False, default=0)
    total_topics = Column(Integer, nullable=False, default=0)
    completed_topics = Column(Integer, nullable=False, default=0)
    overall_progress = Column(Float, nullable=False, default=0.0)  # 0-100

    # Metadata
    total_time = Column(Integer, nullable=False, default=0)  # Total minutes
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    student = relationship("LearningPathStudentProfile", back_populates="learning_paths")

    # Indexes
    __table_args__ = (
        Index("idx_path_student_subject", "student_id", "subject"),
        Index("idx_path_created_at", "created_at"),
        CheckConstraint(
            "overall_progress >= 0 AND overall_progress <= 100",
            name="check_progress_range",
        ),
    )


class TopicCompletion(Base):
    """Topic completion status"""

    __tablename__ = "topic_completions"

    # Composite Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        String(100),
        ForeignKey("learning_path_student_profiles.student_id"),
        nullable=False,
        index=True,
    )
    node_id = Column(String(100), nullable=False, index=True)  # Format: "MOD1-TOP1"

    # Completion Info
    completed = Column(Boolean, nullable=False, default=False)
    completion_date = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    student = relationship("LearningPathStudentProfile", back_populates="completion_statuses")

    # Indexes
    __table_args__ = (
        Index("idx_completion_student_node", "student_id", "node_id", unique=True),
    )


class TopicProgress(Base):
    """Topic progress tracking"""

    __tablename__ = "topic_progress"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        String(100),
        ForeignKey("learning_path_student_profiles.student_id"),
        nullable=False,
        index=True,
    )
    node_id = Column(String(100), nullable=False, index=True)  # Format: "MOD1-TOP1"

    # Progress Info
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    time_spent = Column(Integer, nullable=False, default=0)  # Minutes
    completed = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    student = relationship("LearningPathStudentProfile", back_populates="progress_updates")

    # Indexes
    __table_args__ = (
        Index("idx_progress_student_node", "student_id", "node_id"),
        CheckConstraint(
            "progress >= 0 AND progress <= 100", name="check_progress_percentage"
        ),
    )


class QuizSubmission(Base):
    """Quiz submission and results"""

    __tablename__ = "quiz_submissions"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        String(100),
        ForeignKey("learning_path_student_profiles.student_id"),
        nullable=False,
        index=True,
    )
    quiz_id = Column(String(100), nullable=False, index=True)

    # Quiz Info
    question_count = Column(Integer, nullable=False)
    passing_score = Column(Float, nullable=False, default=70.0)

    # Results
    score = Column(Float, nullable=False)  # 0-100
    correct_count = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)

    # Details
    answers = Column(JSON, nullable=False, default=list)  # List[Dict] - Answer details
    total_time_seconds = Column(Integer, nullable=False, default=0)

    # Metadata
    submitted_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    student = relationship("LearningPathStudentProfile", back_populates="quiz_submissions")

    # Indexes
    __table_args__ = (
        Index("idx_quiz_student_quiz", "student_id", "quiz_id"),
        Index("idx_quiz_submitted_at", "submitted_at"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_quiz_score_range"),
    )


class FallbackVideo(Base):
    """Fallback/example videos cache"""

    __tablename__ = "fallback_videos"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=True, index=True)

    # Video Info
    video_id = Column(String(100), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)

    # Video Metadata
    duration = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    channel_name = Column(String(200), nullable=True)
    channel_id = Column(String(100), nullable=True)

    # Quality Scores
    turkish_score = Column(Float, nullable=False, default=1.0)  # 0-1
    relevance_score = Column(Float, nullable=False, default=1.0)  # 0-1
    quality_score = Column(Float, nullable=False, default=1.0)  # 0-1
    final_score = Column(Float, nullable=False, default=1.0)  # 0-1

    # Flags
    is_accessible = Column(Boolean, nullable=False, default=True)
    is_embeddable = Column(Boolean, nullable=False, default=True)
    is_turkish = Column(Boolean, nullable=False, default=True)
    is_example = Column(Boolean, nullable=False, default=True)  # Example video flag

    # Metadata
    tags = Column(JSON, nullable=False, default=list)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Indexes
    __table_args__ = (
        Index("idx_fallback_subject_topic", "subject", "topic"),
        Index("idx_fallback_is_example", "is_example"),
        Index("idx_fallback_final_score", "final_score"),
    )
