"""
SQLAlchemy ORM Models - Backward Compatibility Layer
Türkiye Üniversite Sınavları Hazırlık Platformu için database modelleri

Bu dosya artık sadece re-export içerir.
Modeller domain dosyalarına ayrıştırıldı (2026-01-10):
- enums_db.py: Enum tanımları
- user_models.py: User, StudentProfile, TeacherProfile, ParentProfile
- content_db.py: Question, EducationalContent, ClassRoom
- exam_db.py: ExamSession, ExamQuestion, StudentAnswer
- analytics_db.py: LearningAnalytics
- fsrs_models.py: FSRS* modelleri
- eba_models.py: EBA* modelleri
- gamification_db.py: Manipulative*, WeeklyProgress
- system_models.py: RefreshToken, APIKey, SystemConfiguration, AuditLog, Session
- reports_models.py: StudentGoal, Notification, ParentReport, ParentApproval, StudentGrade, ClassReport
"""

# Re-export Base
from .base import Base

# Re-export Enums
from .enums_db import (
    UserRole,
    ExamType,
    QuestionDifficulty,
    LearningStyle,
    SubjectArea,
    EBAContentCategory,
    EBAGradeLevel,
    EBAVideoQuality,
)

# Re-export User models
from .user_models import (
    User,
    StudentProfile,
    TeacherProfile,
    ParentProfile,
)

# Re-export Content models
from .content_db import (
    Question,
    EducationalContent,
    EgitimIcerigi,  # Legacy alias
    ClassRoom,
)

# Re-export Exam models
from .exam_db import (
    ExamSession,
    ExamQuestion,
    StudentAnswer,
)

# Re-export Analytics models
from .analytics_db import LearningAnalytics

# Re-export FSRS models
from .fsrs_models import (
    FSRSCard,
    FSRSReview,
    FSRSSchedule,
    FSRSStudentProfile,
    FSRSStudySession,
    FSRSSubjectStats,
)

# Re-export EBA models
from .eba_models import (
    EBAVideo,
    EBAVideoUsage,
    EBAVideoRecommendation,
    EBAContentCollection,
    EBAContentAnalytics,
)

# Re-export Gamification/Manipulatives models
from .gamification_db import (
    ManipulativeProgress,
    ManipulativeActivity,
    WeeklyProgress,
)

# Re-export System models
from .system_models import (
    RefreshToken,
    APIKey,
    SystemConfiguration,
    AuditLog,
    Session,
)

# Re-export Report models
from .reports_models import (
    StudentGoal,
    Notification,
    ParentReport,
    ParentApproval,
    StudentGrade,
    ClassReport,
)

# Import gamification models for User relationships
from .user_badge import UserBadge  # noqa: F401
from .user_achievement import UserAchievement  # noqa: F401
from .point_transaction import PointTransaction  # noqa: F401

# Re-export Quality Gates models
from .quality_gates_db import (
    QualityGatesRun,
    GateResultRecord,
    OverrideAuditLog,
)

# Re-export Curriculum models
from .curriculum_db import (
    MEBCurriculumStandardDB,
    OSYMStandardDB,
    LearningOutcomeDB,
    CurriculumAlignmentDB,
    CurriculumUpdateRequestDB,
)


__all__ = [
    # Base
    "Base",
    # Enums
    "UserRole",
    "ExamType",
    "QuestionDifficulty",
    "LearningStyle",
    "SubjectArea",
    "EBAContentCategory",
    "EBAGradeLevel",
    "EBAVideoQuality",
    # User models
    "User",
    "StudentProfile",
    "TeacherProfile",
    "ParentProfile",
    # Content models
    "Question",
    "EducationalContent",
    "EgitimIcerigi",
    "ClassRoom",
    # Exam models
    "ExamSession",
    "ExamQuestion",
    "StudentAnswer",
    # Analytics models
    "LearningAnalytics",
    # FSRS models
    "FSRSCard",
    "FSRSReview",
    "FSRSSchedule",
    "FSRSStudentProfile",
    "FSRSStudySession",
    "FSRSSubjectStats",
    # EBA models
    "EBAVideo",
    "EBAVideoUsage",
    "EBAVideoRecommendation",
    "EBAContentCollection",
    "EBAContentAnalytics",
    # Gamification models
    "ManipulativeProgress",
    "ManipulativeActivity",
    "WeeklyProgress",
    # System models
    "RefreshToken",
    "APIKey",
    "SystemConfiguration",
    "AuditLog",
    "Session",
    # Report models
    "StudentGoal",
    "Notification",
    "ParentReport",
    "ParentApproval",
    "StudentGrade",
    "ClassReport",
    # Gamification extras
    "UserBadge",
    "UserAchievement",
    "PointTransaction",
    # Quality Gates models
    "QualityGatesRun",
    "GateResultRecord",
    "OverrideAuditLog",
    # Curriculum models
    "MEBCurriculumStandardDB",
    "OSYMStandardDB",
    "LearningOutcomeDB",
    "CurriculumAlignmentDB",
    "CurriculumUpdateRequestDB",
]
