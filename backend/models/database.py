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
# Re-export Analytics models
from .analytics_db import LearningAnalytics
from .base import Base

# Re-export Content models
from .content_db import (
    ClassRoom,
    EducationalContent,
    EgitimIcerigi,  # Legacy alias
)

# Re-export Curriculum models
from .curriculum_db import (
    CurriculumAlignmentDB,
    CurriculumUpdateRequestDB,
    LearningOutcomeDB,
    MEBCurriculumStandardDB,
    OSYMStandardDB,
)

# Re-export EBA models
from .eba_models import (
    EBAContentAnalytics,
    EBAContentCollection,
    EBAVideo,
    EBAVideoRecommendation,
    EBAVideoUsage,
)

# Re-export Enums
from .enums_db import (
    EBAContentCategory,
    EBAGradeLevel,
    EBAVideoQuality,
    ExamType,
    LearningStyle,
    QuestionDifficulty,
    SubjectArea,
    UserRole,
)

# Re-export Exam models
from .exam_db import (
    ExamQuestion,
    ExamSession,
    StudentAnswer,
)

# Re-export FSRS models
from .fsrs_models import (
    FSRSCard,
    FSRSReview,
    FSRSSchedule,
    FSRSStudentProfile,
    FSRSStudySession,
    FSRSSubjectStats,
)

# Re-export Gamification/Manipulatives models
from .gamification_db import (
    ManipulativeActivity,
    ManipulativeProgress,
    WeeklyProgress,
)
from .notification import Notification

# Re-export Pedagogy models (İçerik Zehirlenmesi filtreleri + Kavram Yanılgısı)
from .pedagogy_models import (
    MEBCurriculumNode,
    MisconceptionMatrix,
    MisconceptionRemedy,
)
from .point_transaction import PointTransaction

# Re-export Quality Gates models
from .quality_gates_db import (
    GateResultRecord,
    OverrideAuditLog,
    QualityGatesRun,
)
from .reports_models import (
    ClassReport,
    ParentApproval,
    ParentReport,
    StudentGrade,
)

# Re-export Report models (StudentGoal, Notification moved to canonical files)
from .student_goal import StudentGoal

# Re-export System models
from .system_models import (
    APIKey,
    AuditLog,
    RefreshToken,
    Session,
    SystemConfiguration,
)
from .user_achievement import UserAchievement

# Import gamification models for User relationships
from .user_badge import UserBadge

# Re-export User models
from .user_models import (
    ParentProfile,
    StudentProfile,
    TeacherProfile,
    User,
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
    # Pedagogy models
    "MEBCurriculumNode",
    "MisconceptionMatrix",
    "MisconceptionRemedy",
]
