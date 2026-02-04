"""
Working tests for agents with proper mocking
Demonstrates correct testing approach for better coverage
"""
import json
import os
import sys
import uuid
from unittest.mock import AsyncMock, patch

import pytest

# Disable telemetry to speed up tests
os.environ["CHROMADB_TELEMETRY"] = "false"
os.environ["USE_MOCK_RESPONSES"] = "true"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent classes (not instances)
from agents.learning_path_agent import KnowledgeLevel, LearningPathAgent, LearningStyle


class TestLearningPathAgentWorking:
    """Working tests with proper mocking"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_analyze_student_working(self):
        """Test student analysis with proper mocking"""

        # Create agent instance
        agent = LearningPathAgent()

        # Mock the LLM service directly on the agent
        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            # Configure mock response
            mock_llm.generate = AsyncMock(
                return_value={
                    "success": True,
                    "text": json.dumps(
                        {
                            "learning_style": "visual",
                            "knowledge_level": "intermediate",
                            "interests": ["matematik", "fizik"],
                            "goal_summary": "YKS hazırlık",
                        }
                    ),
                }
            )

            # Test data
            student_id = str(uuid.uuid4())
            student_data = {
                "name": "Test Student",
                "grade": "11",
                "exam_target": "YKS",
                "goal": "Math and Physics",
                "available_time": 15,
            }

            # Call method
            profile = await agent.analyze_student(student_id, student_data)

            # Assertions
            assert profile is not None
            assert profile.student_id == student_id
            assert profile.name == "Test Student"
            assert profile.learning_style == LearningStyle.VISUAL
            assert profile.knowledge_level == KnowledgeLevel.INTERMEDIATE
            assert "matematik" in profile.interests

            # Verify mock was called
            mock_llm.generate.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_assess_knowledge_level_working(self):
        """Test knowledge assessment with proper mocking"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value={
                    "success": True,
                    "text": json.dumps(
                        {"level": "intermediate", "reasoning": "Good understanding"}
                    ),
                }
            )

            level = await agent.assess_knowledge_level(
                "student123", "Mathematics", {"correct": 7, "total": 10}
            )

            assert level == KnowledgeLevel.INTERMEDIATE

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_search_resources_working(self):
        """Test resource search with proper mocking"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            with patch("agents.learning_path_agent.rag_service") as mock_rag:
                # Mock LLM response
                mock_llm.generate = AsyncMock(
                    return_value={
                        "success": True,
                        "text": json.dumps(
                            {
                                "resources": [
                                    {
                                        "title": "Calculus Tutorial",
                                        "url": "http://example.com",
                                        "type": "video",
                                        "source": "YouTube",
                                        "difficulty": "intermediate",
                                        "duration": 30,
                                        "description": "Learn calculus",
                                    }
                                ]
                            }
                        ),
                    }
                )

                # Mock RAG search
                mock_rag.search = AsyncMock(return_value=[])

                resources = await agent.search_resources(
                    "Calculus", LearningStyle.VISUAL, KnowledgeLevel.INTERMEDIATE
                )

                assert len(resources) > 0
                assert resources[0].title == "Calculus Tutorial"
                assert resources[0].difficulty_level == KnowledgeLevel.INTERMEDIATE


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_analyze_student_with_invalid_json(self):
        """Test handling of invalid JSON from LLM"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            # Return invalid JSON
            mock_llm.generate = AsyncMock(
                return_value={"success": True, "text": "Not valid JSON"}
            )

            profile = await agent.analyze_student(
                "student123", {"name": "Test", "grade": "10"}
            )

            # Should use default values
            assert profile.learning_style == LearningStyle.MIXED
            assert profile.knowledge_level == KnowledgeLevel.BEGINNER

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_analyze_student_with_llm_error(self):
        """Test handling of LLM errors"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            # Simulate LLM error
            mock_llm.generate = AsyncMock(
                return_value={"success": False, "error": "API Error"}
            )

            profile = await agent.analyze_student("student123", {"name": "Test"})

            # Should still return a profile with defaults
            assert profile is not None
            assert profile.learning_style == LearningStyle.MIXED

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_empty_student_data(self):
        """Test with empty student data"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            mock_llm.generate = AsyncMock(return_value={"success": False})

            profile = await agent.analyze_student("student123", {})

            # Should handle empty data gracefully
            assert profile.name == "Öğrenci"  # Default name
            assert profile.grade == ""


class TestCaching:
    """Test caching mechanisms"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_profile_caching(self):
        """Test that profiles are cached"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value={
                    "success": True,
                    "text": json.dumps(
                        {
                            "learning_style": "visual",
                            "knowledge_level": "beginner",
                            "interests": [],
                            "goal_summary": "Test",
                        }
                    ),
                }
            )

            student_id = str(uuid.uuid4())

            # First call
            profile1 = await agent.analyze_student(student_id, {"name": "Test"})

            # Check cache
            assert student_id in agent.profiles
            assert agent.profiles[student_id] == profile1

            # Mock should be called once
            assert mock_llm.generate.call_count == 1


class TestIntegration:
    """Simple integration tests"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_full_workflow(self):
        """Test complete workflow from profile to path"""

        agent = LearningPathAgent()

        with patch("agents.learning_path_agent.llm_service") as mock_llm:
            with patch("agents.learning_path_agent.rag_service") as mock_rag:
                # Setup mocks for full workflow
                mock_llm.generate = AsyncMock(
                    side_effect=[
                        # Profile analysis response
                        {
                            "success": True,
                            "text": json.dumps(
                                {
                                    "learning_style": "visual",
                                    "knowledge_level": "intermediate",
                                    "interests": ["math"],
                                    "goal_summary": "Learn math",
                                }
                            ),
                        },
                        # Path creation response
                        {
                            "success": True,
                            "text": json.dumps(
                                {
                                    "phases": [
                                        {
                                            "phase": 1,
                                            "name": "Basics",
                                            "duration": 2,
                                            "topics": ["Algebra"],
                                            "resources": [],
                                        }
                                    ],
                                    "reasoning": "Progressive learning",
                                }
                            ),
                        },
                    ]
                )

                mock_rag.search = AsyncMock(return_value=[])

                # Create profile
                student_id = str(uuid.uuid4())
                profile = await agent.analyze_student(
                    student_id, {"name": "Test", "grade": "10", "goal": "Math"}
                )

                assert profile is not None

                # Create learning path
                path = await agent.create_learning_path(profile, "Mathematics", 4)

                assert path is not None
                assert len(path.phases) > 0
                assert path.student_profile == profile


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=agents.learning_path_agent",
            "--cov-report=term-missing",
            "--timeout=30",
        ]
    )
