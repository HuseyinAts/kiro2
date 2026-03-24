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
from .birlikte_streak import StreakDailyLog, StreakPair

# Faz 2: Study Planner, Leagues, Coaching models
from .coaching import CoachingEvent, StudentEngagementSignal

# Content models
from .content_models import (
    BulkContentImport,
    ContentFilter,
    ContentInteraction,
    ContentSearchRequest,
    ContentStats,
    ContentType,
    InteractionType,
    MakaleIcerik,
    QuizIcerik,
    VideoIcerik,
)
from .cozum_duellosu import SolutionDuel, SolutionDuelSubmission, SolutionDuelVote

# SQLAlchemy ORM models
from .database import (
    AuditLog,
    # Class management models
    ClassRoom,
    # Content models
    EducationalContent,
    EgitimIcerigi,
    ExamQuestion,
    ExamSession,
    ExamType,
    # FSRS models
    FSRSCard,
    FSRSReview,
    FSRSSchedule,
    FSRSStudentProfile,
    FSRSStudySession,
    FSRSSubjectStats,
    # Analytics models
    LearningAnalytics,
    LearningStyle,
    ParentProfile,
    # Question and Exam models
    Question,
    QuestionDifficulty,
    StudentAnswer,
    StudentProfile,
    SubjectArea,
    # System models
    SystemConfiguration,
    TeacherProfile,
    # User models
    User,
    # Enums
    UserRole,
    WeeklyProgress,  # Added for dashboard service
)

# Faz 4: DINA Cognitive Diagnostic models
from .dina import DINAParameter, NanoSkill, QMatrix, StudentNanoSkillMastery

# Faz 3: Duel models
from .duel import DuelMatch, DuelRating, DuelSession

# Enums
from .enums import (
    IcerikTipi,
    KarsilastirmaGrubu,
    KullaniciRolu,
    OgrenmeStili,
    RaporTipi,
    SinavDurumu,
    SinavTipi,
    TurkishExamType,
    ZorlukSeviyesi,
)

# Faz 5: Error Cluster models
from .error_cluster import ErrorCluster, PeerRecommendation

# Exam models
from .exam import (
    KonuPerformansi,
    PerformansRaporu,
    SinavCevabi,
    SinavOturumu,
    SinavSonucu,
    SinavSorusu,
)

# Gamification models (Master Plan v2.0)
from .gamification import (
    Badge,
    BKTState,
    Duel,
    Oba,
    ObaUye,
    ParentChild,
    Realm,
    RealmProgress,
    Streak,
    StudentAbility,
    UserBadge,
    XPTransaction,
)
from .gamification_db import (
    ManipulativeActivity,
    ManipulativeProgress,
)

# Faz 4 (Knowledge Graph): Knowledge Points, Question mappings, Student mastery
from .knowledge_graph import (
    KnowledgePoint,
    QuestionKnowledgeMapping,
    StudentKnowledgeState,
)
from .league import LeagueHistory, LeagueMembership

# Canonical Learning Path Models
from .learning_path_models import (
    FallbackVideo,
    LearningPath,
    LearningPathStudentProfile,  # Canonical student profile
    QuizSubmission,
    TopicCompletion,
    TopicProgress,
)
from .notification import Notification
from .oba_seferleri import ObaChallenge, ObaChallengeProgress
from .pomodoro import PomodoroParticipant, PomodoroRoom

# Migration utilities
from .profile_migration import (
    ProfileMigrationService,
    check_migration_status,
    validate_canonical_profile,
)

# Social Safety (F0)
from .social_safety import (
    BlockedUser,
    ContentReport,
    MessageAuditLog,
    ModerationAction,
    ParentSocialSettings,
)

# Social Features (F1-F6)
from .soru_meydani import ForumQuestion, ForumSolution, ForumVote

# Dashboard models (Mock Data Cleanup - Phase 2)
from .student_goal import StudentGoal

# Learning Style models (Mock Data Cleanup - Phase 4)
# DEPRECATED: Use LearningPathStudentProfile instead
from .student_learning_profile import StudentLearningProfile
from .study_planner import StudyPlan, WeeklyGoal

# Pydantic models
from .user import (
    Kullanici,
    KullaniciGiris,
    KullaniciOlustur,
    OgrenciProfili,
    OgretmenProfili,
    TokenYaniti,
    VeliProfili,
)
from .usta_cirak import MentorFeedback, MentorPair, MentorSession

# DEPRECATED: Use StudentProfile directly
Student = StudentProfile
# DEPRECATED: Use LearningPathStudentProfile directly
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
    # Gamification (Master Plan v2.0)
    "BKTState",
    "Realm",
    "RealmProgress",
    "Streak",
    "XPTransaction",
    "Oba",
    "ObaUye",
    "Badge",
    "UserBadge",
    "Duel",
    "ParentChild",
    "StudentAbility",
    "ManipulativeActivity",
    "ManipulativeProgress",
    # Social Safety (F0)
    "ContentReport",
    "ModerationAction",
    "BlockedUser",
    "ParentSocialSettings",
    "MessageAuditLog",
    # Social Features (F1-F6)
    "ForumQuestion",
    "ForumSolution",
    "ForumVote",
    "PomodoroRoom",
    "PomodoroParticipant",
    "StreakPair",
    "StreakDailyLog",
    "MentorPair",
    "MentorSession",
    "MentorFeedback",
    # Social Features (F2, F3)
    "SolutionDuel",
    "SolutionDuelSubmission",
    "SolutionDuelVote",
    "ObaChallenge",
    "ObaChallengeProgress",
    # Aliases for backward compatibility
    "Student",
    "CanonicalStudentProfile",  # Alias for LearningPathStudentProfile
]
