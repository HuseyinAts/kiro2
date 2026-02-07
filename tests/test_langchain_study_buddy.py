"""
Test for LangChain Study Buddy Agent
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("langchain", reason="langchain not installed")


@pytest.fixture
def mock_langchain_service():
    """Mock LangChain service"""
    service = MagicMock()
    service.llm = MagicMock()
    service.chat_model = MagicMock()
    return service


@pytest.fixture
def mock_agent_executor():
    """Mock agent executor"""
    executor = AsyncMock()
    executor.arun = AsyncMock(return_value="Test response")
    executor.intermediate_steps = []
    return executor


@pytest.fixture
def mock_memory():
    """Mock conversation memory"""
    memory = MagicMock()
    memory.chat_memory.messages = []
    memory.clear = MagicMock()
    return memory


class TestLangChainStudyBuddy:
    """Test LangChain Study Buddy"""
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    def test_initialization(self, mock_service, mock_langchain_service):
        """Test Study Buddy initialization"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        
        with patch.object(LangChainStudyBuddy, '_initialize'):
            buddy = LangChainStudyBuddy()
            assert buddy is not None
            mock_service.assert_called_once()
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_memory_initialization(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                 mock_llm_chain, mock_memory_class, mock_service, mock_langchain_service, mock_memory):
        """Test memory initialization"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_memory_class.return_value = mock_memory
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        mock_memory_class.assert_called_once()
        assert buddy.memory is not None
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_tools_creation(self, mock_create_agent, mock_agent_exec, mock_seq_chain, 
                           mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test tools creation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        assert len(buddy.tools) >= 5
        assert any(tool.name == 'solve_math' for tool in buddy.tools)
        assert any(tool.name == 'generate_quiz' for tool in buddy.tools)
        assert any(tool.name == 'explain_concept' for tool in buddy.tools)
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_math_solver_tool(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                             mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test math solver tool"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Find math solver tool
        math_tool = None
        for tool in buddy.tools:
            if tool.name == 'solve_math':
                math_tool = tool
                break
        
        assert math_tool is not None
        
        # Test math solving
        result = math_tool.func("2+2")
        assert "Result: 4" in result
        
        # Test error handling
        result = math_tool.func("invalid")
        assert "Error" in result
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_quiz_generator_tool(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test quiz generator tool"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Find quiz generator tool
        quiz_tool = None
        for tool in buddy.tools:
            if tool.name == 'generate_quiz':
                quiz_tool = tool
                break
        
        assert quiz_tool is not None
        
        # Test quiz generation
        result = quiz_tool.func("Mathematics", 3)
        questions = json.loads(result)
        
        assert len(questions) == 3
        assert all('question' in q for q in questions)
        assert all('options' in q for q in questions)
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_concept_explanation_tool(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                     mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test concept explanation tool"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Find explanation tool
        explain_tool = None
        for tool in buddy.tools:
            if tool.name == 'explain_concept':
                explain_tool = tool
                break
        
        assert explain_tool is not None
        
        # Test explanations
        simple = explain_tool.func("Fractions", "simple")
        assert "Fractions" in simple
        assert "Basic explanation" in simple
        
        advanced = explain_tool.func("Fractions", "advanced")
        assert "Fractions" in advanced
        assert "technical details" in advanced
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_study_plan_tool(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                           mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test study plan creation tool"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Find study plan tool
        plan_tool = None
        for tool in buddy.tools:
            if tool.name == 'create_study_plan':
                plan_tool = tool
                break
        
        assert plan_tool is not None
        
        # Test study plan creation
        result = plan_tool.func("Mathematics", 60)
        plan = json.loads(result)
        
        assert plan['subject'] == "Mathematics"
        assert plan['duration_minutes'] == 60
        assert 'sessions' in plan
        assert 'topics' in plan
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_progress_tracker_tool(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                 mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test progress tracking tool"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Find progress tracker tool
        progress_tool = None
        for tool in buddy.tools:
            if tool.name == 'track_progress':
                progress_tool = tool
                break
        
        assert progress_tool is not None
        
        # Test progress tracking
        result = progress_tool.func("student123", "Algebra", 0.8)
        progress = json.loads(result)
        
        assert progress['student_id'] == "student123"
        assert progress['topic'] == "Algebra"
        assert progress['score'] == 0.8
        assert progress['status'] == "completed"
        
        # Test needs review status
        result = progress_tool.func("student456", "Geometry", 0.5)
        progress = json.loads(result)
        assert progress['status'] == "needs_review"
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    def test_chains_creation(self, mock_llm_chain, mock_service, mock_langchain_service):
        """Test chains creation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_llm_chain.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        assert 'quiz_chain' in buddy.chains
        assert 'learning_path_chain' in buddy.chains
        assert 'explanation_chain' in buddy.chains
        assert 'assessment_chain' in buddy.chains
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    def test_agent_creation(self, mock_executor, mock_service, mock_langchain_service):
        """Test agent creation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_executor.return_value = mock_agent_executor()
        
        buddy = LangChainStudyBuddy()
        
        mock_executor.assert_called_once()
        assert buddy.agent_executor is not None
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_chat_functionality(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                    mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test chat functionality"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        buddy.agent_executor = mock_agent_executor()
        buddy.memory = mock_memory()
        
        response = await buddy.chat("Hello, I want to learn math")
        
        assert response['success'] is True
        assert 'response' in response
        buddy.agent_executor.arun.assert_called_once()
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_chat_with_context(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                   mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test chat with context"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        buddy.agent_executor = mock_agent_executor()
        buddy.memory = mock_memory()
        
        context = {"grade": 8, "subject": "Math"}
        response = await buddy.chat("Explain fractions", context=context)
        
        assert response['success'] is True
        # Check that context was included in the call
        call_args = buddy.agent_executor.arun.call_args[1]['input']
        assert "Context:" in call_args
        assert "grade" in call_args
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_chat_error_handling(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                     mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test chat error handling"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        buddy.agent_executor = AsyncMock()
        buddy.agent_executor.arun.side_effect = Exception("Test error")
        buddy.memory = mock_memory()
        
        response = await buddy.chat("Test message")
        
        assert response['success'] is False
        assert 'error' in response
        assert response['response'] == "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_generate_lesson(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                 mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test lesson generation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        mock_chain = AsyncMock()
        mock_chain.arun.return_value = {
            "explanation": "Test explanation",
            "quiz": "Test quiz"
        }
        buddy.chains = {"lesson_chain": mock_chain}
        
        result = await buddy.generate_lesson("Fractions", grade=6)
        
        assert result['success'] is True
        assert result['topic'] == "Fractions"
        assert 'explanation' in result
        assert 'quiz' in result
        assert result['metadata']['grade'] == 6
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_generate_lesson_error(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                       mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test lesson generation error handling"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        mock_chain = AsyncMock()
        mock_chain.arun.side_effect = Exception("Test error")
        buddy.chains = {"lesson_chain": mock_chain}
        
        result = await buddy.generate_lesson("Fractions")
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_create_learning_path(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                      mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test learning path creation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        mock_chain = AsyncMock()
        mock_chain.arun.return_value = "Learning path content"
        buddy.chains = {"learning_path_chain": mock_chain}
        
        result = await buddy.create_learning_path(
            "Ali", "Geometry", "beginner", "visual", 5
        )
        
        assert result['success'] is True
        assert 'learning_path' in result
        mock_chain.arun.assert_called_once()
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_assess_understanding(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                      mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test understanding assessment"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        mock_chain = MagicMock()
        mock_chain.run.return_value = {"understanding": 85, "strengths": ["Good math skills"]}
        buddy.chains = {"assessment_chain": mock_chain}
        
        questions = ["What is 2+2?", "What is 5*3?"]
        answers = ["4", "15"]
        
        result = await buddy.assess_understanding(questions, answers)
        
        assert result['success'] is True
        assert 'assessment' in result
        mock_chain.run.assert_called_once()
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_memory_management(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                             mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test memory management"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        buddy.memory = mock_memory()
        
        # Test clear memory
        buddy.clear_memory()
        buddy.memory.clear.assert_called_once()
        
        # Test conversation summary
        summary = buddy.get_conversation_summary()
        assert summary == "No conversation history"
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    def test_conversation_summary_with_messages(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                             mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test conversation summary with messages"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy, HumanMessage, AIMessage
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        buddy.memory = MagicMock()
        buddy.memory.chat_memory.messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="Teach me math"),
            AIMessage(content="Let's start with basics")
        ]
        
        summary = buddy.get_conversation_summary()
        
        assert "Student: Hello" in summary
        assert "Tutor: Hi there!" in summary
        assert "Student: Teach me math" in summary
        assert "Tutor: Let's start with basics" in summary
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_structured_quiz_generation(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                            mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test structured quiz generation"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Test structured quiz generation with fallback
        result = await buddy._generate_structured_quiz("Math", 8, 3, "easy")
        
        questions = json.loads(result)
        assert len(questions) == 3
        assert all('question' in q for q in questions)
        assert all('difficulty' in q for q in questions)
    
    @patch('backend.agents.langchain_study_buddy.get_langchain_service')
    @patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory')
    @patch('backend.agents.langchain_study_buddy.LLMChain')
    @patch('backend.agents.langchain_study_buddy.SequentialChain')
    @patch('backend.agents.langchain_study_buddy.AgentExecutor')
    @patch('backend.agents.langchain_study_buddy.create_structured_chat_agent')
    @pytest.mark.asyncio
    async def test_student_assessment(self, mock_create_agent, mock_agent_exec, mock_seq_chain,
                                    mock_llm_chain, mock_mem_class, mock_service, mock_langchain_service):
        """Test student assessment functionality"""
        from backend.agents.langchain_study_buddy import LangChainStudyBuddy
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = MagicMock()
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        questions = ["What is 2+2?", "What is the capital of Turkey?"]
        answers = ["4", "Ankara"]
        
        # Test assessment with fallback
        result = await buddy._assess_student(questions, answers)
        
        assessment = json.loads(result)
        assert 'understanding_level' in assessment
        assert 'strengths' in assessment
        assert 'weaknesses' in assessment
        assert 'recommendations' in assessment


@pytest.mark.asyncio
async def test_example_usage(mock_langchain_service, mock_agent_executor, mock_memory):
    """Test example usage function"""
    from backend.agents.langchain_study_buddy import LangChainStudyBuddy
    
    with patch('backend.agents.langchain_study_buddy.get_langchain_service') as mock_service, \
         patch('backend.agents.langchain_study_buddy.ConversationSummaryBufferMemory') as mock_mem_class, \
         patch('backend.agents.langchain_study_buddy.LLMChain') as mock_llm_chain, \
         patch('backend.agents.langchain_study_buddy.SequentialChain') as mock_seq_chain, \
         patch('backend.agents.langchain_study_buddy.AgentExecutor') as mock_agent_exec, \
         patch('backend.agents.langchain_study_buddy.create_structured_chat_agent') as mock_create_agent:
        
        mock_service.return_value = mock_langchain_service
        mock_mem_class.return_value = mock_memory
        mock_llm_chain.return_value = MagicMock()
        mock_seq_chain.return_value = MagicMock()
        mock_agent_exec.return_value = mock_agent_executor
        mock_create_agent.return_value = MagicMock()
        
        buddy = LangChainStudyBuddy()
        
        # Mock chains
        buddy.chains = {
            "lesson_chain": AsyncMock(),
            "learning_path_chain": AsyncMock()
        }
        buddy.chains["lesson_chain"].arun.return_value = {"explanation": "Test", "quiz": "Test"}
        buddy.chains["learning_path_chain"].arun.return_value = "Test path"
        buddy.chains["assessment_chain"] = MagicMock()
        buddy.chains["assessment_chain"].run.return_value = {"understanding": 90}
        
        # Test chat
        response = await buddy.chat("Matematik öğrenmek istiyorum")
        assert response['success'] is True
        
        # Test lesson generation
        lesson = await buddy.generate_lesson("Kesirler", 6, "visual", "tr")
        assert lesson['success'] is True
        
        # Test learning path
        path = await buddy.create_learning_path("Ahmet", "Geometri", "beginner", "kinesthetic", 5)
        assert path['success'] is True
        
        # Test assessment
        assessment = await buddy.assess_understanding(["What is 2+2?"], ["4"])
        assert assessment['success'] is True


def test_pydantic_models():
    """Test Pydantic models"""
    from backend.agents.langchain_study_buddy import QuizQuestion, LearningPath, StudentAssessment
    
    # Test QuizQuestion
    question = QuizQuestion(
        question="What is 2+2?",
        options=["2", "3", "4", "5"],
        correct_answer="4",
        explanation="Basic addition",
        difficulty="easy"
    )
    assert question.question == "What is 2+2?"
    assert len(question.options) == 4
    assert question.correct_answer == "4"
    
    # Test LearningPath
    path = LearningPath(
        topic="Mathematics",
        subtopics=["Addition", "Subtraction"],
        difficulty_progression=["easy", "medium"],
        estimated_time=60,
        resources=["Textbook", "Online videos"]
    )
    assert path.topic == "Mathematics"
    assert len(path.subtopics) == 2
    assert path.estimated_time == 60
    
    # Test StudentAssessment
    assessment = StudentAssessment(
        understanding_level=0.8,
        strengths=["Good at calculations"],
        weaknesses=["Needs practice with word problems"],
        recommendations=["Practice more word problems"]
    )
    assert assessment.understanding_level == 0.8
    assert len(assessment.strengths) == 1
    assert len(assessment.weaknesses) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])