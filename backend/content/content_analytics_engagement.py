"""
KIRO2 Content Analytics and Engagement Tracking System
Comprehensive analytics system for tracking content performance and student engagement
Türkiye Üniversite Sınavları Hazırlık Platformu - İçerik Analitik ve Etkileşim Takip Sistemi
"""

import asyncio
import statistics
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Union

from analytics.unified_analytics_data_model import (
    TurkishExamType,
    TurkishSubject,
)
from content.unified_content_management import ContentType
from core.structured_logging import LogCategory, get_logger
from core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.ANALYTICS)
config = get_unified_config()


class EngagementMetric(Enum):
    """Types of engagement metrics"""

    VIEW_TIME = "view_time"
    COMPLETION_RATE = "completion_rate"
    INTERACTION_COUNT = "interaction_count"
    RETURN_VISITS = "return_visits"
    SHARING = "sharing"
    RATING = "rating"
    BOOKMARK = "bookmark"
    COMMENT = "comment"
    QUIZ_ATTEMPTS = "quiz_attempts"
    DOWNLOAD = "download"


class EngagementLevel(Enum):
    """Levels of user engagement"""

    VERY_LOW = "very_low"  # 0-20%
    LOW = "low"  # 20-40%
    MEDIUM = "medium"  # 40-60%
    HIGH = "high"  # 60-80%
    VERY_HIGH = "very_high"  # 80-100%


class ContentPerformanceCategory(Enum):
    """Content performance categories"""

    TOP_PERFORMER = "top_performer"
    GOOD_PERFORMER = "good_performer"
    AVERAGE_PERFORMER = "average_performer"
    POOR_PERFORMER = "poor_performer"
    NEEDS_IMPROVEMENT = "needs_improvement"


@dataclass
class EngagementEvent:
    """Individual engagement event"""

    event_id: str
    content_id: str
    user_id: int
    event_type: EngagementMetric

    # Event data
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    value: Union[float, int, str, bool] = None
    duration_seconds: float | None = None

    # Context information
    session_id: str | None = None
    device_type: str | None = None
    location: str | None = None
    referrer: str | None = None

    # Learning context
    subject: TurkishSubject | None = None
    exam_type: TurkishExamType | None = None
    difficulty_level: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "content_id": self.content_id,
            "user_id": self.user_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "duration_seconds": self.duration_seconds,
            "session_id": self.session_id,
            "device_type": self.device_type,
            "location": self.location,
            "referrer": self.referrer,
            "subject": self.subject.value if self.subject else None,
            "exam_type": self.exam_type.value if self.exam_type else None,
            "difficulty_level": self.difficulty_level,
            "metadata": self.metadata,
        }


@dataclass
class ContentEngagementSummary:
    """Summary of engagement metrics for content"""

    content_id: str
    content_title: str
    content_type: ContentType

    # Time period
    start_date: datetime
    end_date: datetime

    # Basic metrics
    total_views: int = 0
    unique_viewers: int = 0
    total_view_time_seconds: float = 0.0
    average_view_time_seconds: float = 0.0

    # Engagement metrics
    completion_rate: float = 0.0
    interaction_count: int = 0
    return_visitor_rate: float = 0.0
    engagement_score: float = 0.0

    # Learning metrics
    quiz_attempts: int = 0
    quiz_success_rate: float = 0.0
    bookmark_count: int = 0
    sharing_count: int = 0

    # Rating and feedback
    average_rating: float = 0.0
    rating_count: int = 0
    comment_count: int = 0

    # Performance categorization
    performance_category: ContentPerformanceCategory = (
        ContentPerformanceCategory.AVERAGE_PERFORMER
    )
    engagement_level: EngagementLevel = EngagementLevel.MEDIUM

    # Turkish education specific
    subject_performance_rank: int = 0
    exam_type_relevance: dict[TurkishExamType, float] = field(default_factory=dict)
    curriculum_alignment_score: float = 0.0

    def calculate_engagement_score(self) -> float:
        """Calculate comprehensive engagement score"""
        # Normalize metrics to 0-1 scale
        view_score = min(self.total_views / 1000, 1.0) * 20
        completion_score = self.completion_rate * 25
        interaction_score = min(self.interaction_count / 100, 1.0) * 20
        return_score = self.return_visitor_rate * 15
        rating_score = (self.average_rating / 5.0) * 20 if self.rating_count > 0 else 0

        self.engagement_score = (
            view_score
            + completion_score
            + interaction_score
            + return_score
            + rating_score
        )
        return self.engagement_score

    def determine_performance_category(self) -> ContentPerformanceCategory:
        """Determine performance category based on metrics"""
        score = self.calculate_engagement_score()

        if score >= 90:
            self.performance_category = ContentPerformanceCategory.TOP_PERFORMER
        elif score >= 75:
            self.performance_category = ContentPerformanceCategory.GOOD_PERFORMER
        elif score >= 50:
            self.performance_category = ContentPerformanceCategory.AVERAGE_PERFORMER
        elif score >= 30:
            self.performance_category = ContentPerformanceCategory.POOR_PERFORMER
        else:
            self.performance_category = ContentPerformanceCategory.NEEDS_IMPROVEMENT

        return self.performance_category

    def determine_engagement_level(self) -> EngagementLevel:
        """Determine engagement level"""
        score = self.calculate_engagement_score()

        if score >= 80:
            self.engagement_level = EngagementLevel.VERY_HIGH
        elif score >= 60:
            self.engagement_level = EngagementLevel.HIGH
        elif score >= 40:
            self.engagement_level = EngagementLevel.MEDIUM
        elif score >= 20:
            self.engagement_level = EngagementLevel.LOW
        else:
            self.engagement_level = EngagementLevel.VERY_LOW

        return self.engagement_level

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_id": self.content_id,
            "content_title": self.content_title,
            "content_type": self.content_type.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_views": self.total_views,
            "unique_viewers": self.unique_viewers,
            "total_view_time_seconds": self.total_view_time_seconds,
            "average_view_time_seconds": self.average_view_time_seconds,
            "completion_rate": self.completion_rate,
            "interaction_count": self.interaction_count,
            "return_visitor_rate": self.return_visitor_rate,
            "engagement_score": self.calculate_engagement_score(),
            "quiz_attempts": self.quiz_attempts,
            "quiz_success_rate": self.quiz_success_rate,
            "bookmark_count": self.bookmark_count,
            "sharing_count": self.sharing_count,
            "average_rating": self.average_rating,
            "rating_count": self.rating_count,
            "comment_count": self.comment_count,
            "performance_category": self.determine_performance_category().value,
            "engagement_level": self.determine_engagement_level().value,
            "subject_performance_rank": self.subject_performance_rank,
            "exam_type_relevance": {
                k.value: v for k, v in self.exam_type_relevance.items()
            },
            "curriculum_alignment_score": self.curriculum_alignment_score,
        }


@dataclass
class StudentEngagementProfile:
    """Profile of student's engagement patterns"""

    student_id: int

    # Time period
    start_date: datetime
    end_date: datetime

    # Activity metrics
    total_content_views: int = 0
    unique_content_viewed: int = 0
    total_study_time_hours: float = 0.0
    average_session_duration_minutes: float = 0.0

    # Engagement patterns
    preferred_content_types: list[ContentType] = field(default_factory=list)
    peak_activity_hours: list[int] = field(default_factory=list)
    most_engaged_subjects: list[TurkishSubject] = field(default_factory=list)

    # Learning behavior
    completion_rate: float = 0.0
    quiz_participation_rate: float = 0.0
    average_quiz_score: float = 0.0
    bookmark_usage_rate: float = 0.0

    # Interaction metrics
    comment_frequency: float = 0.0
    sharing_frequency: float = 0.0
    help_seeking_frequency: float = 0.0

    # Engagement scoring
    overall_engagement_score: float = 0.0
    engagement_trend: str = "stable"  # improving, declining, stable

    # Turkish exam preparation
    tyt_content_engagement: float = 0.0
    ayt_content_engagement: float = 0.0
    exam_preparation_intensity: float = 0.0

    def calculate_engagement_score(self) -> float:
        """Calculate overall engagement score"""
        # Activity component (40%)
        activity_score = (
            min(self.total_content_views / 100, 1.0) * 0.3
            + min(self.total_study_time_hours / 50, 1.0) * 0.7
        ) * 40

        # Quality component (35%)
        quality_score = (
            self.completion_rate * 0.4
            + self.quiz_participation_rate * 0.3
            + (self.average_quiz_score / 100) * 0.3
        ) * 35

        # Interaction component (25%)
        interaction_score = (
            min(self.comment_frequency / 5, 1.0) * 0.4
            + min(self.sharing_frequency / 2, 1.0) * 0.3
            + self.bookmark_usage_rate * 0.3
        ) * 25

        self.overall_engagement_score = (
            activity_score + quality_score + interaction_score
        )
        return self.overall_engagement_score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "student_id": self.student_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_content_views": self.total_content_views,
            "unique_content_viewed": self.unique_content_viewed,
            "total_study_time_hours": self.total_study_time_hours,
            "average_session_duration_minutes": self.average_session_duration_minutes,
            "preferred_content_types": [
                ct.value for ct in self.preferred_content_types
            ],
            "peak_activity_hours": self.peak_activity_hours,
            "most_engaged_subjects": [s.value for s in self.most_engaged_subjects],
            "completion_rate": self.completion_rate,
            "quiz_participation_rate": self.quiz_participation_rate,
            "average_quiz_score": self.average_quiz_score,
            "bookmark_usage_rate": self.bookmark_usage_rate,
            "comment_frequency": self.comment_frequency,
            "sharing_frequency": self.sharing_frequency,
            "help_seeking_frequency": self.help_seeking_frequency,
            "overall_engagement_score": self.calculate_engagement_score(),
            "engagement_trend": self.engagement_trend,
            "tyt_content_engagement": self.tyt_content_engagement,
            "ayt_content_engagement": self.ayt_content_engagement,
            "exam_preparation_intensity": self.exam_preparation_intensity,
        }


class EngagementTracker:
    """Tracks and processes engagement events"""

    def __init__(self):
        self.event_buffer: deque = deque(maxlen=10000)
        self.content_sessions: dict[str, dict[str, Any]] = defaultdict(
            dict
        )  # user_id:content_id -> session
        self.session_timeout_minutes = 30

    async def track_engagement_event(self, event: EngagementEvent) -> None:
        """Track an engagement event"""
        self.event_buffer.append(event)

        # Update ongoing sessions
        await self._update_content_session(event)

        logger.debug(
            f"Tracked engagement event: {event.event_type.value} for content {event.content_id}"
        )

    async def _update_content_session(self, event: EngagementEvent) -> None:
        """Update content viewing session"""
        session_key = f"{event.user_id}:{event.content_id}"

        if session_key not in self.content_sessions:
            # Start new session
            self.content_sessions[session_key] = {
                "start_time": event.timestamp,
                "last_activity": event.timestamp,
                "events": [],
                "total_duration": 0.0,
                "completed": False,
            }

        session = self.content_sessions[session_key]

        # Check if session timed out
        time_since_last = (
            event.timestamp - session["last_activity"]
        ).total_seconds() / 60
        if time_since_last > self.session_timeout_minutes:
            # Session timed out, start new one
            await self._finalize_session(session_key, session)
            self.content_sessions[session_key] = {
                "start_time": event.timestamp,
                "last_activity": event.timestamp,
                "events": [],
                "total_duration": 0.0,
                "completed": False,
            }
            session = self.content_sessions[session_key]

        # Update session
        session["last_activity"] = event.timestamp
        session["events"].append(event)

        # Update duration
        if event.duration_seconds:
            session["total_duration"] += event.duration_seconds

        # Mark completion
        if event.event_type == EngagementMetric.COMPLETION_RATE and event.value:
            session["completed"] = True

    async def _finalize_session(
        self, session_key: str, session: dict[str, Any]
    ) -> None:
        """Finalize a content viewing session"""
        # Calculate final session metrics
        session_duration = (
            session["last_activity"] - session["start_time"]
        ).total_seconds()

        # Log session completion
        logger.debug(
            f"Finalized content session {session_key}: {session_duration:.1f}s"
        )

    async def get_content_engagement_events(
        self, content_id: str, start_date: datetime, end_date: datetime
    ) -> list[EngagementEvent]:
        """Get engagement events for specific content"""
        events = []

        for event in self.event_buffer:
            if (
                event.content_id == content_id
                and start_date <= event.timestamp <= end_date
            ):
                events.append(event)

        return sorted(events, key=lambda e: e.timestamp)

    async def get_user_engagement_events(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> list[EngagementEvent]:
        """Get engagement events for specific user"""
        events = []

        for event in self.event_buffer:
            if event.user_id == user_id and start_date <= event.timestamp <= end_date:
                events.append(event)

        return sorted(events, key=lambda e: e.timestamp)

    async def cleanup_old_sessions(self) -> None:
        """Clean up old inactive sessions"""
        current_time = datetime.now(UTC)
        expired_sessions = []

        for session_key, session in self.content_sessions.items():
            time_since_last = (
                current_time - session["last_activity"]
            ).total_seconds() / 60
            if (
                time_since_last > self.session_timeout_minutes * 2
            ):  # Double timeout for cleanup
                expired_sessions.append(session_key)

        for session_key in expired_sessions:
            session = self.content_sessions.pop(session_key)
            await self._finalize_session(session_key, session)

        logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")


class ContentAnalyticsEngine:
    """Engine for analyzing content performance and engagement"""

    def __init__(self, engagement_tracker: EngagementTracker):
        self.engagement_tracker = engagement_tracker
        self.analytics_cache: dict[str, Any] = {}
        self.cache_ttl_seconds = 3600  # 1 hour

    async def analyze_content_engagement(
        self,
        content_id: str,
        start_date: datetime,
        end_date: datetime,
        content_metadata: dict[str, Any] | None = None,
    ) -> ContentEngagementSummary:
        """Analyze engagement for specific content"""

        # Check cache first
        cache_key = (
            f"content_engagement:{content_id}:{start_date.date()}:{end_date.date()}"
        )
        if cache_key in self.analytics_cache:
            cached_data = self.analytics_cache[cache_key]
            if (
                datetime.now(UTC) - cached_data["timestamp"]
            ).total_seconds() < self.cache_ttl_seconds:
                return cached_data["summary"]

        # Get engagement events
        events = await self.engagement_tracker.get_content_engagement_events(
            content_id, start_date, end_date
        )

        # Initialize summary
        summary = ContentEngagementSummary(
            content_id=content_id,
            content_title=content_metadata.get("title", "Unknown")
            if content_metadata
            else "Unknown",
            content_type=ContentType(content_metadata.get("content_type", "document"))
            if content_metadata
            else ContentType.DOCUMENT,
            start_date=start_date,
            end_date=end_date,
        )

        # Analyze events
        unique_viewers = set()
        view_times = []
        interactions = 0
        quiz_attempts = 0
        quiz_successes = 0
        bookmarks = 0
        shares = 0
        ratings = []
        comments = 0
        completions = 0
        total_views = 0

        for event in events:
            unique_viewers.add(event.user_id)

            if event.event_type == EngagementMetric.VIEW_TIME:
                total_views += 1
                if event.duration_seconds:
                    view_times.append(event.duration_seconds)

            elif event.event_type == EngagementMetric.INTERACTION_COUNT:
                interactions += int(event.value) if event.value else 1

            elif event.event_type == EngagementMetric.QUIZ_ATTEMPTS:
                quiz_attempts += 1
                if event.metadata.get("success"):
                    quiz_successes += 1

            elif event.event_type == EngagementMetric.BOOKMARK:
                bookmarks += 1

            elif event.event_type == EngagementMetric.SHARING:
                shares += 1

            elif event.event_type == EngagementMetric.RATING:
                if event.value and isinstance(event.value, (int, float)):
                    ratings.append(float(event.value))

            elif event.event_type == EngagementMetric.COMMENT:
                comments += 1

            elif event.event_type == EngagementMetric.COMPLETION_RATE:
                if event.value:
                    completions += 1

        # Calculate metrics
        summary.total_views = total_views
        summary.unique_viewers = len(unique_viewers)
        summary.total_view_time_seconds = sum(view_times)
        summary.average_view_time_seconds = (
            statistics.mean(view_times) if view_times else 0.0
        )
        summary.completion_rate = (
            (completions / total_views) * 100 if total_views > 0 else 0.0
        )
        summary.interaction_count = interactions
        summary.return_visitor_rate = self._calculate_return_visitor_rate(events)
        summary.quiz_attempts = quiz_attempts
        summary.quiz_success_rate = (
            (quiz_successes / quiz_attempts) * 100 if quiz_attempts > 0 else 0.0
        )
        summary.bookmark_count = bookmarks
        summary.sharing_count = shares
        summary.average_rating = statistics.mean(ratings) if ratings else 0.0
        summary.rating_count = len(ratings)
        summary.comment_count = comments

        # Determine performance and engagement levels
        summary.determine_performance_category()
        summary.determine_engagement_level()

        # Cache results
        self.analytics_cache[cache_key] = {
            "summary": summary,
            "timestamp": datetime.now(UTC),
        }

        return summary

    def _calculate_return_visitor_rate(self, events: list[EngagementEvent]) -> float:
        """Calculate return visitor rate"""
        user_visit_counts = defaultdict(int)

        for event in events:
            if event.event_type == EngagementMetric.VIEW_TIME:
                user_visit_counts[event.user_id] += 1

        if not user_visit_counts:
            return 0.0

        return_visitors = len(
            [uid for uid, count in user_visit_counts.items() if count > 1]
        )
        total_visitors = len(user_visit_counts)

        return (return_visitors / total_visitors) * 100 if total_visitors > 0 else 0.0

    async def analyze_student_engagement(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> StudentEngagementProfile:
        """Analyze engagement patterns for specific student"""

        # Get student's engagement events
        events = await self.engagement_tracker.get_user_engagement_events(
            student_id, start_date, end_date
        )

        # Initialize profile
        profile = StudentEngagementProfile(
            student_id=student_id, start_date=start_date, end_date=end_date
        )

        # Analyze events
        content_views = set()
        study_sessions = []
        content_type_counts = defaultdict(int)
        hour_activity = defaultdict(int)
        subject_engagement = defaultdict(float)

        quiz_attempts = 0
        quiz_scores = []
        bookmarks = 0
        comments = 0
        shares = 0
        completions = 0
        total_views = 0

        for event in events:
            if event.event_type == EngagementMetric.VIEW_TIME:
                content_views.add(event.content_id)
                total_views += 1

                # Track activity hours
                hour = event.timestamp.hour
                hour_activity[hour] += 1

                # Track study time
                if event.duration_seconds:
                    study_sessions.append(event.duration_seconds)

                # Track subject engagement
                if event.subject:
                    subject_engagement[event.subject] += event.duration_seconds or 30

            elif event.event_type == EngagementMetric.QUIZ_ATTEMPTS:
                quiz_attempts += 1
                if event.metadata.get("score"):
                    quiz_scores.append(float(event.metadata["score"]))

            elif event.event_type == EngagementMetric.BOOKMARK:
                bookmarks += 1

            elif event.event_type == EngagementMetric.COMMENT:
                comments += 1

            elif event.event_type == EngagementMetric.SHARING:
                shares += 1

            elif event.event_type == EngagementMetric.COMPLETION_RATE:
                if event.value:
                    completions += 1

        # Calculate metrics
        profile.total_content_views = total_views
        profile.unique_content_viewed = len(content_views)
        profile.total_study_time_hours = (
            sum(study_sessions) / 3600 if study_sessions else 0.0
        )
        profile.average_session_duration_minutes = (
            (statistics.mean(study_sessions) / 60) if study_sessions else 0.0
        )

        # Determine patterns
        profile.peak_activity_hours = sorted(
            hour_activity.keys(), key=hour_activity.get, reverse=True
        )[:3]
        profile.most_engaged_subjects = sorted(
            subject_engagement.keys(), key=subject_engagement.get, reverse=True
        )[:3]

        # Calculate rates
        profile.completion_rate = (
            (completions / total_views) * 100 if total_views > 0 else 0.0
        )
        profile.quiz_participation_rate = (
            (quiz_attempts / total_views) * 100 if total_views > 0 else 0.0
        )
        profile.average_quiz_score = (
            statistics.mean(quiz_scores) if quiz_scores else 0.0
        )
        profile.bookmark_usage_rate = (
            (bookmarks / total_views) * 100 if total_views > 0 else 0.0
        )

        # Calculate frequencies (per week)
        weeks = max(1, (end_date - start_date).days / 7)
        profile.comment_frequency = comments / weeks
        profile.sharing_frequency = shares / weeks

        # Calculate exam type engagement
        tyt_time = sum(
            subject_engagement.get(subject, 0)
            for subject in [TurkishSubject.MATEMATIK, TurkishSubject.TURKCE]
        )
        ayt_time = sum(
            subject_engagement.get(subject, 0)
            for subject in [
                TurkishSubject.FIZIK,
                TurkishSubject.KIMYA,
                TurkishSubject.BIYOLOJI,
            ]
        )
        total_time = sum(subject_engagement.values())

        if total_time > 0:
            profile.tyt_content_engagement = (tyt_time / total_time) * 100
            profile.ayt_content_engagement = (ayt_time / total_time) * 100

        # Calculate engagement trend (simplified)
        profile.engagement_trend = self._calculate_engagement_trend(events)

        return profile

    def _calculate_engagement_trend(self, events: list[EngagementEvent]) -> str:
        """Calculate engagement trend over time"""
        if len(events) < 10:
            return "stable"

        # Split events into first and second half
        mid_point = len(events) // 2
        first_half = events[:mid_point]
        second_half = events[mid_point:]

        first_half_activity = len(first_half)
        second_half_activity = len(second_half)

        # Calculate change rate
        change_rate = (
            (second_half_activity - first_half_activity) / first_half_activity
            if first_half_activity > 0
            else 0
        )

        if change_rate > 0.2:
            return "improving"
        if change_rate < -0.2:
            return "declining"
        return "stable"

    async def generate_content_recommendations(
        self, content_summaries: list[ContentEngagementSummary]
    ) -> list[dict[str, Any]]:
        """Generate recommendations for improving content engagement"""
        recommendations = []

        for summary in content_summaries:
            content_recommendations = []

            # Low engagement recommendations
            if summary.engagement_level in [
                EngagementLevel.LOW,
                EngagementLevel.VERY_LOW,
            ]:
                content_recommendations.append(
                    {
                        "type": "engagement_improvement",
                        "priority": "high",
                        "recommendation": "İçerik etkileşimi düşük - multimedya öğeleri ekleyin",
                        "recommendation_en": "Low engagement - add multimedia elements",
                        "action": "add_multimedia",
                    }
                )

            # Low completion rate
            if summary.completion_rate < 50:
                content_recommendations.append(
                    {
                        "type": "completion_rate",
                        "priority": "high",
                        "recommendation": "Tamamlanma oranı düşük - içeriği kısa bölümlere ayırın",
                        "recommendation_en": "Low completion rate - break content into shorter segments",
                        "action": "segment_content",
                    }
                )

            # Long viewing time but low completion
            if summary.average_view_time_seconds > 600 and summary.completion_rate < 70:
                content_recommendations.append(
                    {
                        "type": "content_length",
                        "priority": "medium",
                        "recommendation": "İçerik çok uzun görünüyor - önemli noktaları öne çıkarın",
                        "recommendation_en": "Content appears too long - highlight key points",
                        "action": "highlight_key_points",
                    }
                )

            # Low interaction
            if summary.interaction_count < 10:
                content_recommendations.append(
                    {
                        "type": "interaction",
                        "priority": "medium",
                        "recommendation": "Etkileşim düşük - sorular ve aktiviteler ekleyin",
                        "recommendation_en": "Low interaction - add questions and activities",
                        "action": "add_interactions",
                    }
                )

            # Good performance recognition
            if summary.performance_category == ContentPerformanceCategory.TOP_PERFORMER:
                content_recommendations.append(
                    {
                        "type": "success_recognition",
                        "priority": "low",
                        "recommendation": "Mükemmel performans! Bu format diğer içeriklerde de kullanılabilir",
                        "recommendation_en": "Excellent performance! This format can be used for other content",
                        "action": "replicate_format",
                    }
                )

            recommendations.append(
                {
                    "content_id": summary.content_id,
                    "content_title": summary.content_title,
                    "performance_category": summary.performance_category.value,
                    "engagement_score": summary.engagement_score,
                    "recommendations": content_recommendations,
                }
            )

        return recommendations

    async def get_engagement_insights(
        self,
        start_date: datetime,
        end_date: datetime,
        content_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive engagement insights"""

        insights = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": (end_date - start_date).days,
            },
            "overall_metrics": {},
            "top_performing_content": [],
            "engagement_trends": {},
            "subject_performance": {},
            "recommendations": [],
        }

        # Get all events in period
        all_events = []
        if content_ids:
            for content_id in content_ids:
                events = await self.engagement_tracker.get_content_engagement_events(
                    content_id, start_date, end_date
                )
                all_events.extend(events)
        else:
            # For demo, use events from buffer
            all_events = [
                event
                for event in self.engagement_tracker.event_buffer
                if start_date <= event.timestamp <= end_date
            ]

        # Calculate overall metrics
        total_events = len(all_events)
        unique_users = len(set(event.user_id for event in all_events))
        unique_content = len(set(event.content_id for event in all_events))

        view_events = [
            e for e in all_events if e.event_type == EngagementMetric.VIEW_TIME
        ]
        total_view_time = sum(e.duration_seconds or 0 for e in view_events)

        insights["overall_metrics"] = {
            "total_events": total_events,
            "unique_users": unique_users,
            "unique_content": unique_content,
            "total_view_time_hours": total_view_time / 3600,
            "average_session_duration_minutes": (
                total_view_time / len(view_events) / 60
            )
            if view_events
            else 0,
            "events_per_user": total_events / unique_users if unique_users > 0 else 0,
        }

        # Subject performance
        subject_metrics = defaultdict(
            lambda: {"events": 0, "view_time": 0, "users": set()}
        )

        for event in all_events:
            if event.subject:
                subject_metrics[event.subject]["events"] += 1
                subject_metrics[event.subject]["users"].add(event.user_id)
                if event.duration_seconds:
                    subject_metrics[event.subject][
                        "view_time"
                    ] += event.duration_seconds

        insights["subject_performance"] = {
            subject.value: {
                "total_events": metrics["events"],
                "unique_users": len(metrics["users"]),
                "total_view_time_hours": metrics["view_time"] / 3600,
                "avg_engagement_per_user": metrics["events"] / len(metrics["users"])
                if metrics["users"]
                else 0,
            }
            for subject, metrics in subject_metrics.items()
        }

        return insights


class ContentAnalyticsService:
    """Main service for content analytics and engagement tracking"""

    def __init__(self):
        self.engagement_tracker = EngagementTracker()
        self.analytics_engine = ContentAnalyticsEngine(self.engagement_tracker)

        # Background tasks
        self._cleanup_task = None
        self._is_running = False

    async def start_service(self) -> None:
        """Start the analytics service"""
        if self._is_running:
            return

        self._is_running = True

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._background_cleanup())

        logger.info("Content analytics service started")

    async def stop_service(self) -> None:
        """Stop the analytics service"""
        self._is_running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Content analytics service stopped")

    async def _background_cleanup(self) -> None:
        """Background task for cleaning up old data"""
        while self._is_running:
            try:
                await self.engagement_tracker.cleanup_old_sessions()
                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
                await asyncio.sleep(60)

    async def track_content_view(
        self,
        content_id: str,
        user_id: int,
        duration_seconds: float,
        session_id: str | None = None,
        metadata: dict[str, Any] = None,
    ) -> None:
        """Track content view event"""
        event = EngagementEvent(
            content_id=content_id,
            user_id=user_id,
            event_type=EngagementMetric.VIEW_TIME,
            duration_seconds=duration_seconds,
            session_id=session_id,
            metadata=metadata or {},
        )

        await self.engagement_tracker.track_engagement_event(event)

    async def track_content_completion(
        self,
        content_id: str,
        user_id: int,
        completion_percentage: float,
        session_id: str | None = None,
    ) -> None:
        """Track content completion event"""
        event = EngagementEvent(
            content_id=content_id,
            user_id=user_id,
            event_type=EngagementMetric.COMPLETION_RATE,
            value=completion_percentage >= 90.0,  # Consider 90%+ as complete
            metadata={"completion_percentage": completion_percentage},
        )

        await self.engagement_tracker.track_engagement_event(event)

    async def track_quiz_attempt(
        self,
        content_id: str,
        user_id: int,
        score: float,
        success: bool,
        session_id: str | None = None,
    ) -> None:
        """Track quiz attempt event"""
        event = EngagementEvent(
            content_id=content_id,
            user_id=user_id,
            event_type=EngagementMetric.QUIZ_ATTEMPTS,
            value=score,
            metadata={"score": score, "success": success},
        )

        await self.engagement_tracker.track_engagement_event(event)

    async def track_content_rating(
        self,
        content_id: str,
        user_id: int,
        rating: float,
        session_id: str | None = None,
    ) -> None:
        """Track content rating event"""
        event = EngagementEvent(
            content_id=content_id,
            user_id=user_id,
            event_type=EngagementMetric.RATING,
            value=rating,
        )

        await self.engagement_tracker.track_engagement_event(event)

    async def track_content_bookmark(
        self, content_id: str, user_id: int, session_id: str | None = None
    ) -> None:
        """Track content bookmark event"""
        event = EngagementEvent(
            content_id=content_id, user_id=user_id, event_type=EngagementMetric.BOOKMARK
        )

        await self.engagement_tracker.track_engagement_event(event)

    async def get_content_analytics(
        self,
        content_id: str,
        days_back: int = 30,
        content_metadata: dict[str, Any] | None = None,
    ) -> ContentEngagementSummary:
        """Get analytics for specific content"""
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days_back)

        return await self.analytics_engine.analyze_content_engagement(
            content_id, start_date, end_date, content_metadata
        )

    async def get_student_analytics(
        self, student_id: int, days_back: int = 30
    ) -> StudentEngagementProfile:
        """Get analytics for specific student"""
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days_back)

        return await self.analytics_engine.analyze_student_engagement(
            student_id, start_date, end_date
        )

    async def get_platform_insights(self, days_back: int = 30) -> dict[str, Any]:
        """Get platform-wide engagement insights"""
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days_back)

        return await self.analytics_engine.get_engagement_insights(start_date, end_date)

    async def generate_content_recommendations(
        self, content_ids: list[str], days_back: int = 30
    ) -> list[dict[str, Any]]:
        """Generate content improvement recommendations"""
        summaries = []

        for content_id in content_ids:
            summary = await self.get_content_analytics(content_id, days_back)
            summaries.append(summary)

        return await self.analytics_engine.generate_content_recommendations(summaries)


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Content Analytics and Engagement Tracking System")
    print("=" * 60)

    async def test_analytics_system():
        """Test content analytics system"""
        service = ContentAnalyticsService()
        await service.start_service()

        try:
            # Simulate content interactions
            content_id = "content_123"
            user_ids = [1001, 1002, 1003, 1004, 1005]

            print("Simulating content interactions...")

            # Track various engagement events
            for user_id in user_ids:
                # Track content views
                await service.track_content_view(
                    content_id=content_id,
                    user_id=user_id,
                    duration_seconds=300 + (user_id % 200),  # Vary duration
                    metadata={"device": "mobile" if user_id % 2 == 0 else "desktop"},
                )

                # Track completions
                completion_rate = 75 + (user_id % 25)  # Vary completion
                await service.track_content_completion(
                    content_id=content_id,
                    user_id=user_id,
                    completion_percentage=completion_rate,
                )

                # Track quiz attempts (some users)
                if user_id % 2 == 0:
                    score = 70 + (user_id % 30)
                    await service.track_quiz_attempt(
                        content_id=content_id,
                        user_id=user_id,
                        score=score,
                        success=score >= 80,
                    )

                # Track ratings (some users)
                if user_id % 3 == 0:
                    rating = 3 + (user_id % 3)  # 3-5 rating
                    await service.track_content_rating(
                        content_id=content_id, user_id=user_id, rating=rating
                    )

                # Track bookmarks (few users)
                if user_id % 4 == 0:
                    await service.track_content_bookmark(
                        content_id=content_id, user_id=user_id
                    )

            # Wait a bit for processing
            await asyncio.sleep(1)

            # Get content analytics
            print("\nAnalyzing content performance...")
            content_metadata = {
                "title": "Türev Alma Kuralları",
                "content_type": "video",
            }

            content_analytics = await service.get_content_analytics(
                content_id=content_id, days_back=1, content_metadata=content_metadata
            )

            print(f"Content Analytics for '{content_analytics.content_title}':")
            print(f"  Total Views: {content_analytics.total_views}")
            print(f"  Unique Viewers: {content_analytics.unique_viewers}")
            print(
                f"  Avg View Time: {content_analytics.average_view_time_seconds:.1f}s"
            )
            print(f"  Completion Rate: {content_analytics.completion_rate:.1f}%")
            print(f"  Engagement Score: {content_analytics.engagement_score:.1f}")
            print(
                f"  Performance Category: {content_analytics.performance_category.value}"
            )
            print(f"  Quiz Attempts: {content_analytics.quiz_attempts}")
            print(f"  Average Rating: {content_analytics.average_rating:.1f}")

            # Get student analytics
            print("\nAnalyzing student engagement...")
            student_analytics = await service.get_student_analytics(
                student_id=1001, days_back=1
            )

            print(f"Student {student_analytics.student_id} Engagement:")
            print(f"  Total Content Views: {student_analytics.total_content_views}")
            print(f"  Study Time: {student_analytics.total_study_time_hours:.2f} hours")
            print(f"  Completion Rate: {student_analytics.completion_rate:.1f}%")
            print(
                f"  Overall Engagement Score: {student_analytics.overall_engagement_score:.1f}"
            )
            print(f"  Engagement Trend: {student_analytics.engagement_trend}")

            # Get platform insights
            print("\nPlatform insights...")
            platform_insights = await service.get_platform_insights(days_back=1)

            print("Platform Metrics:")
            print(
                f"  Total Events: {platform_insights['overall_metrics']['total_events']}"
            )
            print(
                f"  Unique Users: {platform_insights['overall_metrics']['unique_users']}"
            )
            print(
                f"  Total View Time: {platform_insights['overall_metrics']['total_view_time_hours']:.2f} hours"
            )

            # Generate recommendations
            print("\nGenerating recommendations...")
            recommendations = await service.generate_content_recommendations(
                [content_id], days_back=1
            )

            if recommendations:
                content_rec = recommendations[0]
                print(f"Recommendations for '{content_rec['content_title']}':")
                for rec in content_rec["recommendations"]:
                    print(f"  - {rec['recommendation']} (Priority: {rec['priority']})")

        finally:
            await service.stop_service()

    # Run test
    asyncio.run(test_analytics_system())
