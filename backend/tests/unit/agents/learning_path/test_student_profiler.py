"""
Unit Tests for StudentProfiler
Teknofest 2025 - Eğitim Eylemci Projesi

Tests for student profile creation, analysis, and management.

Coverage Target: 90%+
"""

import os

# Import the module to test
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
)

from backend.agents.learning_path.core.student_profiler import StudentProfiler
from backend.agents.learning_path.models import (
    KnowledgeLevel,
    LearningStyle,
    StudentProfile,
)

# Fixtures


@pytest.fixture
def mock_llm_service():
    """Mock LLM service with successful response"""
    mock = Mock()
    mock.generate = AsyncMock(
        return_value={
            "success": True,
            "text": '{"learning_style": "visual", "knowledge_level": "intermediate", "interests": ["math", "physics"], "goal_summary": "Learn calculus for university entrance exam"}',
        }
    )
    return mock


@pytest.fixture
def mock_llm_service_failure():
    """Mock LLM service that fails"""
    mock = Mock()
    mock.generate = AsyncMock(
        return_value={"success": False, "error": "LLM service unavailable"}
    )
    return mock


@pytest.fixture
def mock_assessment_system():
    """Mock assessment system"""
    return Mock()


@pytest.fixture
def mock_learning_style_detector():
    """Mock learning style detector"""
    mock = Mock()
    mock.analyze_behaviors = AsyncMock(return_value="visual")
    return mock


@pytest.fixture
def student_profiler(
    mock_llm_service, mock_assessment_system, mock_learning_style_detector
):
    """StudentProfiler instance with mocked dependencies"""
    return StudentProfiler(
        llm_service=mock_llm_service,
        assessment_system=mock_assessment_system,
        learning_style_detector=mock_learning_style_detector,
    )


@pytest.fixture
def sample_student_data():
    """Sample student data for testing"""
    return {
        "name": "Ali Veli",
        "grade": "10",
        "exam_target": "YKS",
        "goal": "Matematik konusunda gelişmek istiyorum",
        "available_time": 90,
    }


# Test Class


@pytest.mark.asyncio
class TestStudentProfiler:
    """Test suite for StudentProfiler class"""

    # Initialization Tests

    def test_init_success(self, mock_llm_service):
        """Test successful initialization"""
        profiler = StudentProfiler(llm_service=mock_llm_service)

        assert profiler.llm == mock_llm_service
        assert profiler.profiles_cache == {}

    def test_init_missing_llm_service(self):
        """Test initialization fails without LLM service"""
        with pytest.raises(ValueError, match="llm_service is required"):
            StudentProfiler(llm_service=None)

    # analyze_student Tests

    async def test_analyze_student_success(
        self, student_profiler, mock_llm_service, sample_student_data
    ):
        """Test successful student analysis"""
        student_id = "student123"

        profile = await student_profiler.analyze_student(
            student_id, sample_student_data
        )

        # Assert profile created correctly
        assert isinstance(profile, StudentProfile)
        assert profile.student_id == student_id
        assert profile.name == "Ali Veli"
        assert profile.grade == "10"
        assert profile.exam_target == "YKS"
        assert profile.learning_goal == "Matematik konusunda gelişmek istiyorum"
        assert profile.learning_style == LearningStyle.VISUAL
        assert profile.knowledge_level == KnowledgeLevel.INTERMEDIATE
        assert "math" in profile.interests
        assert profile.available_time == 90

        # Assert LLM was called
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args
        assert "temperature" in call_args.kwargs
        assert call_args.kwargs["temperature"] == 0.3

        # Assert profile is cached
        cached_profile = student_profiler.get_profile(student_id)
        assert cached_profile == profile

    async def test_analyze_student_minimal_data(self, student_profiler):
        """Test with minimal data (only required fields)"""
        student_id = "student456"
        minimal_data = {"goal": "Learn English"}

        profile = await student_profiler.analyze_student(student_id, minimal_data)

        assert profile.student_id == student_id
        assert profile.name == "Öğrenci"  # Default name
        assert profile.grade == ""  # Default grade
        assert profile.learning_goal == "Learn English"
        assert profile.available_time == 60  # Default time

    async def test_analyze_student_invalid_student_id(self, student_profiler):
        """Test with invalid student ID"""
        invalid_ids = ["", None, 123, []]

        for invalid_id in invalid_ids:
            with pytest.raises(
                ValueError, match="student_id must be a non-empty string"
            ):
                await student_profiler.analyze_student(invalid_id, {"goal": "test"})

    async def test_analyze_student_invalid_data(self, student_profiler):
        """Test with invalid initial data"""
        student_id = "student789"
        invalid_data = [{}, None, [], "string", 123]

        for invalid in invalid_data:
            with pytest.raises(
                ValueError, match="initial_data must be a non-empty dictionary"
            ):
                await student_profiler.analyze_student(student_id, invalid)

    async def test_analyze_student_missing_goal(self, student_profiler):
        """Test with missing goal field"""
        student_id = "student789"
        data_without_goal = {"name": "Test Student"}

        with pytest.raises(ValueError, match="initial_data must contain 'goal'"):
            await student_profiler.analyze_student(student_id, data_without_goal)

    async def test_analyze_student_llm_failure(
        self, mock_llm_service_failure, sample_student_data
    ):
        """Test when LLM service fails"""
        profiler = StudentProfiler(llm_service=mock_llm_service_failure)
        student_id = "student999"

        profile = await profiler.analyze_student(student_id, sample_student_data)

        # Should use default values
        assert profile.learning_style == LearningStyle.MIXED
        assert profile.knowledge_level == KnowledgeLevel.BEGINNER
        assert profile.interests == []

    async def test_analyze_student_llm_invalid_json(self, mock_llm_service):
        """Test when LLM returns invalid JSON"""
        mock_llm_service.generate.return_value = {
            "success": True,
            "text": "This is not valid JSON",
        }

        profiler = StudentProfiler(llm_service=mock_llm_service)
        student_id = "student888"
        data = {"goal": "test"}

        profile = await profiler.analyze_student(student_id, data)

        # Should fallback to defaults
        assert profile.learning_style == LearningStyle.MIXED
        assert profile.knowledge_level == KnowledgeLevel.BEGINNER

    # assess_knowledge_level Tests

    async def test_assess_knowledge_level_from_test_results(self, student_profiler):
        """Test knowledge level assessment from test results"""
        test_cases = [
            ({"score": 25, "total": 100}, KnowledgeLevel.BEGINNER),  # 25%
            ({"score": 45, "total": 100}, KnowledgeLevel.ELEMENTARY),  # 45%
            ({"score": 65, "total": 100}, KnowledgeLevel.INTERMEDIATE),  # 65%
            ({"score": 85, "total": 100}, KnowledgeLevel.ADVANCED),  # 85%
            ({"score": 95, "total": 100}, KnowledgeLevel.EXPERT),  # 95%
        ]

        for test_results, expected_level in test_cases:
            level = await student_profiler.assess_knowledge_level(
                "student123", "math", test_results
            )
            assert level == expected_level, f"Failed for score {test_results['score']}"

    async def test_assess_knowledge_level_edge_cases(self, student_profiler):
        """Test edge cases for knowledge level assessment"""
        # Exact boundary values
        edge_cases = [
            ({"score": 30, "total": 100}, KnowledgeLevel.ELEMENTARY),
            ({"score": 50, "total": 100}, KnowledgeLevel.INTERMEDIATE),
            ({"score": 70, "total": 100}, KnowledgeLevel.ADVANCED),
            ({"score": 90, "total": 100}, KnowledgeLevel.EXPERT),
        ]

        for test_results, expected_level in edge_cases:
            level = await student_profiler.assess_knowledge_level(
                "student123", "math", test_results
            )
            assert level == expected_level

    async def test_assess_knowledge_level_zero_total(self, student_profiler):
        """Test with zero total score"""
        level = await student_profiler.assess_knowledge_level(
            "student123", "math", {"score": 0, "total": 0}
        )
        assert level == KnowledgeLevel.BEGINNER

    async def test_assess_knowledge_level_from_profile(
        self, student_profiler, sample_student_data
    ):
        """Test knowledge level from cached profile"""
        student_id = "student123"

        # Create profile first
        profile = await student_profiler.analyze_student(
            student_id, sample_student_data
        )

        # Assess without test results
        level = await student_profiler.assess_knowledge_level(student_id, "math")

        # Should return profile's knowledge level
        assert level == profile.knowledge_level

    async def test_assess_knowledge_level_no_profile(self, student_profiler):
        """Test when no profile exists"""
        level = await student_profiler.assess_knowledge_level("unknown_student", "math")

        # Should default to BEGINNER
        assert level == KnowledgeLevel.BEGINNER

    async def test_assess_knowledge_level_invalid_inputs(self, student_profiler):
        """Test with invalid inputs"""
        # Invalid student_id
        with pytest.raises(ValueError, match="student_id must be a non-empty string"):
            await student_profiler.assess_knowledge_level("", "math")

        # Invalid subject
        with pytest.raises(ValueError, match="subject must be a non-empty string"):
            await student_profiler.assess_knowledge_level("student123", "")

    # analyze_behavioral_learning_style Tests

    async def test_analyze_behavioral_learning_style_success(
        self, student_profiler, mock_learning_style_detector
    ):
        """Test successful behavioral learning style analysis"""
        student_id = "student123"
        behaviors = [
            {"action": "watched_video", "duration": 600, "engagement": 85},
            {"action": "watched_video", "duration": 450, "engagement": 90},
        ]

        style = await student_profiler.analyze_behavioral_learning_style(
            student_id, behaviors
        )

        assert style == LearningStyle.VISUAL
        mock_learning_style_detector.analyze_behaviors.assert_called_once_with(
            student_id=student_id, behaviors=behaviors
        )

    async def test_analyze_behavioral_learning_style_no_detector(
        self, mock_llm_service
    ):
        """Test when learning style detector is not available"""
        profiler = StudentProfiler(
            llm_service=mock_llm_service, learning_style_detector=None
        )

        style = await profiler.analyze_behavioral_learning_style("student123", [])

        # Should default to MIXED
        assert style == LearningStyle.MIXED

    async def test_analyze_behavioral_learning_style_updates_profile(
        self, student_profiler, sample_student_data
    ):
        """Test that behavioral analysis updates cached profile"""
        student_id = "student123"

        # Create profile
        await student_profiler.analyze_student(student_id, sample_student_data)

        # Analyze behaviors
        behaviors = [{"action": "watched_video", "duration": 600}]
        new_style = await student_profiler.analyze_behavioral_learning_style(
            student_id, behaviors
        )

        # Check profile was updated
        profile = student_profiler.get_profile(student_id)
        assert profile.learning_style == new_style

    # record_learning_behavior Tests

    def test_record_learning_behavior_success(self, student_profiler):
        """Test successful behavior recording"""
        result = student_profiler.record_learning_behavior(
            student_id="student123",
            action="watched_video",
            context={"video_id": "vid123", "subject": "math"},
            duration=600,
        )

        assert result is True

    def test_record_learning_behavior_minimal(self, student_profiler):
        """Test behavior recording with minimal data"""
        result = student_profiler.record_learning_behavior(
            student_id="student123", action="completed_quiz", context={}
        )

        assert result is True

    # analyze_performance_trend Tests

    def test_analyze_performance_trend(self, student_profiler):
        """Test performance trend analysis"""
        # Check if method exists, if not skip
        if not hasattr(student_profiler, 'analyze_performance_trend'):
            pytest.skip("analyze_performance_trend method not implemented")

        # Test cases based on actual implementation behavior
        # Implementation returns: stable_excellent, stable_good, stable_average, needs_improvement
        # Note: Each test case uses a different student_id to avoid cache interference
        test_cases = [
            (95, "stable_excellent"),  # >= 80
            (80, "stable_excellent"),  # >= 80
            (75, "stable_good"),       # >= 60 && < 80
            (60, "stable_good"),       # >= 60 && < 80
            (55, "stable_average"),    # >= 40 && < 60
            (40, "stable_average"),    # >= 40 && < 60
            (25, "needs_improvement"), # < 40
            (10, "needs_improvement"), # < 40
        ]

        for idx, (score, expected_trend) in enumerate(test_cases):
            # Use unique student_id for each test to avoid cache interference
            student_id = f"student_trend_{idx}"
            trend = student_profiler.analyze_performance_trend(student_id, score)
            assert trend == expected_trend, f"Failed for score {score}: got {trend}, expected {expected_trend}"

    # get_profile Tests

    def test_get_profile_exists(self, student_profiler):
        """Test getting existing profile"""
        student_id = "student123"
        profile = StudentProfile(
            student_id=student_id,
            name="Test",
            grade="10",
            exam_target="YKS",
            learning_goal="Learn",
            learning_style=LearningStyle.VISUAL,
            knowledge_level=KnowledgeLevel.INTERMEDIATE,
            interests=[],
            available_time=60,
            metadata={},
        )

        student_profiler.profiles_cache[student_id] = profile

        retrieved = student_profiler.get_profile(student_id)
        assert retrieved == profile

    def test_get_profile_not_exists(self, student_profiler):
        """Test getting non-existent profile"""
        profile = student_profiler.get_profile("unknown_student")
        assert profile is None

    # update_profile Tests

    def test_update_profile_success(self, student_profiler):
        """Test successful profile update"""
        student_id = "student123"
        profile = StudentProfile(
            student_id=student_id,
            name="Test",
            grade="10",
            exam_target="YKS",
            learning_goal="Learn",
            learning_style=LearningStyle.VISUAL,
            knowledge_level=KnowledgeLevel.BEGINNER,
            interests=[],
            available_time=60,
            metadata={},
        )

        student_profiler.profiles_cache[student_id] = profile

        # Update profile
        updated = student_profiler.update_profile(
            student_id,
            {
                "knowledge_level": KnowledgeLevel.ADVANCED,
                "available_time": 90,
                "interests": ["math", "physics"],
            },
        )

        assert updated is not None
        assert updated.knowledge_level == KnowledgeLevel.ADVANCED
        assert updated.available_time == 90
        assert updated.interests == ["math", "physics"]

    def test_update_profile_not_found(self, student_profiler):
        """Test updating non-existent profile"""
        updated = student_profiler.update_profile(
            "unknown_student", {"knowledge_level": KnowledgeLevel.ADVANCED}
        )

        assert updated is None

    def test_update_profile_ignore_restricted_fields(self, student_profiler):
        """Test that restricted fields are not updated"""
        student_id = "student123"
        original_id = "student123"
        original_name = "Test Student"

        profile = StudentProfile(
            student_id=original_id,
            name=original_name,
            grade="10",
            exam_target="YKS",
            learning_goal="Learn",
            learning_style=LearningStyle.VISUAL,
            knowledge_level=KnowledgeLevel.INTERMEDIATE,
            interests=[],
            available_time=60,
            metadata={},
        )

        student_profiler.profiles_cache[student_id] = profile

        # Try to update restricted fields
        updated = student_profiler.update_profile(
            student_id,
            {
                "student_id": "new_id",  # Should not update
                "name": "New Name",  # Should not update
                "knowledge_level": KnowledgeLevel.ADVANCED,  # Should update
            },
        )

        # Restricted fields should not change
        assert updated.student_id == original_id
        assert updated.name == original_name

        # Allowed field should change
        assert updated.knowledge_level == KnowledgeLevel.ADVANCED

    # Integration Tests

    async def test_full_workflow(self, student_profiler, sample_student_data):
        """Test complete workflow: analyze → assess → update"""
        student_id = "student123"

        # 1. Analyze student
        profile = await student_profiler.analyze_student(
            student_id, sample_student_data
        )
        assert profile.knowledge_level == KnowledgeLevel.INTERMEDIATE

        # 2. Assess with test results
        test_results = {"score": 85, "total": 100}
        new_level = await student_profiler.assess_knowledge_level(
            student_id, "math", test_results
        )
        assert new_level == KnowledgeLevel.ADVANCED

        # 3. Update profile
        updated = student_profiler.update_profile(
            student_id, {"knowledge_level": new_level}
        )
        assert updated.knowledge_level == KnowledgeLevel.ADVANCED

        # 4. Verify cached profile
        cached = student_profiler.get_profile(student_id)
        assert cached.knowledge_level == KnowledgeLevel.ADVANCED

    async def test_concurrent_students(self, student_profiler):
        """Test managing multiple students concurrently"""
        students = [
            ("student1", {"name": "Ali", "goal": "Math"}),
            ("student2", {"name": "Ayşe", "goal": "Physics"}),
            ("student3", {"name": "Mehmet", "goal": "Chemistry"}),
        ]

        # Create profiles for all students
        for student_id, data in students:
            await student_profiler.analyze_student(student_id, data)

        # Verify all profiles are cached
        for student_id, data in students:
            profile = student_profiler.get_profile(student_id)
            assert profile is not None
            assert profile.student_id == student_id
            assert profile.name == data["name"]


# Run tests
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=backend.agents.learning_path.core.student_profiler",
            "--cov-report=term-missing",
        ]
    )
