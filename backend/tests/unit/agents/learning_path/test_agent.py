"""
Unit Tests for Learning Path Agent Main Orchestrator
Teknofest 2025 - Eğitim Eylemci Projesi

Tests the main LearningPathAgent orchestrator that coordinates all components.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.agents.learning_path.agent import LearningPathAgent
from backend.agents.learning_path.models import (
    KnowledgeLevel,
    LearningPath,
    LearningPhase,
    LearningResource,
    LearningStyle,
    StudentProfile,
)

# Fixtures


@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    mock = Mock()
    mock.generate = AsyncMock(
        return_value={
            "success": True,
            "text": '{"learning_style": "visual", "knowledge_level": "intermediate"}',
        }
    )
    return mock


@pytest.fixture
def mock_assessment_system():
    """Mock assessment system"""
    mock = Mock()
    mock.generate_diagnostic_test = AsyncMock(
        return_value={
            "success": True,
            "questions": [{"id": "q1", "text": "Test question"}],
        }
    )
    mock.generate_quick_test = AsyncMock(
        return_value={
            "success": True,
            "questions": [{"id": "q1", "text": "Quick question"}],
        }
    )
    return mock


@pytest.fixture
def mock_youtube_service():
    """Mock YouTube service"""
    mock = Mock()
    mock.search = AsyncMock(
        return_value=[
            {
                "title": "Matematik Video 1",
                "url": "https://youtube.com/watch?v=test1",
                "duration": "PT10M",
                "subjects": ["Matematik"],
            }
        ]
    )
    return mock


@pytest.fixture
def learning_path_agent(mock_llm_service, mock_assessment_system, mock_youtube_service):
    """Create LearningPathAgent instance with mocked dependencies"""
    agent = LearningPathAgent(
        llm_service=mock_llm_service,
        assessment_system=mock_assessment_system,
        youtube_service=mock_youtube_service,
    )
    return agent


@pytest.fixture
def sample_student_data():
    """Sample student data for testing"""
    return {
        "name": "Ahmet Yılmaz",
        "grade": "12",
        "exam_target": "YKS",
        "learning_goal": "Matematik TYT hazırlık",
        "subjects": ["Matematik", "Fizik"],
        "interests": ["Matematik", "Bilim"],
    }


@pytest.fixture
def sample_student_profile():
    """Sample StudentProfile object"""
    return StudentProfile(
        student_id="student123",
        name="Ahmet Yılmaz",
        grade="12",
        exam_target="YKS",
        learning_goal="Matematik TYT hazırlık",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["Matematik", "Bilim"],
        available_time=20,
    )


@pytest.fixture
def sample_resources():
    """Sample learning resources"""
    return [
        LearningResource(
            resource_id="res1",
            title="Video 1",
            source="youtube",
            url="https://youtube.com/watch?v=1",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=10,
            language="tr",
            description="Matematik video",
            tags=["Matematik", "visual"],
            metadata={},  # Initialize metadata to prevent NoneType errors
        ),
        LearningResource(
            resource_id="res2",
            title="Video 2",
            source="youtube",
            url="https://youtube.com/watch?v=2",
            resource_type="video",
            difficulty_level=KnowledgeLevel.INTERMEDIATE,
            estimated_time=15,
            language="tr",
            description="Matematik video 2",
            tags=["Matematik", "visual", "auditory"],
            metadata={},  # Initialize metadata to prevent NoneType errors
        ),
    ]


@pytest.fixture
def sample_learning_path(sample_resources):
    """Sample learning path"""
    phase = LearningPhase(
        phase_id="phase1",
        name="Temel Kavramlar",
        description="Temel matematik kavramları",
        order=1,
        resources=sample_resources,
        learning_objectives=["Temel kavramları öğren"],
    )

    return LearningPath(
        path_id="path123",
        student_id="student123",
        goal="Matematik TYT hazırlık",
        resources=sample_resources,
        phases=[phase],
        created_at=datetime.now(),
        reasoning="Kişiselleştirilmiş yol",
    )


# Initialization Tests


def test_agent_initialization_success(mock_llm_service, mock_assessment_system):
    """Test successful agent initialization"""
    agent = LearningPathAgent(
        llm_service=mock_llm_service, assessment_system=mock_assessment_system
    )

    assert agent is not None
    assert agent.llm == mock_llm_service
    assert agent.assessment_system == mock_assessment_system
    assert agent.student_profiler is not None
    assert agent.assessment_creator is not None
    assert agent.resource_finder is not None
    assert agent.path_generator is not None
    assert agent.path_optimizer is not None


def test_agent_initialization_missing_llm():
    """Test agent initialization fails without LLM service"""
    with pytest.raises(ValueError, match="llm_service is required"):
        LearningPathAgent(llm_service=None, assessment_system=Mock())


def test_agent_initialization_missing_assessment():
    """Test agent initialization fails without assessment system"""
    with pytest.raises(ValueError, match="assessment_system is required"):
        LearningPathAgent(llm_service=Mock(), assessment_system=None)


def test_agent_initialization_with_all_services(
    mock_llm_service, mock_assessment_system, mock_youtube_service
):
    """Test agent initialization with all optional services"""
    khan_service = Mock()
    oer_service = Mock()
    chat_service = Mock()

    agent = LearningPathAgent(
        llm_service=mock_llm_service,
        assessment_system=mock_assessment_system,
        youtube_service=mock_youtube_service,
        khan_service=khan_service,
        oer_service=oer_service,
        chat_service=chat_service,
    )

    assert agent.youtube_integration is not None
    assert agent.khan_integration is not None
    assert agent.oer_integration is not None
    assert agent.chat_integration is not None


# Main Workflow Tests


@pytest.mark.asyncio
async def test_create_learning_path_success(learning_path_agent, sample_student_data):
    """Test successful learning path creation"""
    # Mock the profiler's analyze_student
    mock_profile = StudentProfile(
        student_id="student123",
        name="Ahmet Yılmaz",
        grade="12",
        exam_target="YKS",
        learning_goal="Matematik TYT hazırlık",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["Matematik"],
        available_time=20,
    )

    with patch.object(
        learning_path_agent.student_profiler,
        "analyze_student",
        new=AsyncMock(return_value=mock_profile),
    ), patch.object(
        learning_path_agent.assessment_creator,
        "create_diagnostic_assessment",
        new=AsyncMock(return_value={"success": True, "questions": []}),
    ), patch.object(
        learning_path_agent,
        "_search_personalized_resources",
        new=AsyncMock(return_value=[]),
    ), patch.object(
        learning_path_agent.path_generator,
        "generate_path",
        new=AsyncMock(
            return_value=LearningPath(
                path_id="path123",
                student_id="student123",
                goal="Test goal",
                resources=[],
                phases=[],
                created_at=datetime.now(),
                reasoning="Test reasoning",
            )
        ),
    ):
        result = await learning_path_agent.create_learning_path(
            student_id="student123", student_data=sample_student_data
        )

        assert result["success"] is True
        assert "student_profile" in result
        assert "learning_path" in result
        assert "assessment" in result
        assert result["student_profile"]["student_id"] == "student123"


@pytest.mark.asyncio
async def test_create_learning_path_with_goal(learning_path_agent, sample_student_data):
    """Test learning path creation with explicit goal"""
    mock_profile = StudentProfile(
        student_id="student123",
        name="Ahmet",
        grade="12",
        exam_target="YKS",
        learning_goal="Custom goal",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=[],
        available_time=20,
    )

    with patch.object(
        learning_path_agent.student_profiler,
        "analyze_student",
        new=AsyncMock(return_value=mock_profile),
    ), patch.object(
        learning_path_agent.assessment_creator,
        "create_diagnostic_assessment",
        new=AsyncMock(return_value={"success": True, "questions": []}),
    ), patch.object(
        learning_path_agent,
        "_search_personalized_resources",
        new=AsyncMock(return_value=[]),
    ), patch.object(
        learning_path_agent.path_generator,
        "generate_path",
        new=AsyncMock(
            return_value=LearningPath(
                path_id="path123",
                student_id="student123",
                goal="Custom goal",
                resources=[],
                phases=[],
                created_at=datetime.now(),
                reasoning="Test",
            )
        ),
    ):
        result = await learning_path_agent.create_learning_path(
            student_id="student123",
            student_data=sample_student_data,
            goal="Custom goal",
        )

        assert result["success"] is True
        assert result["learning_path"]["goal"] == "Custom goal"


@pytest.mark.asyncio
async def test_create_learning_path_error_handling(
    learning_path_agent, sample_student_data
):
    """Test error handling in learning path creation"""
    with patch.object(
        learning_path_agent.student_profiler,
        "analyze_student",
        new=AsyncMock(side_effect=Exception("Profile error")),
    ):
        result = await learning_path_agent.create_learning_path(
            student_id="student123", student_data=sample_student_data
        )

        assert result["success"] is False
        assert "error" in result
        assert "Profile error" in result["error"]


# Progress Update Tests


@pytest.mark.asyncio
async def test_update_path_progress_success(learning_path_agent, sample_learning_path):
    """Test successful progress update"""
    # Cache a learning path
    learning_path_agent.paths_cache["student123"] = sample_learning_path

    # Cache a profile
    profile = StudentProfile(
        student_id="student123",
        name="Test",
        grade="12",
        exam_target="YKS",
        learning_goal="Test",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=[],
        available_time=20,
    )
    learning_path_agent.student_profiler.profiles_cache["student123"] = profile

    result = await learning_path_agent.update_path_progress(
        student_id="student123",
        completed_resource_ids=["res1"],
        performance_data={"avg_score": 85, "consistency": 0.8},
    )

    assert result["success"] is True
    assert result["progress_percent"] > 0
    assert result["completed_resources"] == 1


@pytest.mark.asyncio
async def test_update_path_progress_no_path(learning_path_agent):
    """Test progress update with no cached path"""
    result = await learning_path_agent.update_path_progress(
        student_id="nonexistent", completed_resource_ids=[]
    )

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_update_path_progress_difficulty_adaptation(
    learning_path_agent, sample_learning_path
):
    """Test difficulty adaptation during progress update"""
    # Cache path and profile
    learning_path_agent.paths_cache["student123"] = sample_learning_path

    profile = StudentProfile(
        student_id="student123",
        name="Test",
        grade="12",
        exam_target="YKS",
        learning_goal="Test",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=[],
        available_time=20,
    )
    learning_path_agent.student_profiler.profiles_cache["student123"] = profile

    # High performance should increase difficulty
    result = await learning_path_agent.update_path_progress(
        student_id="student123",
        completed_resource_ids=["res1"],
        performance_data={"avg_score": 90, "consistency": 0.9},
    )

    assert result["success"] is True


# Recommendations Tests


@pytest.mark.asyncio
async def test_get_next_recommendations_success(
    learning_path_agent, sample_learning_path
):
    """Test getting next recommendations"""
    learning_path_agent.paths_cache["student123"] = sample_learning_path

    result = await learning_path_agent.get_next_recommendations(
        student_id="student123", count=5
    )

    assert result["success"] is True
    assert "recommendations" in result
    assert len(result["recommendations"]) <= 5


@pytest.mark.asyncio
async def test_get_next_recommendations_no_path(learning_path_agent):
    """Test recommendations with no cached path"""
    result = await learning_path_agent.get_next_recommendations(
        student_id="nonexistent"
    )

    assert result["success"] is False


# Quick Assessment Tests


@pytest.mark.asyncio
async def test_create_quick_assessment_success(learning_path_agent):
    """Test quick assessment creation"""
    with patch.object(
        learning_path_agent.assessment_creator,
        "create_quick_assessment",
        new=AsyncMock(return_value={"success": True, "questions": []}),
    ):
        result = await learning_path_agent.create_quick_assessment(
            student_id="student123",
            subject="Matematik",
            topic="Cebir",
            question_count=5,
        )

        assert result["success"] is True


@pytest.mark.asyncio
async def test_create_quick_assessment_error(learning_path_agent):
    """Test quick assessment error handling"""
    with patch.object(
        learning_path_agent.assessment_creator,
        "create_quick_assessment",
        new=AsyncMock(side_effect=Exception("Assessment error")),
    ):
        result = await learning_path_agent.create_quick_assessment(
            student_id="student123", subject="Matematik"
        )

        assert result["success"] is False
        assert "error" in result


# Video Search Tests


@pytest.mark.asyncio
async def test_search_videos_success(learning_path_agent):
    """Test YouTube video search"""
    result = await learning_path_agent.search_videos(
        query="Matematik dersi", max_results=5
    )

    assert result["success"] is True
    assert "videos" in result


@pytest.mark.asyncio
async def test_search_videos_no_service(mock_llm_service, mock_assessment_system):
    """Test video search without YouTube service"""
    agent = LearningPathAgent(
        llm_service=mock_llm_service, assessment_system=mock_assessment_system
    )

    result = await agent.search_videos(query="Test")

    assert result["success"] is False
    assert "not configured" in result["error"]


# Chat Tests


@pytest.mark.asyncio
async def test_chat_with_student_success(learning_path_agent):
    """Test chat functionality"""
    result = await learning_path_agent.chat_with_student(
        session_id="session123", message="Matematik konusunda yardım"
    )

    assert result["success"] is True
    assert "response" in result or "text" in result


# Path Regeneration Tests


@pytest.mark.asyncio
async def test_regenerate_path_success(learning_path_agent, sample_student_profile):
    """Test path regeneration with new preferences"""
    # Cache profile
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile

    with patch.object(
        learning_path_agent,
        "_search_personalized_resources",
        new=AsyncMock(return_value=[]),
    ), patch.object(
        learning_path_agent.path_generator,
        "generate_path",
        new=AsyncMock(
            return_value=LearningPath(
                path_id="path_new",
                student_id="student123",
                goal="New goal",
                resources=[],
                phases=[],
                created_at=datetime.now(),
                reasoning="Regenerated",
            )
        ),
    ):
        result = await learning_path_agent.regenerate_path(
            student_id="student123", preferences={"difficulty": "advanced"}
        )

        assert result["success"] is True
        assert "learning_path" in result


@pytest.mark.asyncio
async def test_regenerate_path_no_profile(learning_path_agent):
    """Test path regeneration without profile"""
    result = await learning_path_agent.regenerate_path(student_id="nonexistent")

    assert result["success"] is False


# Learning Gaps Analysis Tests


@pytest.mark.asyncio
async def test_analyze_learning_gaps_success(
    learning_path_agent, sample_student_profile
):
    """Test learning gaps analysis"""
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile

    assessment_results = {
        "topic_scores": {"Cebir": 45, "Geometri": 85, "Trigonometri": 50}
    }

    with patch.object(
        learning_path_agent.resource_finder,
        "search_resources",
        new=AsyncMock(return_value=[]),
    ):
        result = await learning_path_agent.analyze_learning_gaps(
            student_id="student123", assessment_results=assessment_results
        )

        assert result["success"] is True
        assert "weak_topics" in result
        assert len(result["weak_topics"]) == 2  # Cebir and Trigonometri


# Statistics and Cache Tests


def test_get_agent_stats(
    learning_path_agent, sample_student_profile, sample_learning_path
):
    """Test agent statistics"""
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile
    learning_path_agent.paths_cache["student123"] = sample_learning_path

    stats = learning_path_agent.get_agent_stats()

    assert stats["version"] == "2.0.0"
    assert stats["cached_profiles"] == 1
    assert stats["cached_paths"] == 1
    assert "integrations" in stats
    assert "components" in stats


def test_clear_cache_specific_student(learning_path_agent, sample_student_profile):
    """Test clearing cache for specific student"""
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile

    learning_path_agent.clear_cache(student_id="student123")

    assert "student123" not in learning_path_agent.student_profiler.profiles_cache


def test_clear_cache_all(learning_path_agent, sample_student_profile):
    """Test clearing all caches"""
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile

    learning_path_agent.clear_cache()

    assert len(learning_path_agent.student_profiler.profiles_cache) == 0
    assert len(learning_path_agent.paths_cache) == 0


# Profile and Path Retrieval Tests


def test_get_student_profile(learning_path_agent, sample_student_profile):
    """Test getting cached student profile"""
    learning_path_agent.student_profiler.profiles_cache[
        "student123"
    ] = sample_student_profile

    profile = learning_path_agent.get_student_profile("student123")

    assert profile is not None
    assert profile.student_id == "student123"


def test_get_student_profile_not_found(learning_path_agent):
    """Test getting non-existent profile"""
    profile = learning_path_agent.get_student_profile("nonexistent")

    assert profile is None


def test_get_learning_path(learning_path_agent, sample_learning_path):
    """Test getting cached learning path"""
    learning_path_agent.paths_cache["student123"] = sample_learning_path

    path = learning_path_agent.get_learning_path("student123")

    assert path is not None
    assert path.path_id == "path123"


def test_get_learning_path_not_found(learning_path_agent):
    """Test getting non-existent path"""
    path = learning_path_agent.get_learning_path("nonexistent")

    assert path is None
