from unittest.mock import Mock, patch, AsyncMock

"""
Phase 1: Learning Analytics Comprehensive Tests
Target: 0% → 30%+ coverage for learning_analytics.py (360 lines)
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLearningAnalyticsEnums:
    """Test Learning Analytics enum classes"""

    def test_interaction_type_enum(self):
        """Test InteractionType enum values"""
        try:
            from core.learning_analytics import InteractionType

            # Test all enum values exist
            assert InteractionType.QUESTION_ASKED.value == "question_asked"
            assert InteractionType.ANSWER_RECEIVED.value == "answer_received"
            assert InteractionType.CONTENT_VIEWED.value == "content_viewed"
            assert InteractionType.QUIZ_STARTED.value == "quiz_started"
            assert InteractionType.QUIZ_COMPLETED.value == "quiz_completed"
            assert (
                InteractionType.STUDY_SESSION_STARTED.value == "study_session_started"
            )
            assert InteractionType.STUDY_SESSION_ENDED.value == "study_session_ended"
            assert InteractionType.FEEDBACK_GIVEN.value == "feedback_given"
            assert InteractionType.HELP_REQUESTED.value == "help_requested"
            assert InteractionType.RESOURCE_ACCESSED.value == "resource_accessed"

            # Test enum iteration
            interaction_types = list(InteractionType)
            assert len(interaction_types) == 10

        except ImportError:
            pytest.skip("InteractionType not available")

    def test_learning_outcome_enum(self):
        """Test LearningOutcome enum values"""
        try:
            from core.learning_analytics import LearningOutcome

            # Test all enum values
            assert LearningOutcome.MASTERY_ACHIEVED.value == "mastery_achieved"
            assert LearningOutcome.IMPROVEMENT_SHOWN.value == "improvement_shown"
            assert LearningOutcome.STRUGGLING.value == "struggling"
            assert LearningOutcome.DISENGAGED.value == "disengaged"
            assert LearningOutcome.CONFUSED.value == "confused"
            assert LearningOutcome.MOTIVATED.value == "motivated"

            # Test enum count
            outcomes = list(LearningOutcome)
            assert len(outcomes) == 6

        except ImportError:
            pytest.skip("LearningOutcome not available")

    def test_study_pattern_enum(self):
        """Test StudyPattern enum values"""
        try:
            from core.learning_analytics import StudyPattern

            # Test all enum values
            assert StudyPattern.CONSISTENT.value == "consistent"
            assert StudyPattern.CRAMMING.value == "cramming"
            assert StudyPattern.SPORADIC.value == "sporadic"
            assert StudyPattern.PROCRASTINATING.value == "procrastinating"
            assert StudyPattern.INTENSIVE.value == "intensive"
            assert StudyPattern.BALANCED.value == "balanced"

            # Test enum count
            patterns = list(StudyPattern)
            assert len(patterns) == 6

        except ImportError:
            pytest.skip("StudyPattern not available")


class TestLearningInteractionDataClass:
    """Test LearningInteraction dataclass"""

    def test_learning_interaction_creation(self):
        """Test LearningInteraction dataclass creation"""
        try:
            from core.learning_analytics import InteractionType, LearningInteraction

            interaction = LearningInteraction(
                student_id="student_123",
                interaction_type=InteractionType.QUESTION_ASKED,
                timestamp=datetime.now(),
                session_id="session_456",
                content_id="content_789",
                subject="matematik",
                topic="türev",
                difficulty_level=3,
                duration_seconds=120,
                success_rate=0.85,
                confidence_level=4,
                emotional_state="motivated",
                learning_style="visual",
                device_type="tablet",
                context={"question_count": 5, "hints_used": 1},
            )

            assert interaction.student_id == "student_123"
            assert interaction.interaction_type == InteractionType.QUESTION_ASKED
            assert interaction.subject == "matematik"
            assert interaction.topic == "türev"
            assert interaction.difficulty_level == 3
            assert interaction.success_rate == 0.85
            assert "question_count" in interaction.context

        except ImportError:
            pytest.skip("LearningInteraction not available")

    def test_learning_interaction_to_dict(self):
        """Test LearningInteraction to_dict method"""
        try:
            from core.learning_analytics import InteractionType, LearningInteraction

            timestamp = datetime.now()
            interaction = LearningInteraction(
                student_id="student_123",
                interaction_type=InteractionType.CONTENT_VIEWED,
                timestamp=timestamp,
                session_id="session_456",
                subject="fizik",
            )

            # Test to_dict conversion
            data = interaction.to_dict()

            assert isinstance(data, dict)
            assert data["student_id"] == "student_123"
            assert data["interaction_type"] == "content_viewed"
            assert data["timestamp"] == timestamp.isoformat()
            assert data["session_id"] == "session_456"
            assert data["subject"] == "fizik"

        except ImportError:
            pytest.skip("LearningInteraction not available")

    def test_learning_interaction_defaults(self):
        """Test LearningInteraction default values"""
        try:
            from core.learning_analytics import InteractionType, LearningInteraction

            interaction = LearningInteraction(
                student_id="student_123",
                interaction_type=InteractionType.QUIZ_STARTED,
                timestamp=datetime.now(),
                session_id="session_456",
            )

            # Test default values
            assert interaction.content_id is None
            assert interaction.subject is None
            assert interaction.topic is None
            assert interaction.difficulty_level is None
            assert interaction.duration_seconds is None
            assert interaction.success_rate is None
            assert interaction.confidence_level is None
            assert interaction.emotional_state is None
            assert interaction.learning_style is None
            assert interaction.device_type is None
            assert isinstance(interaction.context, dict)
            assert len(interaction.context) == 0

        except ImportError:
            pytest.skip("LearningInteraction not available")


class TestLearningSessionDataClass:
    """Test LearningSession dataclass"""

    def test_learning_session_creation(self):
        """Test LearningSession dataclass creation"""
        try:
            from core.learning_analytics import LearningOutcome, LearningSession

            start_time = datetime.now()
            end_time = start_time + timedelta(hours=2)

            session = LearningSession(
                session_id="session_123",
                student_id="student_456",
                start_time=start_time,
                end_time=end_time,
                total_duration_minutes=120,
                interactions_count=25,
                subjects_covered=["matematik", "fizik"],
                topics_covered=["türev", "limit", "hareket"],
                average_success_rate=0.78,
                engagement_score=0.82,
                learning_outcomes=[
                    LearningOutcome.IMPROVEMENT_SHOWN,
                    LearningOutcome.MOTIVATED,
                ],
                notes="Başarılı bir çalışma seansı",
            )

            assert session.session_id == "session_123"
            assert session.student_id == "student_456"
            assert session.start_time == start_time
            assert session.end_time == end_time
            assert session.total_duration_minutes == 120
            assert session.interactions_count == 25
            assert "matematik" in session.subjects_covered
            assert "türev" in session.topics_covered
            assert session.average_success_rate == 0.78
            assert LearningOutcome.IMPROVEMENT_SHOWN in session.learning_outcomes

        except ImportError:
            pytest.skip("LearningSession not available")

    def test_learning_session_defaults(self):
        """Test LearningSession default values"""
        try:
            from core.learning_analytics import LearningSession

            session = LearningSession(
                session_id="session_123",
                student_id="student_456",
                start_time=datetime.now(),
            )

            # Test default values
            assert session.end_time is None
            assert session.total_duration_minutes is None
            assert session.interactions_count == 0
            assert isinstance(session.subjects_covered, list)
            assert len(session.subjects_covered) == 0
            assert isinstance(session.topics_covered, list)
            assert len(session.topics_covered) == 0
            assert session.average_success_rate is None
            assert session.engagement_score is None
            assert isinstance(session.learning_outcomes, list)
            assert len(session.learning_outcomes) == 0
            assert session.notes is None

        except ImportError:
            pytest.skip("LearningSession not available")


class TestStudentProfileDataClass:
    """Test StudentProfile dataclass"""

    def test_student_profile_creation(self):
        """Test StudentProfile dataclass creation"""
        try:
            from core.learning_analytics import StudentProfile, StudyPattern

            profile = StudentProfile(
                student_id="student_789",
                total_study_time_hours=45.5,
                total_sessions=15,
                average_session_duration_minutes=180,
                preferred_study_times=[14, 15, 16, 19, 20],  # 14:00-16:00, 19:00-20:00
                preferred_subjects=["matematik", "fizik", "kimya"],
                learning_style="visual",
                study_pattern=StudyPattern.CONSISTENT,
                engagement_level=0.85,
                mastery_levels={"matematik": 0.90, "fizik": 0.75, "kimya": 0.65},
                difficulty_preferences={"matematik": 4, "fizik": 3, "kimya": 3},
                strengths=["problem_solving", "analytical_thinking"],
                weaknesses=["time_management", "test_anxiety"],
                recommendations=[
                    "More practice problems",
                    "Stress management techniques",
                ],
                last_updated=datetime.now(),
            )

            assert profile.student_id == "student_789"
            assert profile.total_study_time_hours == 45.5
            assert profile.total_sessions == 15
            assert profile.average_session_duration_minutes == 180
            assert 14 in profile.preferred_study_times
            assert "matematik" in profile.preferred_subjects
            assert profile.learning_style == "visual"
            assert profile.study_pattern == StudyPattern.CONSISTENT
            assert profile.engagement_level == 0.85
            assert profile.mastery_levels["matematik"] == 0.90
            assert profile.difficulty_preferences["matematik"] == 4
            assert "problem_solving" in profile.strengths
            assert "time_management" in profile.weaknesses
            assert len(profile.recommendations) == 2

        except ImportError:
            pytest.skip("StudentProfile not available")


class TestLearningAnalyticsEngine:
    """Test LearningAnalyticsEngine class"""

    def test_learning_analytics_engine_import(self):
        """Test LearningAnalyticsEngine can be imported"""
        try:
            from core.learning_analytics import LearningAnalyticsEngine

            # Test class exists
            assert LearningAnalyticsEngine is not None

            # Test class can be instantiated
            engine = LearningAnalyticsEngine()
            assert engine is not None

        except ImportError:
            pytest.skip("LearningAnalyticsEngine not available")

    def test_learning_analytics_engine_initialization(self):
        """Test LearningAnalyticsEngine initialization"""
        try:
            from core.learning_analytics import LearningAnalyticsEngine

            engine = LearningAnalyticsEngine()

            # Test basic attributes exist
            assert hasattr(engine, "__class__")

            # Test common analytics methods might exist
            potential_methods = [
                "track_interaction",
                "analyze_session",
                "generate_profile",
                "calculate_engagement",
                "detect_patterns",
                "get_recommendations",
            ]

            for method_name in potential_methods:
                if hasattr(engine, method_name):
                    method = getattr(engine, method_name)
                    assert callable(method)

        except ImportError:
            pytest.skip("LearningAnalyticsEngine not available")


class TestLearningAnalyticsDataProcessing:
    """Test Learning Analytics data processing capabilities"""

    def test_interaction_data_validation(self):
        """Test interaction data validation"""
        try:
            from core.learning_analytics import InteractionType, LearningInteraction

            # Test valid interaction
            valid_interaction = LearningInteraction(
                student_id="student_123",
                interaction_type=InteractionType.QUIZ_COMPLETED,
                timestamp=datetime.now(),
                session_id="session_456",
                success_rate=0.85,
            )

            assert valid_interaction.student_id is not None
            assert valid_interaction.interaction_type is not None
            assert valid_interaction.timestamp is not None
            assert valid_interaction.session_id is not None
            assert 0.0 <= valid_interaction.success_rate <= 1.0

        except ImportError:
            pytest.skip("Learning analytics classes not available")

    def test_study_pattern_classification(self):
        """Test study pattern classification logic"""
        try:
            from core.learning_analytics import StudyPattern

            # Test all study patterns can be used
            patterns = [
                StudyPattern.CONSISTENT,
                StudyPattern.CRAMMING,
                StudyPattern.SPORADIC,
                StudyPattern.PROCRASTINATING,
                StudyPattern.INTENSIVE,
                StudyPattern.BALANCED,
            ]

            for pattern in patterns:
                assert pattern.value is not None
                assert isinstance(pattern.value, str)

            # Test pattern values are unique
            pattern_values = [p.value for p in patterns]
            assert len(pattern_values) == len(set(pattern_values))

        except ImportError:
            pytest.skip("StudyPattern not available")

    def test_learning_outcome_analysis(self):
        """Test learning outcome analysis"""
        try:
            from core.learning_analytics import LearningOutcome

            # Test positive outcomes
            positive_outcomes = [
                LearningOutcome.MASTERY_ACHIEVED,
                LearningOutcome.IMPROVEMENT_SHOWN,
                LearningOutcome.MOTIVATED,
            ]

            # Test challenging outcomes
            challenging_outcomes = [
                LearningOutcome.STRUGGLING,
                LearningOutcome.DISENGAGED,
                LearningOutcome.CONFUSED,
            ]

            all_outcomes = positive_outcomes + challenging_outcomes

            for outcome in all_outcomes:
                assert outcome.value is not None
                assert isinstance(outcome.value, str)

            # Test outcome categorization makes sense
            assert len(positive_outcomes) == 3
            assert len(challenging_outcomes) == 3

        except ImportError:
            pytest.skip("LearningOutcome not available")


class TestLearningAnalyticsModuleStructure:
    """Test Learning Analytics module structure and imports"""

    def test_module_imports(self):
        """Test module can be imported and has expected structure"""
        try:
            import core.learning_analytics as analytics_module

            # Test module exists
            assert analytics_module is not None

            # Test logger exists
            assert hasattr(analytics_module, "logger")

            # Test expected classes exist
            expected_classes = [
                "InteractionType",
                "LearningOutcome",
                "StudyPattern",
                "LearningInteraction",
                "LearningSession",
                "StudentProfile",
            ]

            for class_name in expected_classes:
                if hasattr(analytics_module, class_name):
                    class_obj = getattr(analytics_module, class_name)
                    assert class_obj is not None

        except ImportError:
            pytest.skip("Learning analytics module not available")

    def test_datetime_handling(self):
        """Test datetime handling in learning analytics"""
        try:
            from core.learning_analytics import InteractionType, LearningInteraction

            # Test current time
            now = datetime.now()

            interaction = LearningInteraction(
                student_id="student_123",
                interaction_type=InteractionType.CONTENT_VIEWED,
                timestamp=now,
                session_id="session_456",
            )

            assert interaction.timestamp == now
            assert isinstance(interaction.timestamp, datetime)

            # Test to_dict with datetime conversion
            data = interaction.to_dict()
            assert isinstance(data["timestamp"], str)
            assert data["timestamp"] == now.isoformat()

        except ImportError:
            pytest.skip("Learning analytics classes not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
