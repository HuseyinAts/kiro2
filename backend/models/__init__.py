# -*- coding: utf-8 -*-
"""
Models Package
Tüm model sınıflarını export et

CANONICAL MODELS:
- LearningPathStudentProfile: Primary student profile model for learning paths

DEPRECATED MODELS (will be removed in v3.0.0):
- StudentProfile (user_models.py): Use for general user profile only
- StudentLearningProfile: Use LearningPathStudentProfile instead
"""

# Base import (avoid circular import)
from .base import Base

# Canonical Learning Path Models
from .learning_path_models import (
    LearningPathStudentProfile,  # Canonical student profile
    LearningPath,
    TopicCompletion,
    TopicProgress,
    QuizSubmission,
    FallbackVideo,
)

# SQLAlchemy ORM models
from .database import (
    # Enums
    UserRole,
    ExamType,
    QuestionDifficulty,
    LearningStyle,
    SubjectArea,
    # User models
    User,
    StudentProfile,
    TeacherProfile,
    ParentProfile,
    # Question and Exam models
    Question,
    ExamSession,
    ExamQuestion,
    StudentAnswer,
    # Analytics models
    LearningAnalytics,
    WeeklyProgress,  # Added for dashboard service
    # Content models
    EducationalContent,
    EgitimIcerigi,
    # Class management models
    ClassRoom,
    # System models
    SystemConfiguration,
    AuditLog,
    # FSRS models
    FSRSCard,
    FSRSSchedule,
    FSRSReview,
    FSRSStudentProfile,
    FSRSStudySession,
    FSRSSubjectStats,
)

# Enums
from .enums import (
    SinavDurumu,
    SinavTipi,
    TurkishExamType,
    ZorlukSeviyesi,
    OgrenmeStili,
    IcerikTipi,
    KullaniciRolu,
    RaporTipi,
    KarsilastirmaGrubu,
)

# Exam models
from .exam import (
    SinavSorusu,
    SinavOturumu,
    SinavCevabi,
    KonuPerformansi,
    SinavSonucu,
    PerformansRaporu,
)

# Content models
from .content_models import (
    MakaleIcerik,
    VideoIcerik,
    QuizIcerik,
    ContentType,
    ContentStats,
    ContentInteraction,
    InteractionType,
    ContentFilter,
    ContentSearchRequest,
    BulkContentImport,
)

# Dashboard models (Mock Data Cleanup - Phase 2)
from .student_goal import StudentGoal
from .notification import Notification

# Learning Style models (Mock Data Cleanup - Phase 4)
# DEPRECATED: Use LearningPathStudentProfile instead
from .student_learning_profile import StudentLearningProfile

# Migration utilities
from .profile_migration import (
    ProfileMigrationService,
    check_migration_status,
    validate_canonical_profile,
)

# Pydantic models
from .user import (
    Kullanici,
    KullaniciOlustur,
    KullaniciGiris,
    OgrenciProfili,
    OgretmenProfili,
    VeliProfili,
    TokenYaniti,
)

# Backward compatibility aliases - for tests expecting these names
Question = Question  # Already imported from database
Student = StudentProfile  # Alias for StudentProfile

# Faz 2: Study Planner, Leagues, Coaching models
from .study_planner import StudyPlan, WeeklyGoal
from .league import LeagueMembership, LeagueHistory
from .coaching import CoachingEvent, StudentEngagementSignal

# Faz 3: Duel models
from .duel import DuelMatch, DuelRating, DuelSession

# Faz 4: DINA Cognitive Diagnostic models
from .dina import DINAParameter, NanoSkill, QMatrix, StudentNanoSkillMastery

# Faz 5: Error Cluster models
from .error_cluster import ErrorCluster, PeerRecommendation

# Faz 4 (Knowledge Graph): Knowledge Points, Question mappings, Student mastery
from .knowledge_graph import KnowledgePoint, QuestionKnowledgeMapping, StudentKnowledgeState

# Convenience alias pointing to canonical model
CanonicalStudentProfile = LearningPathStudentProfile

__all__ = [
    # Base
    "Base",
    # Canonical Models
    "LearningPathStudentProfile",  # PRIMARY student profile model
    "LearningPath",
    "TopicCompletion",
    "TopicProgress",
    "QuizSubmission",
    "FallbackVideo",
    # SQLAlchemy Enums
    "UserRole",
    "ExamType",
    "QuestionDifficulty",
    "LearningStyle",
    "SubjectArea",
    # User models
    "User",
    "StudentProfile",  # NOTE: For user-related data only, use LearningPathStudentProfile for learning
    "TeacherProfile",
    "ParentProfile",
    # Question and Exam models
    "Question",
    "ExamSession",
    "ExamQuestion",
    "StudentAnswer",
    # Analytics models
    "LearningAnalytics",
    "WeeklyProgress",
    # Content models
    "EducationalContent",
    "EgitimIcerigi",
    "MakaleIcerik",
    "VideoIcerik",
    "QuizIcerik",
    "ContentType",
    "ContentStats",
    "ContentInteraction",
    "InteractionType",
    "ContentFilter",
    "ContentSearchRequest",
    "BulkContentImport",
    # Class management models
    "ClassRoom",
    # System models
    "SystemConfiguration",
    "AuditLog",
    # Dashboard models
    "StudentGoal",
    "Notification",
    # Learning Style models (DEPRECATED)
    "StudentLearningProfile",  # DEPRECATED: Use LearningPathStudentProfile
    # Migration utilities
    "ProfileMigrationService",
    "check_migration_status",
    "validate_canonical_profile",
    # FSRS models
    "FSRSCard",
    "FSRSSchedule",
    "FSRSReview",
    "FSRSStudentProfile",
    "FSRSStudySession",
    "FSRSSubjectStats",
    # Pydantic models
    "Kullanici",
    "KullaniciOlustur",
    "KullaniciGiris",
    "OgrenciProfili",
    "OgretmenProfili",
    "VeliProfili",
    "TokenYaniti",
    # Exam models
    "SinavSorusu",
    "SinavOturumu",
    "SinavCevabi",
    "KonuPerformansi",
    "SinavSonucu",
    "PerformansRaporu",
    # Enums
    "SinavTipi",
    "TurkishExamType",
    "SinavDurumu",
    "ZorlukSeviyesi",
    "OgrenmeStili",
    "IcerikTipi",
    "KullaniciRolu",
    "RaporTipi",
    "KarsilastirmaGrubu",
    # Faz 2: Study Planner, Leagues, Coaching
    "StudyPlan",
    "WeeklyGoal",
    "LeagueMembership",
    "LeagueHistory",
    "CoachingEvent",
    "StudentEngagementSignal",
    # Faz 3: Duel
    "DuelSession",
    "DuelMatch",
    "DuelRating",
    # Faz 4: DINA
    "NanoSkill",
    "QMatrix",
    "DINAParameter",
    "StudentNanoSkillMastery",
    # Faz 5: Error Clusters
    "ErrorCluster",
    "PeerRecommendation",
    # Faz 4 (Knowledge Graph)
    "KnowledgePoint",
    "QuestionKnowledgeMapping",
    "StudentKnowledgeState",
    # Aliases for backward compatibility
    "Student",
    "CanonicalStudentProfile",  # Alias for LearningPathStudentProfile
]
