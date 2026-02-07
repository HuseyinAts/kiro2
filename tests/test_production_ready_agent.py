"""
Test for Production Ready Agent
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.agents.production_ready_agent import ProductionLearningAgent  # noqa: F401
except ImportError:
    pytest.skip("production_ready_agent dependencies not available", allow_module_level=True)


@pytest.fixture
def mock_content_provider():
    """Mock content provider"""
    provider = AsyncMock()
    provider.get_lgs_math_content.return_value = "Mock LGS math content"
    provider.get_personalized_plan.return_value = "Mock study plan"
    provider.get_study_resources.return_value = "Mock resources"
    return provider


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker"""
    breaker = MagicMock()
    breaker.call = AsyncMock(return_value="Mock response")
    breaker.is_open.return_value = False
    breaker.failure_count = 0
    return breaker


@pytest.fixture
def mock_health_checker():
    """Mock health checker"""
    checker = AsyncMock()
    checker.get_health_status.return_value = {
        'status': 'healthy',
        'checks': {}
    }
    return checker


@pytest.fixture
def mock_conversation_context():
    """Mock conversation context"""
    context = MagicMock()
    context.session_id = "test-session"
    context.student_id = "test-student"
    context.metadata = {'grade': 8, 'exam_target': 'LGS'}
    context.history = []
    context.get_context_summary.return_value = "Test context summary"
    return context


@pytest.fixture
def mock_global_metrics():
    """Mock global metrics"""
    metrics = MagicMock()
    metrics.record_request = MagicMock()
    metrics.record_error = MagicMock()
    metrics.record_cache_hit = MagicMock()
    metrics.record_cache_miss = MagicMock()
    metrics.record_llm_call = MagicMock()
    metrics.record_fallback_used = MagicMock()
    metrics.get_metrics_summary.return_value = {
        'total_requests': 100,
        'error_rate': 0.05
    }
    return metrics


class TestProductionLearningAgent:
    """Test Production Learning Agent"""
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    def test_initialization(self, mock_metrics, mock_health, mock_breaker, mock_provider, 
                           mock_content_provider, mock_circuit_breaker, mock_health_checker, mock_global_metrics):
        """Test agent initialization"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        assert agent.name == "ProductionLearningAgent"
        assert agent.max_context_length == 1000
        assert agent.response_timeout == 10.0
        mock_provider.assert_called_once()
        mock_breaker.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @patch('backend.agents.production_ready_agent.PerformanceMonitor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_monitor, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test successful processing"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        # Mock performance monitor as async context manager
        mock_monitor.return_value.__aenter__ = AsyncMock()
        mock_monitor.return_value.__aexit__ = AsyncMock()
        
        agent = ProductionLearningAgent()
        
        # Mock the parent process method
        with patch.object(agent.__class__.__bases__[0], 'process', new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = "Test response"
            
            result = await agent.process("Test message")
            
            assert result == "Test response"
            mock_metrics.record_request.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @patch('backend.agents.production_ready_agent.PerformanceMonitor')
    @pytest.mark.asyncio
    async def test_process_error_handling(self, mock_monitor, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test error handling in process method"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        # Mock performance monitor
        mock_monitor.return_value.__aenter__ = AsyncMock()
        mock_monitor.return_value.__aexit__ = AsyncMock()
        
        agent = ProductionLearningAgent()
        
        # Mock parent process to raise error
        with patch.object(agent.__class__.__bases__[0], 'process', new_callable=AsyncMock) as mock_parent:
            mock_parent.side_effect = Exception("Test error")
            
            result = await agent.process("Test message")
            
            # Should return fallback response
            assert "Özür dilerim" in result or "Teknik bir sorun" in result
            mock_metrics.record_error.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_process_mock_lgs_math(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test mock processing for LGS math"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        content_provider = mock_content_provider
        mock_provider.return_value = content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        result = await agent._process_mock("LGS matematik", None)
        
        assert result == "Mock LGS math content"
        content_provider.get_lgs_math_content.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_process_mock_study_plan(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test mock processing for study plan"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        content_provider = mock_content_provider
        mock_provider.return_value = content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        context = mock_conversation_context
        context.metadata = {'available_hours': 30}
        
        result = await agent._process_mock("LGS plan", context)
        
        assert result == "Mock study plan"
        content_provider.get_personalized_plan.assert_called_with(
            "lgs_matematik", available_hours=30
        )
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_process_mock_resources(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test mock processing for resources"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        content_provider = mock_content_provider
        mock_provider.return_value = content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        result = await agent._process_mock("LGS kaynak", None)
        
        assert result == "Mock resources"
        content_provider.get_study_resources.assert_called_with("lgs_matematik")
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_process_with_llm_cache_hit(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test LLM processing with cache hit"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        # Mock cache hit
        with patch.object(agent, 'cache') as mock_cache:
            mock_cache.get.return_value = "Cached response"
            
            result = await agent._process_with_llm("Test message", None)
            
            assert result == "Cached response"
            mock_metrics.record_cache_hit.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @patch('backend.agents.production_ready_agent.llm_service')
    @pytest.mark.asyncio
    async def test_call_llm_with_timeout_success(self, mock_llm, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test LLM call with timeout success"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        # Mock LLM service
        mock_llm.generate = AsyncMock(return_value={
            "success": True,
            "text": "LLM response"
        })
        
        agent = ProductionLearningAgent()
        
        result = await agent._call_llm_with_timeout("Test prompt", None)
        
        assert result == "LLM response"
        mock_llm.generate.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @patch('backend.agents.production_ready_agent.llm_service')
    @pytest.mark.asyncio
    async def test_call_llm_with_timeout_error(self, mock_llm, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test LLM call timeout error"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        # Mock LLM service to return empty response
        mock_llm.generate = AsyncMock(return_value={
            "success": False,
            "text": ""
        })
        
        agent = ProductionLearningAgent()
        
        with pytest.raises(Exception, match="LLM returned empty response"):
            await agent._call_llm_with_timeout("Test prompt", None)
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    def test_build_enhanced_prompt_with_context(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test enhanced prompt building with context"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        context = mock_conversation_context
        context.history = ["Previous message"]
        
        prompt = agent._build_enhanced_prompt("Test message", context)
        
        assert "Önceki konuşma özeti:" in prompt
        assert "Öğrenci ID: test-student" in prompt
        assert "Sınıf: 8" in prompt
        assert "Hedef: LGS" in prompt
        assert "Öğrenci sorusu: Test message" in prompt
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    def test_build_enhanced_prompt_without_context(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test enhanced prompt building without context"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        prompt = agent._build_enhanced_prompt("Test message", None)
        
        assert prompt == "Öğrenci sorusu: Test message"
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    def test_get_system_prompt_lgs(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test system prompt for LGS context"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        context = mock_conversation_context
        context.metadata = {'exam_target': 'LGS'}
        
        prompt = agent._get_system_prompt(context)
        
        assert "eğitim asistanısın" in prompt
        assert "8. sınıf seviyesinde" in prompt
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    def test_get_system_prompt_yks(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test system prompt for YKS context"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        context = mock_conversation_context
        context.metadata = {'exam_target': 'YKS'}
        
        prompt = agent._get_system_prompt(context)
        
        assert "eğitim asistanısın" in prompt
        assert "lise seviyesinde" in prompt
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_get_content_based_response(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test content-based response"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        content_provider = mock_content_provider
        mock_provider.return_value = content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        # Test math content
        result = await agent._get_content_based_response("matematik sorusu")
        assert result == "Mock LGS math content"
        
        # Test plan content
        result = await agent._get_content_based_response("çalışma planı")
        assert result == "Mock study plan"
        
        # Test resources
        result = await agent._get_content_based_response("kaynak önerisi")
        assert result == "Mock resources"
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_get_fallback_response(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test fallback response"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        result = await agent._get_fallback_response("test message")
        
        # Should be one of the predefined fallback responses
        assert any(phrase in result for phrase in [
            "Özür dilerim",
            "Teknik bir sorun",
            "test message"
        ])
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_get_educational_response(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test educational response"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        result = await agent._get_educational_response("test topic", None)
        
        assert "Eğitim konusunda" in result
        assert "test topic" in result
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_get_general_lgs_info(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test general LGS information"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        result = await agent._get_general_lgs_info()
        
        assert "LGS HAKKINDA" in result
        assert "Liselere Geçiş Sınavı" in result
        assert "Sözel Bölüm" in result
        assert "Sayısal Bölüm" in result
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_get_health_status(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test health status"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        circuit_breaker = mock_circuit_breaker
        mock_breaker.return_value = circuit_breaker
        health_checker = mock_health_checker
        mock_health.return_value = health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        health = await agent.get_health_status()
        
        assert health['status'] == 'healthy'
        assert 'circuit_breaker' in health['checks']
        assert health['checks']['circuit_breaker']['status'] == 'closed'
        assert health['checks']['circuit_breaker']['failures'] == 0
    
    @patch('backend.agents.production_ready_agent.ContentProvider')
    @patch('backend.agents.production_ready_agent.CircuitBreaker')
    @patch('backend.agents.production_ready_agent.HealthChecker')
    @patch('backend.agents.production_ready_agent.global_metrics')
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_metrics, mock_health, mock_breaker, mock_provider):
        """Test cleanup"""
        from backend.agents.production_ready_agent import ProductionLearningAgent
        
        mock_provider.return_value = mock_content_provider
        mock_breaker.return_value = mock_circuit_breaker
        mock_health.return_value = mock_health_checker
        mock_metrics = mock_global_metrics
        
        agent = ProductionLearningAgent()
        
        # Should not raise any exceptions
        await agent.cleanup()


class TestAgentFactory:
    """Test Agent Factory"""
    
    def test_create_learning_agent(self):
        """Test creating learning agent"""
        from backend.agents.production_ready_agent import AgentFactory
        
        with patch('backend.agents.production_ready_agent.ProductionLearningAgent') as mock_agent:
            mock_agent.return_value = MagicMock()
            
            agent = AgentFactory.create_agent("learning")
            
            assert agent is not None
            mock_agent.assert_called_once()
    
    def test_create_unknown_agent(self):
        """Test creating unknown agent type"""
        from backend.agents.production_ready_agent import AgentFactory
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            AgentFactory.create_agent("unknown")
    
    def test_singleton_behavior(self):
        """Test factory singleton behavior"""
        from backend.agents.production_ready_agent import AgentFactory
        
        with patch('backend.agents.production_ready_agent.ProductionLearningAgent') as mock_agent:
            mock_instance = MagicMock()
            mock_agent.return_value = mock_instance
            
            agent1 = AgentFactory.create_agent("learning")
            agent2 = AgentFactory.create_agent("learning")
            
            # Should return the same instance
            assert agent1 is agent2
            # Should only create once
            mock_agent.assert_called_once()
    
    @patch('backend.agents.production_ready_agent.LLMConnectionPool')
    @pytest.mark.asyncio
    async def test_cleanup_all(self, mock_pool):
        """Test cleanup all agents"""
        from backend.agents.production_ready_agent import AgentFactory
        
        # Reset the factory
        AgentFactory._agents = {}
        
        with patch('backend.agents.production_ready_agent.ProductionLearningAgent') as mock_agent:
            mock_instance = AsyncMock()
            mock_instance.cleanup = AsyncMock()
            mock_agent.return_value = mock_instance
            
            # Create an agent
            agent = AgentFactory.create_agent("learning")
            
            # Cleanup all
            await AgentFactory.cleanup_all()
            
            # Should call cleanup on agent
            mock_instance.cleanup.assert_called_once()
            # Should close connection pool
            mock_pool.close.assert_called_once()


@pytest.mark.asyncio
async def test_main_example():
    """Test main example function"""
    from backend.agents.production_ready_agent import AgentFactory, ConversationContext
    
    with patch.object(AgentFactory, 'create_agent') as mock_create:
        with patch.object(AgentFactory, 'cleanup_all') as mock_cleanup:
            # Mock agent
            mock_agent = AsyncMock()
            mock_agent.process.return_value = "Mock response for testing"
            mock_agent.get_health_status.return_value = {'status': 'healthy'}
            mock_create.return_value = mock_agent
            
            # Mock global metrics
            with patch('backend.agents.production_ready_agent.global_metrics') as mock_metrics:
                mock_metrics.get_metrics_summary.return_value = {
                    'total_requests': 100,
                    'error_rate': 0.05
                }
                
                # Import and run main
                from backend.agents.production_ready_agent import main
                
                # Should not raise any exceptions
                await main()
                
                # Verify agent was created and used
                mock_create.assert_called_with("learning")
                assert mock_agent.process.call_count == 3  # Three test messages
                mock_agent.get_health_status.assert_called_once()
                mock_cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])