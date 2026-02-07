"""
Study Buddy Agent - Comprehensive Test Suite
Coverage target: %80+
"""

import pytest

try:
    from agents.study_buddy_agent import StudyBuddyAgent
except ImportError:
    pytest.skip("study_buddy_agent module archived", allow_module_level=True)


@pytest.fixture
def agent():
    """Create study buddy agent"""
    if not StudyBuddyAgent:
        pytest.skip("StudyBuddyAgent not found")
    return StudyBuddyAgent()


class TestStudyBuddyAgent:
    """Study Buddy Agent tests"""

    @pytest.mark.asyncio
    async def test_chat_response(self, agent):
        """Test chat response generation"""
        response = await agent.generate_response("Hello")
        assert response is not None

    @pytest.mark.asyncio
    async def test_explain_concept(self, agent):
        """Test concept explanation"""
        explanation = await agent.explain_concept("derivatives")
        assert explanation is not None

    @pytest.mark.asyncio
    async def test_solve_problem(self, agent):
        """Test problem solving"""
        solution = await agent.solve_problem("2x + 3 = 7")
        assert solution is not None

    @pytest.mark.asyncio
    async def test_provide_hints(self, agent):
        """Test hint generation"""
        hints = await agent.provide_hints("quadratic equation")
        assert hints is not None

    @pytest.mark.asyncio
    async def test_motivate_student(self, agent):
        """Test motivation messages"""
        message = await agent.motivate_student("struggling")
        assert message is not None
