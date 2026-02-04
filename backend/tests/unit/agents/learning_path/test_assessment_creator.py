"""
Unit Tests for AssessmentCreator
Teknofest 2025 - Eğitim Eylemci Projesi

Tests for assessment creation and analysis.
Coverage Target: 90%+
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
)

from backend.agents.learning_path.core.assessment_creator import AssessmentCreator
from backend.agents.learning_path.models import (
    StudentProfile,
    LearningStyle,
    KnowledgeLevel,
)


@pytest.fixture
def mock_assessment_system():
    """Mock assessment system"""
    mock = Mock()
    mock.generate_quick_test = AsyncMock(
        return_value=[
            Mock(
                question_id="q1",
                question_text="Test question?",
                question_type=Mock(value="multiple_choice"),
                subject="Math",
                topic="Algebra",
                difficulty=Mock(value="medium"),
                options=["A", "B", "C", "D"],
                time_limit_seconds=120,
                points=1,
                explanation="Explanation",
                metadata={},
            )
        ]
    )
    mock.create_self_assessment = AsyncMock(return_value=[Mock(question_id="q1")])
    mock.generate_interactive_questionnaire = AsyncMock(
        return_value=[Mock(question_id="q1", time_limit_seconds=120)]
    )
    mock.create_guided_self_assessment_flow = AsyncMock(return_value={"total_steps": 3})
    return mock


@pytest.fixture
def mock_profiler():
    """Mock student profiler"""
    mock = Mock()
    profile = StudentProfile(
        student_id="student123",
        name="Test",
        grade="10",
        exam_target="YKS",
        learning_goal="Learn math",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["math"],
        available_time=60,
        metadata={},
    )
    mock.get_profile = Mock(return_value=profile)
    return mock


@pytest.fixture
def assessment_creator(mock_assessment_system, mock_profiler):
    """AssessmentCreator instance"""
    return AssessmentCreator(
        assessment_system=mock_assessment_system, student_profiler=mock_profiler
    )


@pytest.mark.asyncio
class TestAssessmentCreator:
    """Test suite for AssessmentCreator"""

    def test_init_success(self, mock_assessment_system):
        """Test successful initialization"""
        creator = AssessmentCreator(assessment_system=mock_assessment_system)
        assert creator.assessment == mock_assessment_system

    def test_init_missing_assessment_system(self):
        """Test initialization fails without assessment system"""
        with pytest.raises(ValueError, match="assessment_system is required"):
            AssessmentCreator(assessment_system=None)

    async def test_create_quick_assessment_success(
        self, assessment_creator, mock_assessment_system
    ):
        """Test successful quick assessment creation"""
        result = await assessment_creator.create_quick_assessment(
            "student123", "Matematik", "Türev", question_count=5
        )

        assert result["student_id"] == "student123"
        assert result["subject"] == "Matematik"
        assert result["topic"] == "Türev"
        assert result["assessment_type"] == "quick_test"
        assert len(result["questions"]) > 0

        mock_assessment_system.generate_quick_test.assert_called_once()

    async def test_create_quick_assessment_invalid_inputs(self, assessment_creator):
        """Test with invalid inputs"""
        with pytest.raises(ValueError):
            await assessment_creator.create_quick_assessment("", "Math")

        with pytest.raises(ValueError):
            await assessment_creator.create_quick_assessment("student123", "")

        with pytest.raises(ValueError):
            await assessment_creator.create_quick_assessment(
                "student123", "Math", question_count=0
            )

        with pytest.raises(ValueError):
            await assessment_creator.create_quick_assessment(
                "student123", "Math", question_count=25
            )

    async def test_create_self_assessment_success(
        self, assessment_creator, mock_assessment_system
    ):
        """Test successful self-assessment creation"""
        result = await assessment_creator.create_self_assessment(
            "student123", ["Matematik", "Fizik"]
        )

        assert result["assessment_type"] == "self_assessment"
        assert result["subjects"] == ["Matematik", "Fizik"]

        mock_assessment_system.create_self_assessment.assert_called_once()

    async def test_create_interactive_questionnaire_success(
        self, assessment_creator, mock_assessment_system
    ):
        """Test successful interactive questionnaire creation"""
        result = await assessment_creator.create_interactive_questionnaire(
            "student123", "YKS Matematik hazırlığı"
        )

        assert result["assessment_type"] == "interactive_questionnaire"
        assert result["goal"] == "YKS Matematik hazırlığı"

        mock_assessment_system.generate_interactive_questionnaire.assert_called_once()

    async def test_create_guided_self_assessment_success(
        self, assessment_creator, mock_assessment_system
    ):
        """Test guided self-assessment creation"""
        result = await assessment_creator.create_guided_self_assessment(
            "student123", ["Math"], ["Goal 1"]
        )

        assert result["total_steps"] == 3
        mock_assessment_system.create_guided_self_assessment_flow.assert_called_once()

    async def test_create_learning_style_questionnaire(self, assessment_creator):
        """Test learning style questionnaire creation"""
        result = await assessment_creator.create_learning_style_questionnaire(
            "student123"
        )

        assert result["assessment_type"] == "learning_style_questionnaire"
        assert len(result["questions"]) == 3

    def test_analyze_learning_style_responses_visual(self, assessment_creator):
        """Test visual learning style detection"""
        responses = {
            "style_q1": 0,  # Visual
            "style_q2": 0,  # Visual
            "style_q3": 0,  # Visual
        }

        result = assessment_creator.analyze_learning_style_responses(
            "student123", responses
        )

        assert result["detected_style"] == "visual"
        assert result["style_counts"]["visual"] == 3
        assert result["confidence"] == 1.0

    def test_analyze_learning_style_responses_mixed(self, assessment_creator):
        """Test mixed learning style detection"""
        responses = {
            "style_q1": 0,  # Visual
            "style_q2": 1,  # Auditory
            "style_q3": 2,  # Reading
        }

        result = assessment_creator.analyze_learning_style_responses(
            "student123", responses
        )

        assert result["detected_style"] == "mixed"
        assert result["is_mixed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
