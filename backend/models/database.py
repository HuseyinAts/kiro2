"""
SQLAlchemy ORM Models
Türkiye Üniversite Sınavları Hazırlık Platformu için database modelleri
"""

import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Import Base from separate module to avoid circular imports
from .base import Base


# Enum definitions
class UserRole(enum.Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ADMIN = "ADMIN"


class ExamType(enum.Enum):
    TYT = "tyt"
    AYT = "ayt"
    YDT = "ydt"
    DENEME = "deneme"


class QuestionDifficulty(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LearningStyle(enum.Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class SubjectArea(enum.Enum):
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN = "fen"
    SOSYAL = "sosyal"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    INGILIZCE = "ingilizce"


# User Models
class User(Base):
    """Kullanıcı modeli - öğrenci, öğretmen, veli"""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Sprint 4: Two-Factor Authentication (2FA) fields
    secret_2fa: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="TOTP secret key for 2FA"
    )
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="2FA enabled status"
    )
    backup_codes_hashed: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Hashed backup codes for 2FA recovery"
    )

    # Sprint 6: Premium/Tier fields for rate limiting
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Premium subscription status"
    )
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Premium subscription expiry"
    )

    # Profile information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.STUDENT
    )

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)

    # Gamification fields (Task 91)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    last_level_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # System fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="user", uselist=False
    )
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        "TeacherProfile", back_populates="user", uselist=False
    )
    parent_profile: Mapped[Optional["ParentProfile"]] = relationship(
        "ParentProfile", back_populates="user", uselist=False
    )

    # Parent-Child relationships (ParentChild model defined in models.parent)
    # NOTE: Commented out due to import ordering issues - ParentChild not available at User model initialization time
    # TODO: Fix this by restructuring imports or using late-binding approach
    # children_relations: Mapped[List["ParentChild"]] = relationship(
    #     "ParentChild", back_populates="parent", viewonly=True
    # )

    # Gamification relationships (Task 91, P2.2)
    badges: Mapped[List["UserBadge"]] = relationship("UserBadge", back_populates="user")
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user"
    )
    point_transactions: Mapped[List["PointTransaction"]] = relationship(
        "PointTransaction", back_populates="user"
    )

    # FSRS relationships - using fully qualified paths to avoid conflicts
    fsrs_cards: Mapped[List["FSRSCard"]] = relationship(
        "models.database.FSRSCard", back_populates="student"
    )
    fsrs_schedules: Mapped[List["FSRSSchedule"]] = relationship(
        "models.database.FSRSSchedule", back_populates="student"
    )
    fsrs_reviews: Mapped[List["FSRSReview"]] = relationship(
        "models.database.FSRSReview", back_populates="student"
    )
    fsrs_profile: Mapped[Optional["FSRSStudentProfile"]] = relationship(
        "models.database.FSRSStudentProfile", back_populates="student", uselist=False
    )
    fsrs_study_sessions: Mapped[List["FSRSStudySession"]] = relationship(
        "models.database.FSRSStudySession", back_populates="student"
    )
    fsrs_subject_stats: Mapped[List["FSRSSubjectStats"]] = relationship(
        "FSRSSubjectStats", back_populates="student"
    )

    # Manipulatives relationships (Task 87.9)
    manipulative_progress: Mapped[List["ManipulativeProgress"]] = relationship(
        "ManipulativeProgress", back_populates="user"
    )
    manipulative_activities: Mapped[List["ManipulativeActivity"]] = relationship(
        "ManipulativeActivity", back_populates="user"
    )
    weekly_progress: Mapped[List["WeeklyProgress"]] = relationship(
        "WeeklyProgress", back_populates="user"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_role", "role"),
        Index("idx_user_created_at", "created_at"),
    )


class StudentProfile(Base):
    """Öğrenci profil modeli"""

    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Academic information
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 9, 10, 11, 12
    school_name: Mapped[Optional[str]] = mapped_column(String(200))
    target_university: Mapped[Optional[str]] = mapped_column(String(200))
    target_department: Mapped[Optional[str]] = mapped_column(String(200))
    hedef_sinav: Mapped[Optional[str]] = mapped_column(String(20))  # Target exam: TYT, AYT, YDT, LGS
    veli_onay: Mapped[bool] = mapped_column(Boolean, default=True)  # Parent approval for data collection

    # Learning preferences
    learning_style: Mapped[Optional[LearningStyle]] = mapped_column(Enum(LearningStyle))
    study_hours_per_day: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_study_time: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # morning, afternoon, evening

    # Performance tracking
    current_level: Mapped[float] = mapped_column(Float, default=0.0)
    total_study_hours: Mapped[int] = mapped_column(Integer, default=0)
    total_questions_solved: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)

    # Devrimsel özellikler
    vark_profile: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # VARK + Felder-Silverman hibrit profil
    zpd_range: Mapped[Optional[dict]] = mapped_column(JSON)  # ZPD + Maarif aralığı
    irt_ability: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # IRT yetenek parametresi
    fsrs_parameters: Mapped[Optional[dict]] = mapped_column(JSON)  # FSRS parametreleri

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships (ARCHITECTURE FIX: Eager loading to prevent N+1)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_profile",
        lazy="selectin",  # Eager load user when accessing student_profile
    )
    exam_sessions: Mapped[List["ExamSession"]] = relationship(
        "ExamSession",
        back_populates="student",
        lazy="selectin",  # Prevent N+1 when iterating through students
    )
    learning_analytics: Mapped[List["LearningAnalytics"]] = relationship(
        "LearningAnalytics", back_populates="student", lazy="selectin"
    )

    # Constraints (ARCHITECTURE FIX: Composite indexes added)
    __table_args__ = (
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_grade_level"
        ),
        CheckConstraint(
            "current_level >= 0.0 AND current_level <= 10.0", name="check_current_level"
        ),
        Index("idx_student_grade_level", "grade_level"),
        Index("idx_student_learning_style", "learning_style"),
        # Composite indexes for common query patterns
        Index("idx_student_grade_style", "grade_level", "learning_style"),
        Index("idx_student_user_grade", "user_id", "grade_level"),
    )


class TeacherProfile(Base):
    """Öğretmen profil modeli"""

    __tablename__ = "teacher_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Professional information
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_areas: Mapped[Optional[dict]] = mapped_column(JSON)  # Branş alanları
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    education_level: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Lisans, Yüksek Lisans, Doktora

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")
    classes: Mapped[List["ClassRoom"]] = relationship(
        "ClassRoom", back_populates="teacher"
    )


class ParentProfile(Base):
    """Veli profil modeli"""

    __tablename__ = "parent_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Children information (JSON array of student IDs)
    children_ids: Mapped[Optional[dict]] = mapped_column(JSON)

    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    weekly_reports: Mapped[bool] = mapped_column(Boolean, default=True)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="parent_profile")


# Question and Exam Models
class Question(Base):
    """Soru modeli"""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Answer options
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    option_e: Mapped[Optional[str]] = mapped_column(Text)  # YDT için 5. seçenek

    correct_answer: Mapped[str] = mapped_column(
        String(1), nullable=False
    )  # A, B, C, D, E
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Classification
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    subtopic: Mapped[Optional[str]] = mapped_column(String(200))

    # Difficulty and IRT parameters
    difficulty: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty), nullable=False
    )
    irt_difficulty: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # IRT difficulty parameter (-3 to +3)
    irt_discrimination: Mapped[float] = mapped_column(
        Float, default=1.0
    )  # IRT discrimination parameter
    irt_guessing: Mapped[float] = mapped_column(
        Float, default=0.25
    )  # IRT guessing parameter

    # Turkish morphology analysis
    morphology_complexity: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Türkçe morfolojik karmaşıklık
    readability_score: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Okunabilirlik skoru

    # Statistics
    times_asked: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)  # seconds

    # System fields
    created_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column("aktif", Boolean, default=True)

    # Visual content support (Phase 1: Tables, Phase 2: Graphs, Phase 3: Geometry)
    visual_content: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="question"
    )
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer", back_populates="question"
    )

    # Indexes and constraints
    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D', 'E')", name="check_correct_answer"
        ),
        CheckConstraint(
            "irt_difficulty >= -3.0 AND irt_difficulty <= 3.0",
            name="check_irt_difficulty",
        ),
        CheckConstraint(
            "irt_discrimination >= 0.1 AND irt_discrimination <= 3.0",
            name="check_irt_discrimination",
        ),
        CheckConstraint(
            "irt_guessing >= 0.0 AND irt_guessing <= 1.0", name="check_irt_guessing"
        ),
        Index("idx_question_exam_type", "exam_type"),
        Index("idx_question_subject", "subject_area"),
        Index("idx_question_topic", "topic"),
        Index("idx_question_difficulty", "difficulty"),
        Index("idx_question_irt_difficulty", "irt_difficulty"),
    )


class ExamSession(Base):
    """Sınav oturumu modeli"""

    __tablename__ = "exam_sessions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Exam information
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), nullable=False)
    exam_name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Session status
    status: Mapped[str] = mapped_column(
        String(50), default="not_started"
    )  # not_started, in_progress, completed, abandoned
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_wrong: Mapped[int] = mapped_column(Integer, default=0)
    total_empty: Mapped[int] = mapped_column(Integer, default=0)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    scaled_score: Mapped[Optional[float]] = mapped_column(
        Float
    )  # ÖSYM benzeri ölçeklenmiş puan
    percentile: Mapped[Optional[float]] = mapped_column(Float)  # Yüzdelik dilim

    # IRT Analysis
    estimated_ability: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # IRT yetenek tahmini
    ability_confidence: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Tahmin güvenilirliği

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile", back_populates="exam_sessions"
    )
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="exam_session"
    )
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer", back_populates="exam_session"
    )

    # Indexes
    __table_args__ = (
        Index("idx_exam_session_student", "student_id"),
        Index("idx_exam_session_type", "exam_type"),
        Index("idx_exam_session_status", "status"),
        Index("idx_exam_session_created", "created_at"),
    )


class ExamQuestion(Base):
    """Sınav-soru ilişki modeli"""

    __tablename__ = "exam_questions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    exam_session_id: Mapped[str] = mapped_column(
        String, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )

    question_order: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Sınavdaki soru sırası

    # Relationships
    exam_session: Mapped["ExamSession"] = relationship(
        "ExamSession", back_populates="exam_questions"
    )
    question: Mapped["Question"] = relationship(
        "Question", back_populates="exam_questions"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "exam_session_id", "question_order", name="uq_exam_question_order"
        ),
        Index("idx_exam_question_session", "exam_session_id"),
        Index("idx_exam_question_order", "question_order"),
    )


class StudentAnswer(Base):
    """Öğrenci cevap modeli"""

    __tablename__ = "student_answers"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    exam_session_id: Mapped[str] = mapped_column(
        String, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )

    # Answer information
    selected_answer: Mapped[Optional[str]] = mapped_column(
        String(1)
    )  # A, B, C, D, E or NULL for empty
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    response_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Behavioral data
    answer_changes: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Kaç kez değiştirdi
    time_to_first_answer: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # İlk cevaba kadar geçen süre
    confidence_level: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Güven seviyesi (1-5)

    # System fields
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    exam_session: Mapped["ExamSession"] = relationship(
        "ExamSession", back_populates="student_answers"
    )
    question: Mapped["Question"] = relationship(
        "Question", back_populates="student_answers"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("exam_session_id", "question_id", name="uq_student_answer"),
        CheckConstraint(
            "selected_answer IS NULL OR selected_answer IN ('A', 'B', 'C', 'D', 'E')",
            name="check_selected_answer",
        ),
        Index("idx_student_answer_session", "exam_session_id"),
        Index("idx_student_answer_question", "question_id"),
    )


# Learning Analytics Models
class LearningAnalytics(Base):
    """Öğrenme analitiği modeli"""

    __tablename__ = "learning_analytics"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Analytics data
    date: Mapped[date] = mapped_column(Date, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # Performance metrics
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    questions_correct: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Learning progress
    skill_level: Mapped[float] = mapped_column(Float, default=0.0)  # 0-10 arası
    improvement_rate: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Günlük gelişim oranı
    difficulty_preference: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Tercih edilen zorluk

    # Devrimsel özellik metrikleri
    zpd_utilization: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # ZPD kullanım oranı
    fsrs_retention_rate: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # FSRS hatırlama oranı
    morphology_awareness: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Morfoloji farkındalığı

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile", back_populates="learning_analytics"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "student_id", "date", "subject_area", name="uq_learning_analytics"
        ),
        Index("idx_learning_analytics_student", "student_id"),
        Index("idx_learning_analytics_date", "date"),
        Index("idx_learning_analytics_subject", "subject_area"),
    )


# Content and Resource Models
# Legacy alias for compatibility
EgitimIcerigi = "EducationalContent"


class EducationalContent(Base):
    """Eğitim içeriği modeli"""

    __tablename__ = "educational_contents"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Content information
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # video, article, interactive, quiz

    # Source information
    source_platform: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # youtube, khan_academy, eba_tv
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(
        String(200)
    )  # Platform-specific ID

    # Classification
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    subtopic: Mapped[Optional[str]] = mapped_column(String(200))
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quality metrics
    difficulty_level: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty), nullable=False
    )
    educational_score: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0-1 arası kalite skoru
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Accessibility features
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(10), default="tr")

    # Engagement metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index("idx_content_subject", "subject_area"),
        Index("idx_content_topic", "topic"),
        Index("idx_content_grade", "grade_level"),
        Index("idx_content_difficulty", "difficulty_level"),
        Index("idx_content_score", "educational_score"),
        Index("idx_content_platform", "source_platform"),
    )


# Class and School Management Models
class ClassRoom(Base):
    """Sınıf modeli"""

    __tablename__ = "classrooms"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    teacher_id: Mapped[str] = mapped_column(
        String, ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Class information
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    school_year: Mapped[str] = mapped_column(String(20), nullable=False)  # 2024-2025

    # Student list (JSON array of student IDs)
    student_ids: Mapped[Optional[dict]] = mapped_column(JSON)

    # Class settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_students: Mapped[int] = mapped_column(Integer, default=40)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    teacher: Mapped["TeacherProfile"] = relationship(
        "TeacherProfile", back_populates="classes"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_class_grade_level"
        ),
        Index("idx_classroom_teacher", "teacher_id"),
        Index("idx_classroom_grade", "grade_level"),
        Index("idx_classroom_subject", "subject_area"),
    )


# System and Configuration Models
class RefreshToken(Base):
    """
    JWT Refresh Token modeli (Task 48.4)
    Dual-token authentication system for enhanced security
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Token information
    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )  # JWT ID from token payload

    # Device and session tracking
    device_id: Mapped[Optional[str]] = mapped_column(String(255))
    device_name: Mapped[Optional[str]] = mapped_column(String(200))
    device_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # mobile, desktop, tablet
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv4/IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # Expiration and status
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes and constraints
    __table_args__ = (
        Index("idx_refresh_token_user", "user_id"),
        Index("idx_refresh_token_hash", "token_hash"),
        Index("idx_refresh_token_jti", "jti"),
        Index("idx_refresh_token_expires", "expires_at"),
        Index("idx_refresh_token_revoked", "revoked"),
        Index("idx_refresh_token_user_device", "user_id", "device_id"),
    )


class APIKey(Base):
    """
    API Key modeli (Task 48.6)
    Scoped API keys for third-party integrations
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # API Key information
    key_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    key_prefix: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # First 8 chars for identification
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # Human-readable name
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Permissions and scopes
    scopes: Mapped[Optional[dict]] = mapped_column(JSON)  # List of allowed permissions
    allowed_ips: Mapped[Optional[dict]] = mapped_column(JSON)  # IP whitelist (optional)
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)  # Requests per hour

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(45))

    # Security
    created_from_ip: Mapped[Optional[str]] = mapped_column(String(45))

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes and constraints
    __table_args__ = (
        Index("idx_api_key_user", "user_id"),
        Index("idx_api_key_hash", "key_hash"),
        Index("idx_api_key_prefix", "key_prefix"),
        Index("idx_api_key_active", "is_active"),
        Index("idx_api_key_revoked", "revoked"),
        Index("idx_api_key_expires", "expires_at"),
    )


class SystemConfiguration(Base):
    """Sistem konfigürasyon modeli"""

    __tablename__ = "system_configurations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Configuration
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    config_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # string, integer, float, boolean, json
    description: Mapped[Optional[str]] = mapped_column(Text)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (Index("idx_config_key", "config_key"),)


class AuditLog(Base):
    """Sistem audit log modeli"""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Audit information
    user_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String)

    # Details
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created", "created_at"),
    )


# EBA TV Content Models
class EBAContentCategory(enum.Enum):
    """EBA TV içerik kategorileri"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    INGILIZCE = "ingilizce"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    EDEBIYAT = "edebiyat"


class EBAGradeLevel(enum.Enum):
    """EBA TV sınıf seviyeleri"""

    SINIF_5 = "5"
    SINIF_6 = "6"
    SINIF_7 = "7"
    SINIF_8 = "8"  # LGS
    SINIF_9 = "9"
    SINIF_10 = "10"
    SINIF_11 = "11"
    SINIF_12 = "12"  # YKS


class EBAVideoQuality(enum.Enum):
    """EBA video kalite seviyeleri"""

    LOW = "low"  # 0-4 puan
    MEDIUM = "medium"  # 4-7 puan
    HIGH = "high"  # 7-10 puan


class EBAVideo(Base):
    """EBA TV video modeli"""

    __tablename__ = "eba_videos"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Video bilgileri
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Kategorilendirme
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )
    subject_topics: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Konu başlıkları listesi
    difficulty_level: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty), nullable=False
    )

    # URL ve medya
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    transcript: Mapped[Optional[str]] = mapped_column(Text)

    # Kalite ve değerlendirme
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_category: Mapped[EBAVideoQuality] = mapped_column(
        Enum(EBAVideoQuality), default=EBAVideoQuality.MEDIUM
    )
    curriculum_alignment: Mapped[Optional[dict]] = mapped_column(JSON)  # Müfredat uyumu

    # Erişilebilirlik
    accessibility_features: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Erişilebilirlik özellikleri
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)

    # İstatistikler
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)

    # Kalite analizi detayları
    duration_score: Mapped[float] = mapped_column(Float, default=0.0)
    title_clarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    description_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    curriculum_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    accessibility_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Moderasyon
    moderation_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, approved, rejected, flagged
    moderated_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    moderation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Sistem alanları
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    usage_analytics: Mapped[List["EBAVideoUsage"]] = relationship(
        "EBAVideoUsage", back_populates="video"
    )
    recommendations: Mapped[List["EBAVideoRecommendation"]] = relationship(
        "EBAVideoRecommendation", back_populates="video"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        CheckConstraint(
            "duration_minutes >= 1 AND duration_minutes <= 180",
            name="check_eba_duration",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 10.0",
            name="check_eba_quality_score",
        ),
        Index("idx_eba_video_category", "category"),
        Index("idx_eba_video_grade", "grade_level"),
        Index("idx_eba_video_difficulty", "difficulty_level"),
        Index("idx_eba_video_quality", "quality_score"),
        Index("idx_eba_video_moderation", "moderation_status"),
        Index("idx_eba_video_created", "created_at"),
    )


class EBAVideoUsage(Base):
    """EBA video kullanım istatistikleri"""

    __tablename__ = "eba_video_usage"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("eba_videos.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Kullanım bilgileri
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    watch_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Etkileşim
    paused_count: Mapped[int] = mapped_column(Integer, default=0)
    rewound_count: Mapped[int] = mapped_column(Integer, default=0)
    fast_forwarded_count: Mapped[int] = mapped_column(Integer, default=0)

    # Değerlendirme
    user_rating: Mapped[Optional[float]] = mapped_column(Float)  # 1-5 arası
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Öğrenme etkisi
    pre_knowledge_score: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Video öncesi bilgi seviyesi
    post_knowledge_score: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Video sonrası bilgi seviyesi
    learning_effectiveness: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Öğrenme etkinliği

    # İlişkiler
    video: Mapped["EBAVideo"] = relationship(
        "EBAVideo", back_populates="usage_analytics"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        CheckConstraint(
            "completion_percentage >= 0.0 AND completion_percentage <= 100.0",
            name="check_eba_completion",
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1.0 AND user_rating <= 5.0)",
            name="check_eba_rating",
        ),
        Index("idx_eba_usage_video", "video_id"),
        Index("idx_eba_usage_student", "student_id"),
        Index("idx_eba_usage_started", "started_at"),
        UniqueConstraint(
            "video_id", "student_id", "started_at", name="uq_eba_video_usage"
        ),
    )


class EBAVideoRecommendation(Base):
    """EBA video önerileri"""

    __tablename__ = "eba_video_recommendations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("eba_videos.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Öneri bilgileri
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(String(200), nullable=False)
    recommendation_category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # weak_subject, learning_style, curriculum

    # Kişiselleştirme faktörleri
    learning_style_match: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_appropriateness: Mapped[float] = mapped_column(Float, default=0.0)
    curriculum_relevance: Mapped[float] = mapped_column(Float, default=0.0)

    # Durum takibi
    shown_to_student: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_by_student: Mapped[bool] = mapped_column(Boolean, default=False)
    watched_by_student: Mapped[bool] = mapped_column(Boolean, default=False)

    # Zaman damgaları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    shown_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # İlişkiler
    video: Mapped["EBAVideo"] = relationship(
        "EBAVideo", back_populates="recommendations"
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        CheckConstraint(
            "recommendation_score >= 0.0 AND recommendation_score <= 10.0",
            name="check_eba_rec_score",
        ),
        Index("idx_eba_rec_video", "video_id"),
        Index("idx_eba_rec_student", "student_id"),
        Index("idx_eba_rec_score", "recommendation_score"),
        Index("idx_eba_rec_created", "created_at"),
    )


class EBAContentCollection(Base):
    """EBA içerik koleksiyonları"""

    __tablename__ = "eba_content_collections"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Koleksiyon bilgileri
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )

    # Video listesi (JSON array of video IDs)
    video_ids: Mapped[Optional[dict]] = mapped_column(JSON)

    # İstatistikler
    total_videos: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Durum
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Sistem alanları
    created_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İndeksler
    __table_args__ = (
        Index("idx_eba_collection_category", "category"),
        Index("idx_eba_collection_grade", "grade_level"),
        Index("idx_eba_collection_featured", "is_featured"),
    )


class EBAContentAnalytics(Base):
    """EBA içerik analitikleri"""

    __tablename__ = "eba_content_analytics"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Analiz dönemi
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )

    # Kullanım metrikleri
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    unique_viewers: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Kalite metrikleri
    average_user_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0)
    average_learning_effectiveness: Mapped[float] = mapped_column(Float, default=0.0)

    # Popülerlik metrikleri
    trending_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint(
            "analysis_date", "category", "grade_level", name="uq_eba_analytics"
        ),
        Index("idx_eba_analytics_date", "analysis_date"),
        Index("idx_eba_analytics_category", "category"),
        Index("idx_eba_analytics_grade", "grade_level"),
    )


# FSRS (Spaced Repetition System) Models
class FSRSCard(Base):
    """FSRS flashcard modeli"""

    __tablename__ = "fsrs_cards"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Kart içeriği
    front_text: Mapped[str] = mapped_column(Text, nullable=False)
    back_text: Mapped[str] = mapped_column(Text, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)

    # FSRS parametreleri
    stability: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)

    # Durum
    state: Mapped[str] = mapped_column(
        String(20), default="new"
    )  # new, learning, review, relearning
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Türk öğrenci özel faktörleri
    cultural_factors: Mapped[Optional[dict]] = mapped_column(JSON)  # Kültürel faktörler

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_cards")
    reviews: Mapped[List["FSRSReview"]] = relationship(
        "FSRSReview", back_populates="card"
    )

    # İndeksler
    __table_args__ = (
        Index("idx_fsrs_card_student", "student_id"),
        Index("idx_fsrs_card_due", "due_date"),
        Index("idx_fsrs_card_subject", "subject_area"),
        Index("idx_fsrs_card_state", "state"),
    )


class FSRSReview(Base):
    """FSRS review kayıtları"""

    __tablename__ = "fsrs_reviews"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    card_id: Mapped[str] = mapped_column(
        String, ForeignKey("fsrs_cards.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Review bilgileri
    grade: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1-4 (Again, Hard, Good, Easy)
    review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    response_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # FSRS hesaplamaları
    old_stability: Mapped[float] = mapped_column(Float, default=0.0)
    new_stability: Mapped[float] = mapped_column(Float, default=0.0)
    old_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    new_difficulty: Mapped[float] = mapped_column(Float, default=0.0)

    # Kültürel faktör etkisi
    cultural_adjustment: Mapped[float] = mapped_column(Float, default=1.0)

    # İlişkiler - using fully qualified path
    card: Mapped["FSRSCard"] = relationship(
        "models.database.FSRSCard", back_populates="reviews"
    )
    student: Mapped["User"] = relationship("User", back_populates="fsrs_reviews")

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        CheckConstraint("grade >= 1 AND grade <= 4", name="check_fsrs_grade"),
        Index("idx_fsrs_review_card", "card_id"),
        Index("idx_fsrs_review_student", "student_id"),
        Index("idx_fsrs_review_date", "review_date"),
    )


class FSRSSchedule(Base):
    """FSRS zamanlama tablosu"""

    __tablename__ = "fsrs_schedules"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Zamanlama bilgileri
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_cards_due: Mapped[int] = mapped_column(Integer, default=0)
    new_cards: Mapped[int] = mapped_column(Integer, default=0)
    review_cards: Mapped[int] = mapped_column(Integer, default=0)

    # Performans metrikleri
    cards_studied: Mapped[int] = mapped_column(Integer, default=0)
    study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Türk öğrenci adaptasyonu
    cultural_period: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # ramadan, exam_season, summer_break
    adjustment_factor: Mapped[float] = mapped_column(Float, default=1.0)

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_schedules")

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint("student_id", "schedule_date", name="uq_fsrs_schedule"),
        Index("idx_fsrs_schedule_student", "student_id"),
        Index("idx_fsrs_schedule_date", "schedule_date"),
    )


class FSRSStudentProfile(Base):
    """FSRS öğrenci profili"""

    __tablename__ = "fsrs_student_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # FSRS parametreleri (17 parametre)
    fsrs_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Türk öğrenci özel parametreleri
    cultural_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)

    # İstatistikler
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    average_retention: Mapped[float] = mapped_column(Float, default=0.0)
    study_streak_days: Mapped[int] = mapped_column(Integer, default=0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_profile")

    # İndeksler
    __table_args__ = (Index("idx_fsrs_profile_student", "student_id"),)


class FSRSStudySession(Base):
    """FSRS çalışma oturumları"""

    __tablename__ = "fsrs_study_sessions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Oturum bilgileri
    session_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    cards_reviewed: Mapped[int] = mapped_column(Integer, default=0)

    # Performans
    correct_reviews: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Kültürel bağlam
    cultural_context: Mapped[Optional[dict]] = mapped_column(JSON)

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_study_sessions")

    # İndeksler
    __table_args__ = (
        Index("idx_fsrs_session_student", "student_id"),
        Index("idx_fsrs_session_date", "session_date"),
    )


class FSRSSubjectStats(Base):
    """FSRS konu bazlı istatistikler"""

    __tablename__ = "fsrs_subject_stats"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # İstatistikler
    total_cards: Mapped[int] = mapped_column(Integer, default=0)
    mature_cards: Mapped[int] = mapped_column(Integer, default=0)  # Stability > 21 gün
    average_stability: Mapped[float] = mapped_column(Float, default=0.0)
    average_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Zaman damgaları
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_subject_stats")

    # İndeksler ve kısıtlamalar
    __table_args__ = (
        UniqueConstraint("student_id", "subject_area", name="uq_fsrs_subject_stats"),
        Index("idx_fsrs_stats_student", "student_id"),
        Index("idx_fsrs_stats_subject", "subject_area"),
    )


# ============================================================================
# MANIPULATIVES MODELS (Task 87.9)
# REQ-51.101-51.105: Progress tracking, badges, achievements
# ============================================================================


class ManipulativeProgress(Base):
    """Manipulative usage progress tracking"""

    __tablename__ = "manipulative_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(
        String(50), nullable=False
    )  # virtualBlocks, geogebra, geometry, tangram
    activity_type = Column(String(50))  # add, subtract, geometry, algebra, etc.

    # Progress metrics
    operation_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, default=0.0)
    mastery_level = Column(Float, default=0.0)  # 0-100

    # Activity details
    activity_data = Column(JSON)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="manipulative_progress")

    # Indexes
    __table_args__ = (
        Index("idx_manip_progress_user", "user_id"),
        Index("idx_manip_progress_type", "manipulative_type"),
        Index("idx_manip_progress_user_type", "user_id", "manipulative_type"),
    )


class ManipulativeActivity(Base):
    """Individual manipulative activity log"""

    __tablename__ = "manipulative_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(String(50), nullable=False)
    activity_type = Column(String(50))

    # Activity metrics
    duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)

    # Activity details
    details = Column(JSON)  # Specific activity data

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="manipulative_activities")

    # Indexes
    __table_args__ = (
        Index("idx_manip_activity_user", "user_id"),
        Index("idx_manip_activity_created", "created_at"),
        Index("idx_manip_activity_user_created", "user_id", "created_at"),
    )


class WeeklyProgress(Base):
    """Weekly progress tracking"""

    __tablename__ = "weekly_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Week info
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)  # 1-52

    # Metrics
    total_activities = Column(Integer, default=0)
    total_time_seconds = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)

    # Daily breakdown
    daily_data = Column(JSON)  # {day: {activities: X, time: Y}}

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="weekly_progress")

    # Indexes
    __table_args__ = (
        UniqueConstraint("user_id", "year", "week_number", name="uq_weekly_progress"),
        Index("idx_weekly_progress_user", "user_id"),
        Index("idx_weekly_progress_year_week", "year", "week_number"),
    )


# Import gamification models at the end to avoid circular imports
# These are referenced in User model relationships (lines 151-157)
from .user_badge import UserBadge  # noqa: E402, F401
from .user_achievement import UserAchievement  # noqa: E402, F401
from .point_transaction import PointTransaction  # noqa: E402, F401

# Removed duplicate - use get_db_session from core.database instead
