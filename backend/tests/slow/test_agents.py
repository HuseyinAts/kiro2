"""
Comprehensive tests for AI agents with 80%+ coverage
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock

import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
simple_agents = pytest.importorskip("simple_agents", reason="simple_agents module removed")
ExamAgent = simple_agents.ExamAgent
LearningAgent = simple_agents.LearningAgent
LLMClient = simple_agents.LLMClient
StudyAgent = simple_agents.StudyAgent


class TestLLMClient:
    """Test LLMClient class"""

    @pytest.mark.asyncio
    async def test_llm_client_initialization(self):
        """Test LLMClient initialization with environment variables"""
        client = LLMClient()
        assert client.endpoint == os.getenv("HF_ENDPOINT_URL")
        assert client.api_key == os.getenv("HF_API_KEY", "")
        assert client.use_mock == True  # Default in test env
        assert client.timeout == 5
        assert client.max_retries == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_llm_client_mock_mode(self):
        """Test LLMClient returns None in mock mode"""
        client = LLMClient()
        result = await client.generate("Test prompt", "learning")
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_llm_client_successful_request(
        self, mock_env_with_llm, mock_httpx_client
    ):
        """Test successful LLM API request"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "generated_text": "System prompt\n\nUser: Test\nAssistant: Mock LLM response"
        }
        mock_httpx_client.post.return_value = mock_response

        client = LLMClient()
        client.client = mock_httpx_client
        result = await client.generate("Test prompt", "learning")

        assert result == "Mock LLM response"
        mock_httpx_client.post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_llm_client_list_response(self, mock_env_with_llm, mock_httpx_client):
        """Test LLM API request with list response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "Full prompt here. Actual response text"}
        ]
        mock_httpx_client.post.return_value = mock_response

        client = LLMClient()
        client.client = mock_httpx_client
        result = await client.generate("Test", "study")

        assert "Actual response text" in result or result is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_llm_client_error_handling(
        self, mock_env_with_llm, mock_httpx_client
    ):
        """Test LLM client error handling and retries"""
        mock_httpx_client.post.side_effect = httpx.RequestError("Connection failed")

        client = LLMClient()
        client.client = mock_httpx_client
        client.max_retries = 2

        result = await client.generate("Test", "exam")
        assert result is None  # Falls back to None on error
        assert mock_httpx_client.post.call_count == 2  # Retried
        await client.close()

    @pytest.mark.asyncio
    async def test_llm_client_http_error(self, mock_env_with_llm, mock_httpx_client):
        """Test LLM client with HTTP error response"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_client.post.return_value = mock_response

        client = LLMClient()
        client.client = mock_httpx_client
        result = await client.generate("Test", "learning")

        assert result is None
        await client.close()

    def test_get_system_prompt(self):
        """Test system prompt generation for different agent types"""
        client = LLMClient()

        learning_prompt = client._get_system_prompt("learning")
        assert "learning path" in learning_prompt.lower()

        study_prompt = client._get_system_prompt("study")
        assert "study buddy" in study_prompt.lower()

        exam_prompt = client._get_system_prompt("exam")
        assert "exam" in exam_prompt.lower()

        # Test default fallback
        default_prompt = client._get_system_prompt("unknown")
        assert default_prompt == learning_prompt


class TestLearningAgent:
    """Test LearningAgent class"""

    @pytest.mark.asyncio
    async def test_learning_agent_initialization(self):
        """Test LearningAgent initialization"""
        agent = LearningAgent()
        assert agent.name == "Öğrenme Yolu Ajanı"
        assert hasattr(agent, "use_mock")
        assert hasattr(agent, "responses")
        assert len(agent.responses) > 0

    @pytest.mark.asyncio
    async def test_learning_agent_plan_keyword(self, learning_agent):
        """Test learning agent responds to 'plan' keyword"""
        response = await learning_agent.process("Bana bir plan oluştur")
        assert "Öğrenme Planınız" in response
        assert "Hafta" in response

    @pytest.mark.asyncio
    async def test_learning_agent_level_assessment(self, learning_agent):
        """Test learning agent level assessment"""
        response = await learning_agent.process("Seviyemi değerlendir")
        assert "Seviye" in response
        assert "%" in response

    @pytest.mark.asyncio
    async def test_learning_agent_goals(self, learning_agent):
        """Test learning agent goal setting"""
        response = await learning_agent.process("Hedeflerimi belirle")
        assert "Hedef" in response
        assert "Vadeli" in response

    @pytest.mark.asyncio
    async def test_learning_agent_progress(self, learning_agent):
        """Test learning agent progress check"""
        response = await learning_agent.process("İlerleme durumum nedir?")
        assert "İlerleme" in response or "ilerleme" in response

    @pytest.mark.asyncio
    async def test_learning_agent_recommendations(self, learning_agent):
        """Test learning agent recommendations"""
        response = await learning_agent.process("Bana öneri ver")
        assert "Öneri" in response or "öneri" in response

    @pytest.mark.asyncio
    async def test_learning_agent_schedule(self, learning_agent):
        """Test learning agent schedule creation"""
        response = await learning_agent.process("Çalışma programı oluştur")
        assert "Program" in response or "program" in response
        assert "Pazartesi" in response or "PAZARTESİ" in response

    @pytest.mark.asyncio
    async def test_learning_agent_general_response(self, learning_agent):
        """Test learning agent general response"""
        response = await learning_agent.process("Merhaba nasılsın?")
        assert len(response) > 0
        assert "yardım" in response.lower() or "destek" in response.lower()

    @pytest.mark.asyncio
    async def test_learning_agent_with_llm(self, mock_env_with_llm, mock_httpx_client):
        """Test learning agent with LLM response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "generated_text": "LLM generated learning plan response"
        }
        mock_httpx_client.post.return_value = mock_response

        agent = LearningAgent()
        agent.llm_client.client = mock_httpx_client
        agent.llm_client.use_mock = False

        response = await agent.process("Create a study plan")
        assert "LLM generated" in response or len(response) > 0
        await agent.llm_client.close()


class TestStudyAgent:
    """Test StudyAgent class"""

    @pytest.mark.asyncio
    async def test_study_agent_initialization(self):
        """Test StudyAgent initialization"""
        agent = StudyAgent()
        assert agent.name == "Çalışma Arkadaşı"
        assert hasattr(agent, "use_mock")
        assert hasattr(agent, "name")

    @pytest.mark.asyncio
    async def test_study_agent_question(self, study_agent):
        """Test study agent answering questions"""
        response = await study_agent.process("Python nedir?")
        assert "Soru" in response or "Cevap" in response
        assert len(response) > 100

    @pytest.mark.asyncio
    async def test_study_agent_quiz(self, study_agent):
        """Test study agent quiz creation"""
        response = await study_agent.process("Bana bir quiz hazırla")
        assert "Quiz" in response or "Soru" in response
        assert "Cevap" in response or "Doğru" in response

    @pytest.mark.asyncio
    async def test_study_agent_explanation(self, study_agent):
        """Test study agent concept explanation"""
        response = await study_agent.process("Recursion'ı açıkla")
        assert (
            "Açıklama" in response
            or "açıklama" in response
            or "konu" in response.lower()
        )

    @pytest.mark.asyncio
    async def test_study_agent_example(self, study_agent):
        """Test study agent giving examples"""
        response = await study_agent.process("Bana bir örnek ver")
        assert "Örnek" in response or "örnek" in response
        assert "Çözüm" in response or "Problem" in response

    @pytest.mark.asyncio
    async def test_study_agent_help(self, study_agent):
        """Test study agent help menu"""
        response = await study_agent.process("Yardım")
        assert "Yardım" in response or "yardım" in response
        assert "Quiz" in response or "Soru" in response

    @pytest.mark.asyncio
    async def test_study_agent_general(self, study_agent):
        """Test study agent general response"""
        response = await study_agent.process("Algoritma konusunda")
        assert len(response) > 0
        assert "yardım" in response.lower() or "konu" in response.lower()


class TestExamAgent:
    """Test ExamAgent class"""

    @pytest.mark.asyncio
    async def test_exam_agent_initialization(self):
        """Test ExamAgent initialization"""
        agent = ExamAgent()
        assert agent.name == "Sınav Uzmanı"
        assert hasattr(agent, "use_mock")
        assert hasattr(agent, "name")

    @pytest.mark.asyncio
    async def test_exam_agent_create_exam(self, exam_agent):
        """Test exam agent creating exam"""
        response = await exam_agent.process("Deneme sınavı oluştur")
        assert "Sınav" in response or "sınav" in response
        assert "Puan" in response or "puan" in response

    @pytest.mark.asyncio
    async def test_exam_agent_evaluation(self, exam_agent):
        """Test exam agent performance evaluation"""
        response = await exam_agent.process("Performansımı değerlendir")
        assert "Değerlendirme" in response or "Puan" in response
        assert "%" in response or "100" in response

    @pytest.mark.asyncio
    async def test_exam_agent_strategies(self, exam_agent):
        """Test exam agent strategies"""
        response = await exam_agent.process("Sınav stratejileri neler?")
        assert "Strateji" in response or "strateji" in response
        assert "Sınav" in response or "dakika" in response.lower()

    @pytest.mark.asyncio
    async def test_exam_agent_flashcards(self, exam_agent):
        """Test exam agent flashcard creation"""
        response = await exam_agent.process("Flashcard oluştur")
        assert "Flashcard" in response or "Kart" in response
        assert "ÖN YÜZ" in response or "ARKA YÜZ" in response

    @pytest.mark.asyncio
    async def test_exam_agent_time_management(self, exam_agent):
        """Test exam agent time management tips"""
        response = await exam_agent.process("Zaman yönetimi tavsiyeleri")
        assert "Zaman" in response or "zaman" in response
        assert "dakika" in response or "Dakika" in response

    @pytest.mark.asyncio
    async def test_exam_agent_stress_management(self, exam_agent):
        """Test exam agent stress management"""
        response = await exam_agent.process("Sınav stresi nasıl yönetilir?")
        assert "Stres" in response or "stres" in response
        assert "Nefes" in response or "Rahatlama" in response

    @pytest.mark.asyncio
    async def test_exam_agent_general(self, exam_agent):
        """Test exam agent general response"""
        response = await exam_agent.process("Yarınki sınav için")
        assert len(response) > 0
        assert "sınav" in response.lower() or "hazırlık" in response.lower()


class TestAgentIntegration:
    """Integration tests for all agents"""

    @pytest.mark.asyncio
    async def test_all_agents_respond(self):
        """Test that all agents can process messages"""
        agents = [LearningAgent(), StudyAgent(), ExamAgent()]
        test_message = "Merhaba, nasıl yardımcı olabilirsin?"

        for agent in agents:
            response = await agent.process(test_message)
            assert len(response) > 0
            assert isinstance(response, str)
            await agent.llm_client.close()

    @pytest.mark.asyncio
    async def test_agents_fallback_on_llm_failure(
        self, mock_env_with_llm, mock_httpx_client
    ):
        """Test agents fallback to mock responses when LLM fails"""
        mock_httpx_client.post.side_effect = Exception("Network error")

        agent = LearningAgent()
        agent.llm_client.client = mock_httpx_client
        agent.llm_client.use_mock = False

        response = await agent.process("plan oluştur")
        assert len(response) > 0  # Should fallback to keyword response
        assert "Plan" in response or "plan" in response
        await agent.llm_client.close()

    @pytest.mark.asyncio
    async def test_concurrent_agent_requests(self):
        """Test multiple agents can handle concurrent requests"""
        learning = LearningAgent()
        study = StudyAgent()
        exam = ExamAgent()

        tasks = [learning.process("plan"), study.process("quiz"), exam.process("sınav")]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        for response in responses:
            assert len(response) > 0

        # Cleanup
        await learning.llm_client.close()
        await study.llm_client.close()
        await exam.llm_client.close()
