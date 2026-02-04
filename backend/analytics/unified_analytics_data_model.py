"""
KIRO2 Unified Analytics Data Model
Comprehensive analytics data model for Turkish exam platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Analitik Veri Modeli
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.ANALYTICS)
config = get_unified_config()


class TurkishExamType(Enum):
    """Turkish exam types"""

    TYT = "tyt"  # Temel Yeterlilik Testi
    AYT = "ayt"  # Alan Yeterlilik Testi
    YKS = "yks"  # Yükseköğretim Kurumları Sınavı
    MSU = "msu"  # Matematik ve Fen Bilimleri Testi
    DIL = "dil"  # Yabancı Dil Testi


class TurkishSubject(Enum):
    """Turkish education subjects"""

    MATEMATIK = "matematik"
    GEOMETRI = "geometri"
    TURKCE = "turkce"
    EDEBIYAT = "edebiyat"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    DIN = "din"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    INGILIZCE = "ingilizce"
    ALMANCA = "almanca"
    FRANSIZCA = "fransizca"


class AnalyticsEventType(Enum):
    """Analytics event types"""

    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE_UPDATE = "user_profile_update"

    # Exam events
    EXAM_START = "exam_start"
    EXAM_PAUSE = "exam_pause"
    EXAM_RESUME = "exam_resume"
    EXAM_COMPLETE = "exam_complete"
    EXAM_ABANDON = "exam_abandon"

    # Question events
    QUESTION_VIEW = "question_view"
    QUESTION_ANSWER = "question_answer"
    QUESTION_SKIP = "question_skip"
    QUESTION_REVIEW = "question_review"
    QUESTION_FLAG = "question_flag"

    # Learning events
    CONTENT_VIEW = "content_view"
    VIDEO_WATCH = "video_watch"
    PRACTICE_START = "practice_start"
    PRACTICE_COMPLETE = "practice_complete"

    # Performance events
    SCORE_ACHIEVEMENT = "score_achievement"
    MILESTONE_REACHED = "milestone_reached"
    PROGRESS_UPDATE = "progress_update"

    # System events
    PAGE_VIEW = "page_view"
    API_CALL = "api_call"
    ERROR_OCCURRED = "error_occurred"


class PerformanceLevel(Enum):
    """Student performance levels"""

    EXCELLENT = "excellent"  # Mükemmel (450-500 TYT)
    VERY_GOOD = "very_good"  # Çok İyi (400-449 TYT)
    GOOD = "good"  # İyi (350-399 TYT)
    AVERAGE = "average"  # Orta (300-349 TYT)
    BELOW_AVERAGE = "below_average"  # Ortanın Altı (250-299 TYT)
    WEAK = "weak"  # Zayıf (200-249 TYT)
    VERY_WEAK = "very_weak"  # Çok Zayıf (150-199 TYT)
    CRITICAL = "critical"  # Kritik (0-149 TYT)


@dataclass
class TurkishEducationContext:
    """Turkish education system context"""

    grade_level: int  # Sınıf seviyesi (9-12)
    school_type: str  # Okul türü (anadolu_lisesi, fen_lisesi, meslek_lisesi, etc.)
    city: str  # Şehir
    region: str  # Bölge (marmara, ege, akdeniz, etc.)
    school_name: Optional[str] = None
    district: Optional[str] = None  # İlçe
    education_year: str = "2024-2025"  # Eğitim öğretim yılı
    curriculum_type: str = "2018"  # Müfredat türü

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "grade_level": self.grade_level,
            "school_type": self.school_type,
            "city": self.city,
            "region": self.region,
            "school_name": self.school_name,
            "district": self.district,
            "education_year": self.education_year,
            "curriculum_type": self.curriculum_type,
        }


@dataclass
class ExamMetrics:
    """Comprehensive exam performance metrics"""

    exam_id: str
    exam_type: TurkishExamType
    total_questions: int
    answered_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    score: Decimal
    max_possible_score: Decimal
    percentile: Optional[float] = None  # Yüzdelik dilim

    # Time metrics
    total_time_seconds: int
    average_time_per_question: float
    fastest_answer_time: Optional[float] = None
    slowest_answer_time: Optional[float] = None

    # Subject breakdown
    subject_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Turkish exam specific metrics
    net_score: Optional[Decimal] = None  # Net puan (doğru - yanlış/4)
    raw_score: Optional[Decimal] = None  # Ham puan
    weighted_score: Optional[Decimal] = None  # Ağırlıklı puan

    # Difficulty analysis
    easy_questions_correct: int = 0
    medium_questions_correct: int = 0
    hard_questions_correct: int = 0

    def calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

    def calculate_net_score(self) -> Decimal:
        """Calculate net score (Turkish system)"""
        if self.net_score is None:
            penalty = self.wrong_answers / 4  # 4 yanlış 1 doğruyu götürür
            self.net_score = Decimal(str(max(0, self.correct_answers - penalty)))
        return self.net_score

    def get_performance_level(self) -> PerformanceLevel:
        """Get performance level based on Turkish standards"""
        score_float = float(self.score)

        if score_float >= 450:
            return PerformanceLevel.EXCELLENT
        elif score_float >= 400:
            return PerformanceLevel.VERY_GOOD
        elif score_float >= 350:
            return PerformanceLevel.GOOD
        elif score_float >= 300:
            return PerformanceLevel.AVERAGE
        elif score_float >= 250:
            return PerformanceLevel.BELOW_AVERAGE
        elif score_float >= 200:
            return PerformanceLevel.WEAK
        elif score_float >= 150:
            return PerformanceLevel.VERY_WEAK
        else:
            return PerformanceLevel.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "exam_id": self.exam_id,
            "exam_type": self.exam_type.value,
            "total_questions": self.total_questions,
            "answered_questions": self.answered_questions,
            "correct_answers": self.correct_answers,
            "wrong_answers": self.wrong_answers,
            "empty_answers": self.empty_answers,
            "score": str(self.score),
            "max_possible_score": str(self.max_possible_score),
            "percentile": self.percentile,
            "total_time_seconds": self.total_time_seconds,
            "average_time_per_question": self.average_time_per_question,
            "subject_scores": self.subject_scores,
            "net_score": str(self.net_score) if self.net_score else None,
            "success_rate": self.calculate_success_rate(),
            "performance_level": self.get_performance_level().value,
        }


@dataclass
class StudentPerformanceProfile:
    """Comprehensive student performance profile"""

    student_id: int
    education_context: TurkishEducationContext

    # Overall metrics
    total_exams_taken: int = 0
    total_study_hours: Decimal = Decimal("0")
    total_questions_answered: int = 0
    overall_success_rate: float = 0.0

    # Current performance
    current_tyt_score: Optional[Decimal] = None
    current_ayt_score: Optional[Decimal] = None
    current_yks_score: Optional[Decimal] = None
    current_ranking: Optional[int] = None

    # Subject strengths and weaknesses
    subject_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    strongest_subjects: List[str] = field(default_factory=list)
    weakest_subjects: List[str] = field(default_factory=list)

    # Progress tracking
    performance_trend: str = "stable"  # improving, declining, stable
    last_30_days_progress: Dict[str, float] = field(default_factory=dict)
    goal_progress: Dict[str, float] = field(default_factory=dict)

    # Time analytics
    average_study_session_minutes: float = 0.0
    preferred_study_times: List[str] = field(default_factory=list)
    most_productive_hours: List[int] = field(default_factory=list)

    # Turkish exam specific
    tyt_subject_breakdown: Dict[str, Any] = field(default_factory=dict)
    ayt_field_preference: Optional[str] = None  # sayisal, sozel, esit_agirlik
    target_university: Optional[str] = None
    target_department: Optional[str] = None
    probability_of_success: Optional[float] = None

    # Behavioral analytics
    question_answering_patterns: Dict[str, Any] = field(default_factory=dict)
    exam_taking_behavior: Dict[str, Any] = field(default_factory=dict)
    learning_preferences: Dict[str, Any] = field(default_factory=dict)

    def calculate_yks_prediction(self) -> Dict[str, Any]:
        """Calculate YKS success prediction"""
        if not self.current_tyt_score:
            return {"prediction": "insufficient_data"}

        tyt_score = float(self.current_tyt_score)
        ayt_score = float(self.current_ayt_score or 0)

        # Simplified YKS calculation (actual formula is more complex)
        yks_score = (tyt_score * 0.4) + (ayt_score * 0.6)

        # University placement probability (simplified)
        if yks_score >= 450:
            placement_probability = 0.95
            tier = "top_tier"
        elif yks_score >= 400:
            placement_probability = 0.85
            tier = "high_tier"
        elif yks_score >= 350:
            placement_probability = 0.70
            tier = "mid_tier"
        elif yks_score >= 300:
            placement_probability = 0.50
            tier = "lower_tier"
        else:
            placement_probability = 0.20
            tier = "challenging"

        return {
            "predicted_yks_score": yks_score,
            "placement_probability": placement_probability,
            "tier": tier,
            "recommendation": self._generate_recommendation(yks_score),
        }

    def _generate_recommendation(self, yks_score: float) -> str:
        """Generate study recommendation in Turkish"""
        if yks_score >= 450:
            return "Mükemmel performans! Hedef üniversitenizi rahatça kazanabilirsiniz."
        elif yks_score >= 400:
            return "Çok iyi durumdayız! Zayıf alanlarınızı güçlendirmeye odaklanın."
        elif yks_score >= 350:
            return "İyi seviyede! Düzenli çalışma ile hedeflerinize ulaşabilirsiniz."
        elif yks_score >= 300:
            return "Daha fazla çaba gerekli. Zayıf konularınızı tespit edip yoğunlaşın."
        else:
            return "Temel konuları güçlendirmeniz şart. Sistematik çalışma planı yapın."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "student_id": self.student_id,
            "education_context": self.education_context.to_dict(),
            "total_exams_taken": self.total_exams_taken,
            "total_study_hours": str(self.total_study_hours),
            "total_questions_answered": self.total_questions_answered,
            "overall_success_rate": self.overall_success_rate,
            "current_tyt_score": str(self.current_tyt_score)
            if self.current_tyt_score
            else None,
            "current_ayt_score": str(self.current_ayt_score)
            if self.current_ayt_score
            else None,
            "current_yks_score": str(self.current_yks_score)
            if self.current_yks_score
            else None,
            "subject_performance": self.subject_performance,
            "strongest_subjects": self.strongest_subjects,
            "weakest_subjects": self.weakest_subjects,
            "performance_trend": self.performance_trend,
            "yks_prediction": self.calculate_yks_prediction(),
        }


@dataclass
class AnalyticsEvent:
    """Individual analytics event"""

    event_id: str
    event_type: AnalyticsEventType
    timestamp: datetime
    user_id: int
    session_id: Optional[str] = None

    # Event data
    event_data: Dict[str, Any] = field(default_factory=dict)

    # Context
    exam_context: Optional[Dict[str, Any]] = None
    question_context: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    # Performance data
    response_time_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

    # Turkish education specific
    subject: Optional[TurkishSubject] = None
    difficulty_level: Optional[str] = None
    curriculum_topic: Optional[str] = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "event_data": self.event_data,
            "exam_context": self.exam_context,
            "question_context": self.question_context,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "subject": self.subject.value if self.subject else None,
            "difficulty_level": self.difficulty_level,
            "curriculum_topic": self.curriculum_topic,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated analytics metrics"""

    metric_id: str
    metric_name: str
    metric_type: str  # daily, weekly, monthly, realtime
    aggregation_period: str
    timestamp: datetime

    # Aggregated values
    total_users: int = 0
    active_users: int = 0
    total_exams: int = 0
    completed_exams: int = 0
    total_questions_answered: int = 0

    # Performance aggregates
    average_score: Decimal = Decimal("0")
    median_score: Decimal = Decimal("0")
    score_distribution: Dict[str, int] = field(default_factory=dict)

    # Subject performance
    subject_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Turkish education specific
    tyt_performance: Dict[str, Any] = field(default_factory=dict)
    ayt_performance: Dict[str, Any] = field(default_factory=dict)
    regional_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    school_type_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Trends
    growth_metrics: Dict[str, float] = field(default_factory=dict)
    comparative_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "aggregation_period": self.aggregation_period,
            "timestamp": self.timestamp.isoformat(),
            "total_users": self.total_users,
            "active_users": self.active_users,
            "total_exams": self.total_exams,
            "completed_exams": self.completed_exams,
            "average_score": str(self.average_score),
            "subject_performance": self.subject_performance,
            "tyt_performance": self.tyt_performance,
            "ayt_performance": self.ayt_performance,
            "regional_performance": self.regional_performance,
            "growth_metrics": self.growth_metrics,
        }


@dataclass
class TeacherAnalytics:
    """Teacher-specific analytics"""

    teacher_id: int

    # Student management
    total_students: int = 0
    active_students: int = 0
    student_performance_overview: Dict[str, Any] = field(default_factory=dict)

    # Content creation
    content_created: int = 0
    questions_created: int = 0
    exams_created: int = 0
    content_engagement: Dict[str, Any] = field(default_factory=dict)

    # Class performance
    class_average_scores: Dict[str, Decimal] = field(default_factory=dict)
    subject_teaching_effectiveness: Dict[str, float] = field(default_factory=dict)
    improvement_trends: Dict[str, List[float]] = field(default_factory=dict)

    # Turkish education insights
    curriculum_coverage: Dict[str, float] = field(default_factory=dict)
    topic_difficulty_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "teacher_id": self.teacher_id,
            "total_students": self.total_students,
            "active_students": self.active_students,
            "student_performance_overview": self.student_performance_overview,
            "content_created": self.content_created,
            "class_average_scores": {
                k: str(v) for k, v in self.class_average_scores.items()
            },
            "subject_teaching_effectiveness": self.subject_teaching_effectiveness,
            "curriculum_coverage": self.curriculum_coverage,
        }


@dataclass
class SchoolAnalytics:
    """School-level analytics"""

    school_id: str
    school_name: str
    school_type: str
    city: str
    region: str

    # Overall metrics
    total_students: int = 0
    total_teachers: int = 0
    active_users: int = 0

    # Performance metrics
    school_average_tyt: Optional[Decimal] = None
    school_average_ayt: Optional[Decimal] = None
    regional_ranking: Optional[int] = None
    national_ranking: Optional[int] = None

    # Subject performance
    subject_averages: Dict[str, Decimal] = field(default_factory=dict)
    subject_rankings: Dict[str, int] = field(default_factory=dict)

    # Trends
    yearly_improvement: Dict[str, float] = field(default_factory=dict)
    monthly_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Turkish education specific
    university_placement_rate: float = 0.0
    top_tier_placement_rate: float = 0.0
    yks_success_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "school_id": self.school_id,
            "school_name": self.school_name,
            "school_type": self.school_type,
            "city": self.city,
            "region": self.region,
            "total_students": self.total_students,
            "total_teachers": self.total_teachers,
            "active_users": self.active_users,
            "school_average_tyt": str(self.school_average_tyt)
            if self.school_average_tyt
            else None,
            "school_average_ayt": str(self.school_average_ayt)
            if self.school_average_ayt
            else None,
            "regional_ranking": self.regional_ranking,
            "subject_averages": {k: str(v) for k, v in self.subject_averages.items()},
            "university_placement_rate": self.university_placement_rate,
            "yks_success_metrics": self.yks_success_metrics,
        }


class AnalyticsDataValidator:
    """Validator for analytics data"""

    @staticmethod
    def validate_exam_metrics(metrics: ExamMetrics) -> List[str]:
        """Validate exam metrics data"""
        errors = []

        if metrics.total_questions <= 0:
            errors.append("Total questions must be positive")

        if metrics.answered_questions > metrics.total_questions:
            errors.append("Answered questions cannot exceed total questions")

        if (
            metrics.correct_answers + metrics.wrong_answers + metrics.empty_answers
            != metrics.total_questions
        ):
            errors.append("Question counts don't add up to total")

        if metrics.score < 0 or metrics.score > metrics.max_possible_score:
            errors.append("Score out of valid range")

        if metrics.total_time_seconds < 0:
            errors.append("Time cannot be negative")

        return errors

    @staticmethod
    def validate_turkish_education_context(
        context: TurkishEducationContext,
    ) -> List[str]:
        """Validate Turkish education context"""
        errors = []

        if context.grade_level not in [9, 10, 11, 12]:
            errors.append("Grade level must be 9-12 for Turkish high school")

        valid_school_types = [
            "anadolu_lisesi",
            "fen_lisesi",
            "sosyal_bilimler_lisesi",
            "guzel_sanatlar_lisesi",
            "meslek_lisesi",
            "imam_hatip_lisesi",
            "ozel_lise",
            "devlet_lisesi",
        ]

        if context.school_type not in valid_school_types:
            errors.append(f"Invalid school type: {context.school_type}")

        return errors

    @staticmethod
    def validate_performance_profile(profile: StudentPerformanceProfile) -> List[str]:
        """Validate student performance profile"""
        errors = []

        if profile.total_exams_taken < 0:
            errors.append("Total exams taken cannot be negative")

        if not (0 <= profile.overall_success_rate <= 100):
            errors.append("Success rate must be between 0 and 100")

        if profile.current_tyt_score and not (0 <= profile.current_tyt_score <= 500):
            errors.append("TYT score must be between 0 and 500")

        if profile.current_ayt_score and not (0 <= profile.current_ayt_score <= 500):
            errors.append("AYT score must be between 0 and 500")

        return errors


class AnalyticsDataFactory:
    """Factory for creating analytics data objects"""

    @staticmethod
    def create_exam_metrics(
        exam_data: Dict[str, Any], performance_data: Dict[str, Any]
    ) -> ExamMetrics:
        """Create exam metrics from raw data"""
        return ExamMetrics(
            exam_id=exam_data["exam_id"],
            exam_type=TurkishExamType(exam_data["exam_type"]),
            total_questions=performance_data["total_questions"],
            answered_questions=performance_data["answered_questions"],
            correct_answers=performance_data["correct_answers"],
            wrong_answers=performance_data["wrong_answers"],
            empty_answers=performance_data["empty_answers"],
            score=Decimal(str(performance_data["score"])),
            max_possible_score=Decimal(str(performance_data.get("max_score", 500))),
            total_time_seconds=performance_data["total_time_seconds"],
            average_time_per_question=performance_data["average_time_per_question"],
            subject_scores=performance_data.get("subject_scores", {}),
        )

    @staticmethod
    def create_analytics_event(
        event_type: AnalyticsEventType,
        user_id: int,
        event_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> AnalyticsEvent:
        """Create analytics event"""
        return AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            event_data=event_data,
        )

    @staticmethod
    def create_student_profile(
        student_id: int, education_data: Dict[str, Any]
    ) -> StudentPerformanceProfile:
        """Create student performance profile"""
        education_context = TurkishEducationContext(
            grade_level=education_data["grade_level"],
            school_type=education_data["school_type"],
            city=education_data["city"],
            region=education_data.get("region", ""),
            school_name=education_data.get("school_name"),
            district=education_data.get("district"),
        )

        return StudentPerformanceProfile(
            student_id=student_id, education_context=education_context
        )


# Turkish education constants and utilities

TURKISH_CITIES = [
    "İstanbul",
    "Ankara",
    "İzmir",
    "Bursa",
    "Antalya",
    "Adana",
    "Konya",
    "Gaziantep",
    "Şanlıurfa",
    "Kocaeli",
    "Mersin",
    "Diyarbakır",
    "Hatay",
    "Manisa",
    "Kayseri",
    "Samsun",
    "Balıkesir",
    "Kahramanmaraş",
    "Van",
    "Aydın",
    "Denizli",
    "Sakarya",
    "Eskişehir",
    "Tekirdağ",
    "Muğla",
    "Trabzon",
    "Elazığ",
    "Erzurum",
    "Ordu",
    "Malatya",
]

TURKISH_REGIONS = {
    "Marmara": [
        "İstanbul",
        "Bursa",
        "Kocaeli",
        "Sakarya",
        "Tekirdağ",
        "Edirne",
        "Kırklareli",
        "Çanakkale",
        "Balıkesir",
        "Yalova",
        "Bilecik",
    ],
    "Ege": [
        "İzmir",
        "Manisa",
        "Aydın",
        "Muğla",
        "Denizli",
        "Uşak",
        "Kütahya",
        "Afyonkarahisar",
    ],
    "Akdeniz": [
        "Antalya",
        "Mersin",
        "Adana",
        "Hatay",
        "Kahramanmaraş",
        "Osmaniye",
        "Isparta",
        "Burdur",
    ],
    "İç Anadolu": [
        "Ankara",
        "Konya",
        "Kayseri",
        "Sivas",
        "Yozgat",
        "Kırıkkale",
        "Aksaray",
        "Niğde",
        "Nevşehir",
        "Kırşehir",
        "Çankırı",
        "Karaman",
    ],
    "Karadeniz": [
        "Samsun",
        "Trabzon",
        "Ordu",
        "Giresun",
        "Rize",
        "Artvin",
        "Gümüşhane",
        "Bayburt",
        "Tokat",
        "Amasya",
        "Çorum",
        "Sinop",
        "Kastamonu",
        "Zonguldak",
        "Bartın",
        "Karabük",
        "Düzce",
        "Bolu",
    ],
    "Doğu Anadolu": [
        "Erzurum",
        "Van",
        "Elazığ",
        "Malatya",
        "Tunceli",
        "Bingöl",
        "Muş",
        "Bitlis",
        "Hakkari",
        "Şırnak",
        "Siirt",
        "Batman",
        "Mardin",
        "Diyarbakır",
        "Şanlıurfa",
        "Gaziantep",
        "Kilis",
        "Adıyaman",
    ],
    "Güneydoğu Anadolu": [
        "Diyarbakır",
        "Şanlıurfa",
        "Gaziantep",
        "Mardin",
        "Batman",
        "Siirt",
        "Şırnak",
        "Kilis",
        "Adıyaman",
    ],
}

YKS_SCORE_CALCULATIONS = {
    "tyt_weight": 0.4,
    "ayt_weight": 0.6,
    "sayisal_subjects": ["matematik", "fizik", "kimya", "biyoloji"],
    "sozel_subjects": ["tarih", "cografya", "felsefe", "din", "edebiyat"],
    "esit_agirlik_subjects": ["matematik", "edebiyat", "tarih", "cografya"],
}


def get_region_for_city(city: str) -> str:
    """Get region for Turkish city"""
    for region, cities in TURKISH_REGIONS.items():
        if city in cities:
            return region
    return "Bilinmeyen"


def calculate_turkish_percentile(
    score: float, exam_type: TurkishExamType, total_students: int = 1000000
) -> float:
    """Calculate percentile for Turkish exam scores"""
    # Simplified percentile calculation based on Turkish exam distributions
    if exam_type == TurkishExamType.TYT:
        if score >= 450:
            return 99.0
        elif score >= 400:
            return 95.0
        elif score >= 350:
            return 85.0
        elif score >= 300:
            return 70.0
        elif score >= 250:
            return 50.0
        else:
            return max(0, (score / 500) * 50)
    else:  # AYT
        if score >= 450:
            return 99.5
        elif score >= 400:
            return 97.0
        elif score >= 350:
            return 90.0
        elif score >= 300:
            return 75.0
        elif score >= 250:
            return 55.0
        else:
            return max(0, (score / 500) * 55)


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Unified Analytics Data Model - Turkish Exam Platform")
    print("=" * 60)

    # Create sample education context
    education_context = TurkishEducationContext(
        grade_level=12,
        school_type="anadolu_lisesi",
        city="İstanbul",
        region="Marmara",
        school_name="Atatürk Anadolu Lisesi",
    )

    # Create sample exam metrics
    exam_metrics = ExamMetrics(
        exam_id="tyt_2024_001",
        exam_type=TurkishExamType.TYT,
        total_questions=120,
        answered_questions=115,
        correct_answers=95,
        wrong_answers=20,
        empty_answers=5,
        score=Decimal("425.5"),
        max_possible_score=Decimal("500"),
        total_time_seconds=7200,
        average_time_per_question=62.6,
    )

    # Create student performance profile
    student_profile = StudentPerformanceProfile(
        student_id=12345,
        education_context=education_context,
        total_exams_taken=15,
        current_tyt_score=Decimal("425.5"),
    )

    print(f"Performance Level: {exam_metrics.get_performance_level().value}")
    print(f"Net Score: {exam_metrics.calculate_net_score()}")
    print(f"Success Rate: {exam_metrics.calculate_success_rate():.1f}%")
    print(f"YKS Prediction: {student_profile.calculate_yks_prediction()}")

    # Validate data
    validator = AnalyticsDataValidator()
    exam_errors = validator.validate_exam_metrics(exam_metrics)
    context_errors = validator.validate_turkish_education_context(education_context)

    print(f"\nValidation Errors:")
    print(f"Exam Metrics: {exam_errors}")
    print(f"Education Context: {context_errors}")
