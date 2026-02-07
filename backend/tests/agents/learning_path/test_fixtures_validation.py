"""
Fixture Validation Tests
Tests to verify that all fixtures work correctly.
"""

import pytest


def test_mock_student_profile_fixture(mock_student_profile):
    """Test that mock_student_profile fixture works"""
    assert mock_student_profile is not None
    assert mock_student_profile["student_id"] == "test-student-001"
    assert mock_student_profile["name"] == "Ahmet Yılmaz"
    assert mock_student_profile["grade"] == "12"
    assert "İstanbul" in mock_student_profile["metadata"]["province"]


def test_create_student_profile_factory():
    """Test create_student_profile factory function"""
    from tests.agents.learning_path.conftest import create_student_profile

    profile = create_student_profile(
        name="Test Öğrenci",
        grade="10",
        learning_style="auditory"
    )

    assert profile["name"] == "Test Öğrenci"
    assert profile["grade"] == "10"
    assert profile["learning_style"] == "auditory"


def test_mock_youtube_resource_fixture(mock_youtube_resource):
    """Test that YouTube resource fixture works"""
    assert mock_youtube_resource is not None
    assert mock_youtube_resource["source"] == "YouTube"
    assert mock_youtube_resource["resource_type"] == "video"
    assert "Türev" in mock_youtube_resource["title"]


def test_create_learning_resource_factory():
    """Test create_learning_resource factory function"""
    from tests.agents.learning_path.conftest import create_learning_resource

    resource = create_learning_resource(
        platform="khan",
        title="Test Kaynağı",
        estimated_time=20
    )

    assert resource["source"] == "Khan Academy"
    assert resource["title"] == "Test Kaynağı"
    assert resource["estimated_time"] == 20


def test_mock_learning_path_fixture(mock_learning_path):
    """Test that learning path fixture works"""
    assert mock_learning_path is not None
    assert mock_learning_path["path_id"] == "path-001"
    assert len(mock_learning_path["resources"]) == 4
    assert len(mock_learning_path["phases"]) == 2


def test_create_learning_path_factory():
    """Test create_learning_path factory function"""
    from tests.agents.learning_path.conftest import create_learning_path

    path = create_learning_path(num_phases=3, resources_per_phase=2)

    assert len(path["phases"]) == 3
    assert len(path["resources"]) == 6  # 3 phases * 2 resources


def test_mock_assessment_fixture(mock_assessment):
    """Test that assessment fixture works"""
    assert mock_assessment is not None
    assert mock_assessment["assessment_id"] == "assessment-001"
    assert len(mock_assessment["questions"]) == 2
    assert "Türev" in mock_assessment["title"]


def test_mock_db_session_fixture(mock_db_session):
    """Test that database session mock works"""
    assert mock_db_session is not None
    assert hasattr(mock_db_session, "add")
    assert hasattr(mock_db_session, "commit")


def test_mock_redis_client_fixture(mock_redis_client):
    """Test that Redis client mock works"""
    assert mock_redis_client is not None
    assert hasattr(mock_redis_client, "get")
    assert hasattr(mock_redis_client, "set")


def test_mock_llm_service_fixture(mock_llm_service):
    """Test that LLM service mock works"""
    assert mock_llm_service is not None
    assert hasattr(mock_llm_service, "generate_text")
    assert hasattr(mock_llm_service, "chat_completion")


def test_turkish_subjects_fixture(turkish_subjects):
    """Test Turkish subjects fixture"""
    assert len(turkish_subjects) > 0
    assert "Matematik" in turkish_subjects
    assert "Türkçe" in turkish_subjects


def test_yks_topics_fixture(yks_topics):
    """Test YKS topics fixture"""
    assert "matematik" in yks_topics
    assert "fizik" in yks_topics
    assert len(yks_topics["matematik"]) > 0


def test_turkish_names_fixture(turkish_names):
    """Test Turkish names fixture"""
    assert len(turkish_names) > 0
    # Check for Turkish characters
    assert any("ı" in name or "İ" in name or "ş" in name for name in turkish_names)


def test_student_profile_obj_fixture(student_profile_obj):
    """Test StudentProfile object fixture"""
    from agents.learning_path.models import StudentProfile, LearningStyle, KnowledgeLevel

    assert isinstance(student_profile_obj, StudentProfile)
    assert student_profile_obj.student_id == "test-student-001"
    assert isinstance(student_profile_obj.learning_style, LearningStyle)
    assert isinstance(student_profile_obj.knowledge_level, KnowledgeLevel)


def test_learning_resource_obj_fixture(learning_resource_obj):
    """Test LearningResource object fixture"""
    from agents.learning_path.models import LearningResource, KnowledgeLevel

    assert isinstance(learning_resource_obj, LearningResource)
    assert learning_resource_obj.source == "YouTube"
    assert isinstance(learning_resource_obj.difficulty_level, KnowledgeLevel)


def test_complete_learning_scenario_fixture(complete_learning_scenario):
    """Test complete learning scenario fixture"""
    assert "student" in complete_learning_scenario
    assert "learning_path" in complete_learning_scenario
    assert "assessment" in complete_learning_scenario
    assert complete_learning_scenario["progress_percentage"] == 0.0
