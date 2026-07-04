"""
Learning Path Database Models
Teknofest 2025 - P0 Fix: Database Integration

SQLAlchemy models for Learning Path system
- Student profiles (CANONICAL MODEL)
- Learning paths
- Completion status
- Quiz results
- Progress tracking
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base

# Learning Path Models


class LearningPathStudentProfile(Base):
    """
    CANONICAL student profile model for learning path system.

    This is the primary model for student profiles. Other profile models
    (StudentProfile, StudentLearningProfile) are deprecated and should
    migrate to this model.

    Attributes:
        student_id: Unique identifier
        user_id: Foreign key to users table
        name: Student's full name
        grade: Grade level (9-12 or mezun)
        exam_target: Target exam (YKS-TYT, AYT-SAY, etc.)
        learning_style: VARK learning style
        knowledge_level: Current knowledge level
        interests: List of subjects to study
        goals: Learning goals
        available_time: Daily study time in minutes
        target_university: Target university name
        target_department: Target department name
        target_ranking: Target ranking (top_1000, top_5000, etc.)
        weekly_study_commitment: Weekly study hours
        exam_date: Target exam date
        vark_visual_score: VARK visual score (0.0-1.0)
        vark_auditory_score: VARK auditory score (0.0-1.0)
        vark_reading_score: VARK reading/writing score (0.0-1.0)
        vark_kinesthetic_score: VARK kinesthetic score (0.0-1.0)
        overall_progress: Overall learning progress (0-100)
        average_quiz_score: Average quiz score (0-100)
        total_study_time_minutes: Total study time in minutes
        last_activity_at: Last activity timestamp
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "learning_path_student_profiles"

    # Primary Key
    student_id = Column(String(100), primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String(100), ForeignKey("users.id"), nullable=True, index=True)

    # Profile Info
    name = Column(String(200), nullable=False)
    grade = Column(String(20), nullable=False)  # "9", "10", "11", "12", "mezun"
    exam_target = Column(
        String(50), nullable=False
    )  # "LGS", "YKS-TYT", "YKS-AYT-SAY", etc.

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

    # Extended fields (from other models)
    target_university = Column(String(200), nullable=True)
    target_department = Column(String(200), nullable=True)
    target_ranking = Column(String(50), nullable=True)  # top_1000, top_5000, etc.
    weekly_study_commitment = Column(Integer, nullable=True)  # hours
    exam_date = Column(Date, nullable=True)

    # Learning style questionnaire results (from StudentLearningProfile)
    vark_visual_score = Column(Float, nullable=True)  # 0.0-1.0
    vark_auditory_score = Column(Float, nullable=True)  # 0.0-1.0
    vark_reading_score = Column(Float, nullable=True)  # 0.0-1.0
    vark_kinesthetic_score = Column(Float, nullable=True)  # 0.0-1.0

    # Felder-Silverman dimensions (from StudentLearningProfile)
    felder_active_reflective = Column(Float, nullable=True)  # -1.0 to +1.0
    felder_sensing_intuitive = Column(Float, nullable=True)  # -1.0 to +1.0
    felder_visual_verbal = Column(Float, nullable=True)  # -1.0 to +1.0
    felder_sequential_global = Column(Float, nullable=True)  # -1.0 to +1.0

    # Performance tracking
    overall_progress = Column(Float, default=0.0)  # 0-100
    average_quiz_score = Column(Float, nullable=True)  # 0-100
    total_study_time_minutes = Column(Integer, default=0)
    last_activity_at = Column(DateTime, nullable=True)

    # B2: Daily streak tracking
    daily_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_study_date = Column(Date, nullable=True)

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

    # Table configuration
    __table_args__ = (
        Index("idx_student_grade", "grade"),
        Index("idx_student_exam_target", "exam_target"),
        Index("idx_student_learning_style", "learning_style"),
        Index("idx_student_user_id", "user_id"),
        Index("idx_student_last_activity", "last_activity_at"),
        {"extend_existing": True},
    )

    @classmethod
    def from_legacy_profile(cls, legacy_profile: Any) -> "LearningPathStudentProfile":
        """
        Create from legacy StudentProfile or StudentLearningProfile.

        Args:
            legacy_profile: Legacy profile instance

        Returns:
            New LearningPathStudentProfile instance

        Raises:
            ValueError: If legacy profile type is unknown
        """
        # Handle StudentProfile (from user_models.py)
        if hasattr(legacy_profile, "user_id") and hasattr(
            legacy_profile, "grade_level"
        ):
            return cls(
                student_id=legacy_profile.id,
                user_id=legacy_profile.user_id,
                name=f"{legacy_profile.user.first_name} {legacy_profile.user.last_name}"
                if hasattr(legacy_profile, "user")
                else "",
                grade=str(legacy_profile.grade_level),
                exam_target=legacy_profile.hedef_sinav or "YKS",
                learning_style=legacy_profile.learning_style.value
                if legacy_profile.learning_style
                else "mixed",
                available_time=legacy_profile.study_hours_per_day * 60
                if legacy_profile.study_hours_per_day
                else 60,
                target_university=legacy_profile.target_university,
                target_department=legacy_profile.target_department,
                total_study_time_minutes=legacy_profile.total_study_hours * 60
                if legacy_profile.total_study_hours
                else 0,
                created_at=legacy_profile.created_at,
                updated_at=legacy_profile.updated_at,
            )
        # Handle StudentLearningProfile (from student_learning_profile.py)
        if hasattr(legacy_profile, "vark_visual") and hasattr(
            legacy_profile, "student_id"
        ):
            return cls(
                student_id=legacy_profile.id,
                user_id=legacy_profile.student_id,
                name="",  # Will need to fetch from User
                grade="12",  # Default
                exam_target="YKS",  # Default
                learning_style=legacy_profile.dominant_vark_style or "mixed",
                vark_visual_score=legacy_profile.vark_visual,
                vark_auditory_score=legacy_profile.vark_auditory,
                vark_reading_score=legacy_profile.vark_reading,
                vark_kinesthetic_score=legacy_profile.vark_kinesthetic,
                felder_active_reflective=legacy_profile.felder_active_reflective,
                felder_sensing_intuitive=legacy_profile.felder_sensing_intuitive,
                felder_visual_verbal=legacy_profile.felder_visual_verbal,
                felder_sequential_global=legacy_profile.felder_sequential_global,
                created_at=legacy_profile.detected_at,
                updated_at=legacy_profile.updated_at,
            )
        raise ValueError(f"Unknown legacy profile type: {type(legacy_profile)}")


class LearningPath(Base):
    """Generated learning path"""

    __tablename__ = "learning_paths"

    # Primary Key
    path_id = Column(String(100), primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
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
    student = relationship(
        "LearningPathStudentProfile", back_populates="learning_paths"
    )

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
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
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
    student = relationship(
        "LearningPathStudentProfile", back_populates="completion_statuses"
    )

    # Indexes
    __table_args__ = (
        Index("idx_completion_student_node", "student_id", "node_id", unique=True),
    )


class TopicProgress(Base):
    """Topic progress tracking"""

    __tablename__ = "topic_progress"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
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
    student = relationship(
        "LearningPathStudentProfile", back_populates="progress_updates"
    )

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
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
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
    student = relationship(
        "LearningPathStudentProfile", back_populates="quiz_submissions"
    )

    # Indexes
    __table_args__ = (
        Index("idx_quiz_student_quiz", "student_id", "quiz_id"),
        Index("idx_quiz_submitted_at", "submitted_at"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_quiz_score_range"),
    )


class Quiz(Base):
    """
    Quiz model for storing quiz configurations.

    Links to questions via QuizQuestion association table.
    Enables real database-driven quiz grading instead of mock data.
    """

    __tablename__ = "quizzes"

    # Primary Key
    id = Column(String(100), primary_key=True)

    # Quiz Info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(200), nullable=True, index=True)

    # Configuration
    time_limit_minutes = Column(Integer, nullable=True)  # None = no limit
    passing_score = Column(Float, nullable=False, default=70.0)
    shuffle_questions = Column(Boolean, nullable=False, default=True)
    show_answers_after = Column(Boolean, nullable=False, default=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    questions = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_quiz_subject_topic", "subject", "topic"),)


class QuizQuestion(Base):
    """
    Quiz-Question association with question-specific settings.

    Links Quiz to Question (from questions table) with order and points.
    """

    __tablename__ = "quiz_questions"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    quiz_id = Column(
        String(100),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String,
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Question Settings for this Quiz
    order_number = Column(Integer, nullable=False)  # Question order in quiz
    points = Column(Float, nullable=False, default=1.0)  # Points for this question

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    __table_args__ = (Index("idx_quiz_question_order", "quiz_id", "order_number"),)


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


class StudySession(Base):
    """
    B1: Çalışma oturumu takibi.
    Öğrenci çalışma başlat/bitir ile süre kaydeder.
    Bitişte total_study_time_minutes ve daily_streak güncellenir.
    """

    __tablename__ = "study_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    student_id = Column(
        String(100),
        ForeignKey("learning_path_student_profiles.student_id"),
        nullable=False,
        index=True,
    )

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # Activity during session
    topics_studied = Column(JSON, default=list)
    questions_answered = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    # Indexes
    __table_args__ = (Index("idx_session_student_started", "student_id", "started_at"),)
