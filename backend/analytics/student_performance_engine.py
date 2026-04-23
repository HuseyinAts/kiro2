"""
KIRO2 Student Performance Analytics Engine
Comprehensive student performance analysis and prediction system
Türkiye Üniversite Sınavları Hazırlık Platformu - Öğrenci Performans Analiz Motoru
"""

import asyncio
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from analytics.unified_analytics_data_model import (
    AnalyticsDataValidator,
    AnalyticsEvent,
    AnalyticsEventType,
    ExamMetrics,
    StudentPerformanceProfile,
    TurkishEducationContext,
    TurkishExamType,
    calculate_turkish_percentile,
)
from core.multi_level_caching import get_cache_system
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.ANALYTICS)
config = get_unified_config()


@dataclass
class LearningPattern:
    """Student learning pattern analysis"""

    student_id: int
    pattern_type: str  # "visual", "auditory", "kinesthetic", "mixed"
    confidence: float  # 0.0 to 1.0

    # Time patterns
    optimal_study_hours: list[int] = field(default_factory=list)
    session_duration_preference: int = 45  # minutes
    break_frequency: int = 10  # minutes

    # Content preferences
    preferred_difficulty_progression: str = "gradual"  # gradual, steep, mixed
    question_type_preferences: dict[str, float] = field(default_factory=dict)
    subject_affinity: dict[str, float] = field(default_factory=dict)

    # Behavioral patterns
    procrastination_tendency: float = 0.0  # 0.0 (never) to 1.0 (always)
    consistency_score: float = 0.0  # 0.0 (inconsistent) to 1.0 (very consistent)
    stress_performance_correlation: float = 0.0  # -1.0 to 1.0

    # Turkish exam specific
    tyt_vs_ayt_preference: float = 0.0  # -1.0 (TYT focused) to 1.0 (AYT focused)
    subject_switching_frequency: float = 0.0  # How often student changes subjects


@dataclass
class PredictiveModel:
    """Predictive model for student performance"""

    model_id: str
    model_type: str  # "yks_prediction", "subject_mastery", "improvement_rate"
    confidence: float

    # Model parameters
    features: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    bias: float = 0.0

    # Performance metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Turkish education specific parameters
    regional_adjustment: float = 0.0
    school_type_adjustment: float = 0.0
    curriculum_year_adjustment: float = 0.0

    # Prediction outputs
    predictions: dict[str, Any] = field(default_factory=dict)
    recommendation_strength: float = 0.0


@dataclass
class PerformanceInsight:
    """Performance insight for students"""

    insight_id: str
    student_id: int
    insight_type: str  # "strength", "weakness", "opportunity", "threat"
    priority: str  # "high", "medium", "low"

    # Insight content
    title: str
    title_tr: str
    description: str
    description_tr: str

    # Supporting data
    supporting_metrics: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    recommendations_tr: list[str] = field(default_factory=list)

    # Timeline
    estimated_improvement_weeks: int | None = None
    target_score_improvement: float | None = None

    # Turkish education context
    curriculum_topics: list[str] = field(default_factory=list)
    affected_subjects: list[str] = field(default_factory=list)


class StudentPerformanceAnalyzer:
    """Core performance analysis engine"""

    def __init__(self):
        self.cache_system = None
        self.validator = AnalyticsDataValidator()

        # Analysis configurations
        self.analysis_config = {
            "min_data_points": 5,  # Minimum exams for reliable analysis
            "lookback_days": 90,  # Days to look back for trends
            "prediction_horizon_days": 30,  # Days to predict forward
            "confidence_threshold": 0.7,
            "improvement_threshold": 0.05,  # 5% improvement threshold
        }

        # Turkish exam specific configurations
        self.turkish_exam_config = {
            "tyt_max_score": 500,
            "ayt_max_score": 500,
            "yks_tyt_weight": 0.4,
            "yks_ayt_weight": 0.6,
            "university_placement_threshold": 300,
            "top_tier_threshold": 450,
        }

    async def _get_cache_system(self):
        """Get cache system instance"""
        if not self.cache_system:
            self.cache_system = await get_cache_system()
        return self.cache_system

    async def analyze_student_performance(
        self,
        student_id: int,
        exam_history: list[ExamMetrics],
        learning_events: list[AnalyticsEvent],
    ) -> StudentPerformanceProfile:
        """Comprehensive student performance analysis"""
        try:
            logger.info(f"Starting performance analysis for student {student_id}")

            if not exam_history:
                logger.warning(f"No exam history for student {student_id}")
                return await self._create_minimal_profile(student_id)

            # Validate input data
            errors = []
            for exam in exam_history:
                exam_errors = self.validator.validate_exam_metrics(exam)
                errors.extend(exam_errors)

            if errors:
                logger.error(f"Validation errors in exam data: {errors}")
                raise ValueError(f"Invalid exam data: {', '.join(errors)}")

            # Create base profile
            profile = await self._create_base_profile(student_id, exam_history)

            # Analyze performance trends
            await self._analyze_performance_trends(profile, exam_history)

            # Analyze subject performance
            await self._analyze_subject_performance(profile, exam_history)

            # Analyze learning patterns
            await self._analyze_learning_patterns(profile, learning_events)

            # Generate insights and recommendations
            await self._generate_performance_insights(profile, exam_history)

            # Cache results
            await self._cache_performance_profile(profile)

            logger.info(f"Performance analysis completed for student {student_id}")
            return profile

        except Exception as e:
            logger.error(f"Performance analysis failed for student {student_id}: {e}")
            raise

    async def _create_minimal_profile(
        self, student_id: int
    ) -> StudentPerformanceProfile:
        """Create minimal profile for new students"""
        education_context = TurkishEducationContext(
            grade_level=12,  # Default to senior year
            school_type="anadolu_lisesi",
            city="İstanbul",
            region="Marmara",
        )

        return StudentPerformanceProfile(
            student_id=student_id, education_context=education_context
        )

    async def _create_base_profile(
        self, student_id: int, exam_history: list[ExamMetrics]
    ) -> StudentPerformanceProfile:
        """Create base performance profile"""

        # Get or create education context
        education_context = await self._get_education_context(student_id)

        # Calculate basic metrics
        total_exams = len(exam_history)
        total_questions = sum(exam.total_questions for exam in exam_history)
        total_correct = sum(exam.correct_answers for exam in exam_history)
        overall_success_rate = (
            (total_correct / total_questions * 100) if total_questions > 0 else 0
        )

        # Get latest scores
        recent_exams = sorted(exam_history, key=lambda x: x.exam_id, reverse=True)
        current_tyt_score = None
        current_ayt_score = None

        for exam in recent_exams:
            if exam.exam_type == TurkishExamType.TYT and current_tyt_score is None:
                current_tyt_score = exam.score
            elif exam.exam_type == TurkishExamType.AYT and current_ayt_score is None:
                current_ayt_score = exam.score

        # Calculate study hours (estimated from exam sessions)
        total_study_hours = Decimal(
            str(sum(exam.total_time_seconds for exam in exam_history) / 3600)
        )

        return StudentPerformanceProfile(
            student_id=student_id,
            education_context=education_context,
            total_exams_taken=total_exams,
            total_study_hours=total_study_hours,
            total_questions_answered=total_questions,
            overall_success_rate=overall_success_rate,
            current_tyt_score=current_tyt_score,
            current_ayt_score=current_ayt_score,
        )

    async def _get_education_context(self, student_id: int) -> TurkishEducationContext:
        """Get or infer education context for student"""
        try:
            # Try to get from cache first
            cache_system = await self._get_cache_system()
            cached_context = await cache_system.cache_system.get(
                f"education_context:{student_id}"
            )

            if cached_context:
                return TurkishEducationContext(**cached_context)

            # If not cached, create default context
            # In real implementation, this would query the database
            return TurkishEducationContext(
                grade_level=12,
                school_type="anadolu_lisesi",
                city="İstanbul",
                region="Marmara",
                school_name="Test Lisesi",
            )

        except Exception as e:
            logger.warning(
                f"Could not get education context for student {student_id}: {e}"
            )
            return TurkishEducationContext(
                grade_level=12,
                school_type="anadolu_lisesi",
                city="İstanbul",
                region="Marmara",
            )

    async def _analyze_performance_trends(
        self, profile: StudentPerformanceProfile, exam_history: list[ExamMetrics]
    ):
        """Analyze performance trends over time"""
        try:
            if len(exam_history) < 3:
                profile.performance_trend = "insufficient_data"
                return

            # Sort exams chronologically (using exam_id as proxy for time)
            sorted_exams = sorted(exam_history, key=lambda x: x.exam_id)

            # Calculate score trends
            scores = [float(exam.score) for exam in sorted_exams]
            success_rates = [exam.calculate_success_rate() for exam in sorted_exams]

            # Linear trend analysis
            score_trend = self._calculate_trend(scores)
            success_rate_trend = self._calculate_trend(success_rates)

            # Determine overall trend
            if score_trend > self.analysis_config["improvement_threshold"]:
                profile.performance_trend = "improving"
            elif score_trend < -self.analysis_config["improvement_threshold"]:
                profile.performance_trend = "declining"
            else:
                profile.performance_trend = "stable"

            # Calculate recent progress (last 30 days equivalent)
            recent_count = min(5, len(sorted_exams))
            recent_exams = sorted_exams[-recent_count:]

            if len(recent_exams) >= 2:
                recent_scores = [float(exam.score) for exam in recent_exams]
                recent_trend = self._calculate_trend(recent_scores)

                profile.last_30_days_progress = {
                    "score_trend": recent_trend,
                    "average_score": statistics.mean(recent_scores),
                    "score_variance": statistics.variance(recent_scores)
                    if len(recent_scores) > 1
                    else 0,
                    "exam_count": len(recent_exams),
                }

            # Set goal progress (simplified)
            if profile.current_tyt_score:
                target_tyt = 450  # Default target
                current_tyt = float(profile.current_tyt_score)
                progress = min(100, (current_tyt / target_tyt) * 100)

                profile.goal_progress = {
                    "tyt_target_progress": progress,
                    "target_score": target_tyt,
                    "current_score": current_tyt,
                    "improvement_needed": max(0, target_tyt - current_tyt),
                }

        except Exception as e:
            logger.error(f"Performance trend analysis failed: {e}")
            profile.performance_trend = "unknown"

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate linear trend (slope) for a series of values"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        # Calculate linear regression slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    async def _analyze_subject_performance(
        self, profile: StudentPerformanceProfile, exam_history: list[ExamMetrics]
    ):
        """Analyze performance by subject"""
        try:
            subject_stats = defaultdict(
                lambda: {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "total_time": 0,
                    "exam_count": 0,
                    "scores": [],
                }
            )

            # Aggregate subject data
            for exam in exam_history:
                for subject, subject_data in exam.subject_scores.items():
                    stats = subject_stats[subject]
                    stats["total_questions"] += subject_data.get("total_questions", 0)
                    stats["correct_answers"] += subject_data.get("correct_answers", 0)
                    stats["total_time"] += subject_data.get("time_spent", 0)
                    stats["exam_count"] += 1

                    if "score" in subject_data:
                        stats["scores"].append(subject_data["score"])

            # Calculate performance metrics for each subject
            for subject, stats in subject_stats.items():
                if stats["total_questions"] > 0:
                    success_rate = (
                        stats["correct_answers"] / stats["total_questions"]
                    ) * 100
                    avg_time_per_question = (
                        stats["total_time"] / stats["total_questions"]
                        if stats["total_questions"] > 0
                        else 0
                    )
                    avg_score = (
                        statistics.mean(stats["scores"]) if stats["scores"] else 0
                    )

                    profile.subject_performance[subject] = {
                        "success_rate": success_rate,
                        "avg_time_per_question": avg_time_per_question,
                        "avg_score": avg_score,
                        "total_questions": stats["total_questions"],
                        "exam_count": stats["exam_count"],
                        "performance_level": self._get_subject_performance_level(
                            success_rate
                        ),
                    }

            # Identify strongest and weakest subjects
            if profile.subject_performance:
                sorted_subjects = sorted(
                    profile.subject_performance.items(),
                    key=lambda x: x[1]["success_rate"],
                    reverse=True,
                )

                profile.strongest_subjects = [
                    subject for subject, _ in sorted_subjects[:3]
                ]
                profile.weakest_subjects = [
                    subject for subject, _ in sorted_subjects[-3:]
                ]

            # Turkish exam specific analysis
            await self._analyze_tyt_subjects(profile, exam_history)

        except Exception as e:
            logger.error(f"Subject performance analysis failed: {e}")

    def _get_subject_performance_level(self, success_rate: float) -> str:
        """Get performance level for subject based on success rate"""
        if success_rate >= 90:
            return "excellent"
        if success_rate >= 80:
            return "very_good"
        if success_rate >= 70:
            return "good"
        if success_rate >= 60:
            return "average"
        if success_rate >= 50:
            return "below_average"
        return "weak"

    async def _analyze_tyt_subjects(
        self, profile: StudentPerformanceProfile, exam_history: list[ExamMetrics]
    ):
        """Analyze TYT-specific subject breakdown"""
        try:
            tyt_exams = [
                exam for exam in exam_history if exam.exam_type == TurkishExamType.TYT
            ]

            if not tyt_exams:
                return

            tyt_subjects = {
                "matematik": {"name": "Matematik", "questions": 40, "scores": []},
                "turkce": {"name": "Türkçe-Edebiyat", "questions": 40, "scores": []},
                "fen": {"name": "Fen Bilimleri", "questions": 20, "scores": []},
                "sosyal": {"name": "Sosyal Bilimler", "questions": 20, "scores": []},
            }

            # Aggregate TYT subject scores
            for exam in tyt_exams:
                for subject in tyt_subjects:
                    if subject in exam.subject_scores:
                        subject_score = exam.subject_scores[subject].get("score", 0)
                        tyt_subjects[subject]["scores"].append(subject_score)

            # Calculate TYT subject analytics
            for subject, data in tyt_subjects.items():
                if data["scores"]:
                    avg_score = statistics.mean(data["scores"])
                    score_trend = (
                        self._calculate_trend(data["scores"])
                        if len(data["scores"]) > 1
                        else 0
                    )

                    profile.tyt_subject_breakdown[subject] = {
                        "name": data["name"],
                        "question_count": data["questions"],
                        "average_score": avg_score,
                        "score_trend": score_trend,
                        "exam_count": len(data["scores"]),
                        "performance_level": self._get_score_performance_level(
                            avg_score
                        ),
                    }

        except Exception as e:
            logger.error(f"TYT subject analysis failed: {e}")

    def _get_score_performance_level(self, score: float) -> str:
        """Get performance level based on score"""
        if score >= 90:
            return "excellent"
        if score >= 80:
            return "very_good"
        if score >= 70:
            return "good"
        if score >= 60:
            return "average"
        if score >= 50:
            return "below_average"
        return "weak"

    async def _analyze_learning_patterns(
        self, profile: StudentPerformanceProfile, learning_events: list[AnalyticsEvent]
    ):
        """Analyze learning patterns from user behavior"""
        try:
            if not learning_events:
                return

            # Time pattern analysis
            study_hours = defaultdict(int)
            session_durations = []

            for event in learning_events:
                if event.event_type in [
                    AnalyticsEventType.EXAM_START,
                    AnalyticsEventType.PRACTICE_START,
                ]:
                    hour = event.timestamp.hour
                    study_hours[hour] += 1

                    if "duration" in event.event_data:
                        session_durations.append(event.event_data["duration"])

            # Find preferred study times (top 3 hours)
            if study_hours:
                sorted_hours = sorted(
                    study_hours.items(), key=lambda x: x[1], reverse=True
                )
                profile.preferred_study_times = [
                    f"{hour:02d}:00" for hour, _ in sorted_hours[:3]
                ]
                profile.most_productive_hours = [hour for hour, _ in sorted_hours[:3]]

            # Calculate average session duration
            if session_durations:
                profile.average_study_session_minutes = statistics.mean(
                    session_durations
                )

            # Behavioral pattern analysis
            await self._analyze_behavioral_patterns(profile, learning_events)

        except Exception as e:
            logger.error(f"Learning pattern analysis failed: {e}")

    async def _analyze_behavioral_patterns(
        self, profile: StudentPerformanceProfile, learning_events: list[AnalyticsEvent]
    ):
        """Analyze behavioral patterns"""
        try:
            # Question answering patterns
            question_events = [
                event
                for event in learning_events
                if event.event_type == AnalyticsEventType.QUESTION_ANSWER
            ]

            if question_events:
                answer_times = []
                skip_count = 0
                review_count = 0

                for event in question_events:
                    if "time_spent" in event.event_data:
                        answer_times.append(event.event_data["time_spent"])

                    if event.event_data.get("skipped"):
                        skip_count += 1

                    if event.event_data.get("reviewed"):
                        review_count += 1

                profile.question_answering_patterns = {
                    "average_answer_time": statistics.mean(answer_times)
                    if answer_times
                    else 0,
                    "skip_rate": (skip_count / len(question_events)) * 100,
                    "review_rate": (review_count / len(question_events)) * 100,
                    "total_questions": len(question_events),
                }

            # Exam taking behavior
            exam_events = [
                event
                for event in learning_events
                if event.event_type
                in [
                    AnalyticsEventType.EXAM_START,
                    AnalyticsEventType.EXAM_COMPLETE,
                    AnalyticsEventType.EXAM_ABANDON,
                ]
            ]

            if exam_events:
                completion_rate = len(
                    [
                        e
                        for e in exam_events
                        if e.event_type == AnalyticsEventType.EXAM_COMPLETE
                    ]
                ) / len(
                    [
                        e
                        for e in exam_events
                        if e.event_type == AnalyticsEventType.EXAM_START
                    ]
                )

                profile.exam_taking_behavior = {
                    "completion_rate": completion_rate * 100,
                    "total_exam_sessions": len(
                        [
                            e
                            for e in exam_events
                            if e.event_type == AnalyticsEventType.EXAM_START
                        ]
                    ),
                    "abandonment_rate": (1 - completion_rate) * 100,
                }

        except Exception as e:
            logger.error(f"Behavioral pattern analysis failed: {e}")

    async def _generate_performance_insights(
        self, profile: StudentPerformanceProfile, exam_history: list[ExamMetrics]
    ):
        """Generate performance insights and recommendations"""
        try:
            insights = []

            # Generate trend insights
            if profile.performance_trend == "improving":
                insights.append(
                    {
                        "type": "strength",
                        "title": "Positive Performance Trend",
                        "title_tr": "Pozitif Performans Trendi",
                        "message": "Your scores are consistently improving",
                        "message_tr": "Skorlarınız sürekli olarak artıyor",
                    }
                )
            elif profile.performance_trend == "declining":
                insights.append(
                    {
                        "type": "concern",
                        "title": "Declining Performance",
                        "title_tr": "Azalan Performans",
                        "message": "Recent scores show a downward trend",
                        "message_tr": "Son skorlar düşüş trendi gösteriyor",
                    }
                )

            # Subject-specific insights
            if profile.strongest_subjects:
                strongest = profile.strongest_subjects[0]
                insights.append(
                    {
                        "type": "strength",
                        "title": f"Strong in {strongest}",
                        "title_tr": f"{strongest} konusunda güçlü",
                        "message": f"Excellent performance in {strongest}",
                        "message_tr": f"{strongest} konusunda mükemmel performans",
                    }
                )

            if profile.weakest_subjects:
                weakest = profile.weakest_subjects[-1]
                insights.append(
                    {
                        "type": "opportunity",
                        "title": f"Improve {weakest}",
                        "title_tr": f"{weakest} konusunu geliştir",
                        "message": f"Focus more attention on {weakest}",
                        "message_tr": f"{weakest} konusuna daha fazla dikkat verin",
                    }
                )

            # YKS prediction insights
            yks_prediction = profile.calculate_yks_prediction()
            if yks_prediction.get("tier") == "top_tier":
                insights.append(
                    {
                        "type": "strength",
                        "title": "Top Tier Performance",
                        "title_tr": "Üst Seviye Performans",
                        "message": "You're on track for top universities",
                        "message_tr": "En iyi üniversiteler için doğru yoldasınız",
                    }
                )

            # Store insights in profile (simplified)
            profile.exam_context["insights"] = insights

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")

    async def _cache_performance_profile(self, profile: StudentPerformanceProfile):
        """Cache performance profile for quick access"""
        try:
            cache_system = await self._get_cache_system()
            cache_key = f"performance_profile:{profile.student_id}"

            # Cache for 1 hour
            await cache_system.cache_system.set(cache_key, profile.to_dict(), ttl=3600)

            logger.debug(f"Cached performance profile for student {profile.student_id}")

        except Exception as e:
            logger.error(f"Failed to cache performance profile: {e}")

    async def predict_future_performance(
        self, profile: StudentPerformanceProfile, prediction_days: int = 30
    ) -> dict[str, Any]:
        """Predict future performance based on current trends"""
        try:
            if not profile.current_tyt_score:
                return {"prediction": "insufficient_data"}

            current_score = float(profile.current_tyt_score)

            # Simple trend-based prediction
            trend = 0  # Would be calculated from actual trend analysis
            if profile.performance_trend == "improving":
                trend = 2.0  # 2 points per prediction period
            elif profile.performance_trend == "declining":
                trend = -1.5  # -1.5 points per prediction period

            predicted_score = current_score + (
                trend * (prediction_days / 7)
            )  # Weekly trend
            predicted_score = max(0, min(500, predicted_score))  # Bound to valid range

            # Calculate confidence based on data quality
            confidence = min(0.9, profile.total_exams_taken * 0.1)

            return {
                "predicted_score": predicted_score,
                "current_score": current_score,
                "expected_change": predicted_score - current_score,
                "confidence": confidence,
                "prediction_horizon_days": prediction_days,
                "factors": {
                    "trend": profile.performance_trend,
                    "data_points": profile.total_exams_taken,
                    "consistency": profile.overall_success_rate,
                },
            }

        except Exception as e:
            logger.error(f"Future performance prediction failed: {e}")
            return {"prediction": "error", "error": str(e)}

    async def generate_study_recommendations(
        self, profile: StudentPerformanceProfile
    ) -> list[dict[str, Any]]:
        """Generate personalized study recommendations"""
        try:
            recommendations = []

            # Subject-based recommendations
            if profile.weakest_subjects:
                for subject in profile.weakest_subjects:
                    recommendations.append(
                        {
                            "type": "subject_focus",
                            "priority": "high",
                            "title": f"Focus on {subject}",
                            "title_tr": f"{subject} konusuna odaklan",
                            "description": f"Allocate more study time to {subject}",
                            "description_tr": f"{subject} konusuna daha fazla çalışma süresi ayır",
                            "estimated_improvement": "15-20 points in 4 weeks",
                            "estimated_improvement_tr": "4 haftada 15-20 puan artış",
                        }
                    )

            # Time management recommendations
            if profile.average_study_session_minutes > 0:
                if profile.average_study_session_minutes > 90:
                    recommendations.append(
                        {
                            "type": "time_management",
                            "priority": "medium",
                            "title": "Shorter Study Sessions",
                            "title_tr": "Daha Kısa Çalışma Seansları",
                            "description": "Break long sessions into shorter, focused periods",
                            "description_tr": "Uzun seansları daha kısa, odaklanmış periyotlara böl",
                        }
                    )
                elif profile.average_study_session_minutes < 30:
                    recommendations.append(
                        {
                            "type": "time_management",
                            "priority": "medium",
                            "title": "Extend Study Sessions",
                            "title_tr": "Çalışma Seanslarını Uzat",
                            "description": "Increase session length for better retention",
                            "description_tr": "Daha iyi kavrama için seans uzunluğunu artır",
                        }
                    )

            # Performance trend recommendations
            if profile.performance_trend == "declining":
                recommendations.append(
                    {
                        "type": "performance_recovery",
                        "priority": "high",
                        "title": "Address Performance Decline",
                        "title_tr": "Performans Düşüşünü Ele Al",
                        "description": "Review study methods and identify obstacles",
                        "description_tr": "Çalışma yöntemlerini gözden geçir ve engelleri tespit et",
                    }
                )

            # YKS-specific recommendations
            yks_prediction = profile.calculate_yks_prediction()
            if yks_prediction.get("placement_probability", 0) < 0.7:
                recommendations.append(
                    {
                        "type": "yks_preparation",
                        "priority": "high",
                        "title": "Intensify YKS Preparation",
                        "title_tr": "YKS Hazırlığını Yoğunlaştır",
                        "description": "Increase study intensity for better university placement",
                        "description_tr": "Daha iyi üniversite yerleşimi için çalışma yoğunluğunu artır",
                    }
                )

            return recommendations[:5]  # Limit to top 5 recommendations

        except Exception as e:
            logger.error(f"Study recommendation generation failed: {e}")
            return []


class PerformanceComparator:
    """Compare student performance with peers and standards"""

    def __init__(self):
        self.cache_system = None

    async def _get_cache_system(self):
        """Get cache system instance"""
        if not self.cache_system:
            self.cache_system = await get_cache_system()
        return self.cache_system

    async def compare_with_peers(
        self,
        student_profile: StudentPerformanceProfile,
        comparison_group: str = "grade_level",  # "grade_level", "school", "region", "national"
    ) -> dict[str, Any]:
        """Compare student performance with peer groups"""
        try:
            # This would typically query aggregated statistics from database
            # For now, using mock data based on Turkish education statistics

            peer_averages = {
                "grade_level": {
                    "tyt_average": 350,
                    "ayt_average": 320,
                    "success_rate": 65,
                    "sample_size": 1000,
                },
                "school": {
                    "tyt_average": 380,
                    "ayt_average": 340,
                    "success_rate": 70,
                    "sample_size": 200,
                },
                "region": {
                    "tyt_average": 365,
                    "ayt_average": 330,
                    "success_rate": 67,
                    "sample_size": 50000,
                },
                "national": {
                    "tyt_average": 350,
                    "ayt_average": 320,
                    "success_rate": 65,
                    "sample_size": 1500000,
                },
            }

            peer_stats = peer_averages.get(comparison_group, peer_averages["national"])

            comparison = {"comparison_group": comparison_group, "student_vs_peers": {}}

            # TYT comparison
            if student_profile.current_tyt_score:
                student_tyt = float(student_profile.current_tyt_score)
                peer_tyt = peer_stats["tyt_average"]

                comparison["student_vs_peers"]["tyt"] = {
                    "student_score": student_tyt,
                    "peer_average": peer_tyt,
                    "difference": student_tyt - peer_tyt,
                    "percentile": calculate_turkish_percentile(
                        student_tyt, TurkishExamType.TYT
                    ),
                    "performance_level": "above_average"
                    if student_tyt > peer_tyt
                    else "below_average",
                }

            # Overall success rate comparison
            student_success = student_profile.overall_success_rate
            peer_success = peer_stats["success_rate"]

            comparison["student_vs_peers"]["success_rate"] = {
                "student_rate": student_success,
                "peer_average": peer_success,
                "difference": student_success - peer_success,
                "performance_level": "above_average"
                if student_success > peer_success
                else "below_average",
            }

            # Generate insights
            comparison["insights"] = []

            if student_profile.current_tyt_score:
                tyt_diff = comparison["student_vs_peers"]["tyt"]["difference"]
                if tyt_diff > 50:
                    comparison["insights"].append(
                        {
                            "type": "strength",
                            "message": "Significantly above peer average in TYT",
                            "message_tr": "TYT'de akran ortalamasının önemli ölçüde üstünde",
                        }
                    )
                elif tyt_diff < -30:
                    comparison["insights"].append(
                        {
                            "type": "concern",
                            "message": "Below peer average in TYT - focus needed",
                            "message_tr": "TYT'de akran ortalamasının altında - odaklanma gerekli",
                        }
                    )

            return comparison

        except Exception as e:
            logger.error(f"Peer comparison failed: {e}")
            return {"error": str(e)}

    async def benchmark_against_universities(
        self, student_profile: StudentPerformanceProfile
    ) -> dict[str, Any]:
        """Benchmark student performance against university requirements"""
        try:
            # Mock university data (based on real YKS statistics)
            university_benchmarks = {
                "top_tier": {
                    "name": "Top Universities (İstanbul Ü., Boğaziçi, ODTÜ, etc.)",
                    "name_tr": "Üst Seviye Üniversiteler",
                    "min_yks_score": 450,
                    "competitive_score": 480,
                    "placement_rate": 0.02,  # 2% of all students
                },
                "high_tier": {
                    "name": "High Tier Universities",
                    "name_tr": "Yüksek Seviye Üniversiteler",
                    "min_yks_score": 400,
                    "competitive_score": 430,
                    "placement_rate": 0.10,  # 10% of all students
                },
                "mid_tier": {
                    "name": "Mid Tier Universities",
                    "name_tr": "Orta Seviye Üniversiteler",
                    "min_yks_score": 350,
                    "competitive_score": 380,
                    "placement_rate": 0.25,  # 25% of all students
                },
                "lower_tier": {
                    "name": "Lower Tier Universities",
                    "name_tr": "Alt Seviye Üniversiteler",
                    "min_yks_score": 300,
                    "competitive_score": 320,
                    "placement_rate": 0.50,  # 50% of all students
                },
            }

            yks_prediction = student_profile.calculate_yks_prediction()
            predicted_yks = yks_prediction.get("predicted_yks_score", 0)

            benchmarks = {}

            for tier, data in university_benchmarks.items():
                min_score = data["min_yks_score"]
                competitive_score = data["competitive_score"]

                if predicted_yks >= competitive_score:
                    status = "highly_likely"
                    status_tr = "Yüksek İhtimal"
                elif predicted_yks >= min_score:
                    status = "possible"
                    status_tr = "Mümkün"
                else:
                    status = "unlikely"
                    status_tr = "Düşük İhtimal"

                gap = min_score - predicted_yks

                benchmarks[tier] = {
                    "university_name": data["name"],
                    "university_name_tr": data["name_tr"],
                    "min_required_score": min_score,
                    "competitive_score": competitive_score,
                    "student_predicted_score": predicted_yks,
                    "score_gap": max(0, gap),
                    "admission_status": status,
                    "admission_status_tr": status_tr,
                    "placement_rate": data["placement_rate"],
                }

            return {
                "benchmarks": benchmarks,
                "recommendations": self._generate_university_recommendations(
                    benchmarks
                ),
            }

        except Exception as e:
            logger.error(f"University benchmarking failed: {e}")
            return {"error": str(e)}

    def _generate_university_recommendations(
        self, benchmarks: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Generate university admission recommendations"""
        recommendations = []

        # Find the highest achievable tier
        achievable_tiers = [
            tier
            for tier, data in benchmarks.items()
            if data["admission_status"] in ["highly_likely", "possible"]
        ]

        if "top_tier" in achievable_tiers:
            recommendations.append(
                {
                    "message": "You're on track for top universities! Maintain your performance.",
                    "message_tr": "En iyi üniversiteler için doğru yoldasınız! Performansınızı koruyun.",
                }
            )
        elif "high_tier" in achievable_tiers:
            recommendations.append(
                {
                    "message": "Focus on reaching top tier universities with consistent improvement.",
                    "message_tr": "Sürekli gelişimle üst seviye üniversitelere ulaşmaya odaklanın.",
                }
            )
        else:
            # Find the closest achievable tier
            min_gap = min(
                data["score_gap"]
                for data in benchmarks.values()
                if data["score_gap"] > 0
            )
            recommendations.append(
                {
                    "message": f"Focus on improving your score by {min_gap:.0f} points for better university options.",
                    "message_tr": f"Daha iyi üniversite seçenekleri için skorunuzu {min_gap:.0f} puan artırmaya odaklanın.",
                }
            )

        return recommendations


# Factory and utility functions
async def create_performance_analyzer() -> StudentPerformanceAnalyzer:
    """Create and initialize performance analyzer"""
    analyzer = StudentPerformanceAnalyzer()
    return analyzer


async def analyze_student_batch(
    student_ids: list[int], analyzer: StudentPerformanceAnalyzer
) -> dict[int, StudentPerformanceProfile]:
    """Analyze performance for multiple students"""
    results = {}

    for student_id in student_ids:
        try:
            # This would typically fetch data from database
            exam_history = []  # Mock data
            learning_events = []  # Mock data

            profile = await analyzer.analyze_student_performance(
                student_id, exam_history, learning_events
            )
            results[student_id] = profile

        except Exception as e:
            logger.error(f"Batch analysis failed for student {student_id}: {e}")
            results[student_id] = None

    return results


if __name__ == "__main__":
    # Example usage and testing
    async def main():
        print("KIRO2 Student Performance Analytics Engine")
        print("=" * 50)

        # Create performance analyzer
        analyzer = await create_performance_analyzer()

        # Mock exam data for testing
        from decimal import Decimal

        from analytics.unified_analytics_data_model import (
            ExamMetrics,
            TurkishExamType,
        )

        mock_exam_history = [
            ExamMetrics(
                exam_id="tyt_001",
                exam_type=TurkishExamType.TYT,
                total_questions=120,
                answered_questions=118,
                correct_answers=95,
                wrong_answers=23,
                empty_answers=2,
                score=Decimal("425"),
                max_possible_score=Decimal("500"),
                total_time_seconds=7200,
                average_time_per_question=61.0,
                subject_scores={
                    "matematik": {
                        "total_questions": 40,
                        "correct_answers": 32,
                        "score": 85,
                    },
                    "turkce": {
                        "total_questions": 40,
                        "correct_answers": 35,
                        "score": 90,
                    },
                    "fen": {"total_questions": 20, "correct_answers": 15, "score": 75},
                    "sosyal": {
                        "total_questions": 20,
                        "correct_answers": 13,
                        "score": 65,
                    },
                },
            )
        ]

        # Analyze performance
        profile = await analyzer.analyze_student_performance(
            12345, mock_exam_history, []
        )

        print(f"Student ID: {profile.student_id}")
        print(f"Total Exams: {profile.total_exams_taken}")
        print(f"Overall Success Rate: {profile.overall_success_rate:.1f}%")
        print(f"Current TYT Score: {profile.current_tyt_score}")
        print(f"Performance Trend: {profile.performance_trend}")
        print(f"Strongest Subjects: {', '.join(profile.strongest_subjects)}")
        print(f"Weakest Subjects: {', '.join(profile.weakest_subjects)}")

        # Generate predictions
        prediction = await analyzer.predict_future_performance(profile)
        print(
            f"\nPredicted Score (30 days): {prediction.get('predicted_score', 'N/A')}"
        )
        print(f"Confidence: {prediction.get('confidence', 0)*100:.1f}%")

        # Generate recommendations
        recommendations = await analyzer.generate_study_recommendations(profile)
        print("\nStudy Recommendations:")
        for rec in recommendations[:3]:
            print(f"- {rec['title_tr']}: {rec['description_tr']}")

        # Performance comparison
        comparator = PerformanceComparator()
        peer_comparison = await comparator.compare_with_peers(profile, "national")

        if "student_vs_peers" in peer_comparison:
            tyt_comparison = peer_comparison["student_vs_peers"].get("tyt", {})
            if tyt_comparison:
                print("\nTYT vs National Average:")
                print(f"Student: {tyt_comparison['student_score']}")
                print(f"National Avg: {tyt_comparison['peer_average']}")
                print(f"Difference: {tyt_comparison['difference']:+.1f} points")
                print(f"Percentile: {tyt_comparison['percentile']:.1f}")

    # Run the example
    asyncio.run(main())
