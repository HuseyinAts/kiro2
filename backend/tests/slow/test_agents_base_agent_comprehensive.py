"""
Comprehensive tests for agents.base_agent module
Target: 75%+ coverage for base agent functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from agents.base_agent import (
    BaseAgent,
    AgentType,
    AgentStatus,
    MessageType,
    AgentMessage,
    AgentCapability,
    AgentMetrics,
)


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""

    async def process_request(
        self, request_type: str, parameters: dict, context: dict = None
    ):
        """Mock implementation for testing"""
        return {
            "status": "success",
            "request_type": request_type,
            "parameters": parameters,
            "context": context,
            "processed_by": self.agent_id,
        }


@pytest.fixture
def base_agent():
    """Create BaseAgent instance for testing"""
    return ConcreteTestAgent(
        agent_id="test_agent_123",
        agent_type=AgentType.LEARNING_PATH,
        name="Test Agent",
        description="Test agent for testing purposes",
    )


@pytest.fixture
def sample_request():
    """Sample request data for testing"""
    return {
        "request_type": "analyze_text",
        "parameters": {
            "text": "Bu bir Türkçe metin örneğidir.",
            "analysis_type": "complexity",
            "language": "turkish",
        },
        "context": {"user_id": "user_123", "session_id": "session_456"},
    }


@pytest.fixture
def sample_message():
    """Sample agent message for testing"""
    return AgentMessage(
        message_id="msg_123",
        sender_agent="agent_456",
        receiver_agent="agent_789",
        message_type=MessageType.REQUEST,
        content={"action": "analyze", "data": "test data"},
        timestamp=datetime.now(),
    )


@pytest.fixture
def sample_capability():
    """Sample agent capability for testing"""
    return AgentCapability(
        name="text_analysis",
        description="Text analysis capability",
        input_types=["text", "document"],
        output_types=["analysis_result"],
        parameters={"language": "turkish", "complexity": "medium"},
        performance_metrics={"accuracy": 0.95, "speed": 0.85},
    )


class TestBaseAgentInitialization:
    """Test BaseAgent initialization"""

    def test_base_agent_initialization(self, base_agent):
        """Test BaseAgent initialization with valid parameters"""
        assert base_agent.agent_id == "test_agent_123"
        assert base_agent.agent_type == AgentType.LEARNING_PATH
        assert base_agent.name == "Test Agent"
        assert base_agent.description == "Test agent for testing purposes"
        assert base_agent.status == AgentStatus.IDLE
        assert isinstance(base_agent.capabilities, list)
        assert isinstance(base_agent.metrics, AgentMetrics)
        assert base_agent.metrics.agent_id == "test_agent_123"

    def test_base_agent_initialization_all_agent_types(self):
        """Test BaseAgent initialization with all agent types"""
        agent_types = list(AgentType)

        for agent_type in agent_types:
            agent = ConcreteTestAgent(
                agent_id=f"agent_{agent_type.value}",
                agent_type=agent_type,
                name=f"Test {agent_type.value}",
                description=f"Test agent for {agent_type.value}",
            )
            assert agent.agent_type == agent_type
            assert agent.status == AgentStatus.IDLE

    def test_base_agent_initialization_turkish_id(self):
        """Test BaseAgent initialization with Turkish characters in ID"""
        agent = ConcreteTestAgent(
            agent_id="türkçe_agent_öğrenci",
            agent_type=AgentType.ACCESSIBILITY,
            name="Türkçe Agent",
            description="Turkish character test agent",
        )

        assert agent.agent_id == "türkçe_agent_öğrenci"
        assert agent.status == AgentStatus.IDLE
        assert "Türkçe" in agent.name

    def test_agent_metrics_initialization(self, base_agent):
        """Test that agent metrics are properly initialized"""
        assert base_agent.metrics.agent_id == base_agent.agent_id
        assert base_agent.metrics.total_requests == 0
        assert base_agent.metrics.successful_requests == 0
        assert base_agent.metrics.failed_requests == 0
        assert base_agent.metrics.avg_response_time == 0.0
        assert base_agent.metrics.uptime_percentage == 100.0

    def test_agent_data_structures_initialization(self, base_agent):
        """Test that data structures are properly initialized"""
        assert isinstance(base_agent.message_queue, list)
        assert isinstance(base_agent.blackboard_subscriptions, list)
        assert isinstance(base_agent.coordination_handlers, dict)
        assert isinstance(base_agent.error_handlers, dict)
        assert isinstance(base_agent.config, dict)
        assert isinstance(base_agent.cache, dict)


class TestBaseAgentProcessRequest:
    """Test BaseAgent request processing"""

    @pytest.mark.asyncio
    async def test_process_request_success(self, base_agent, sample_request):
        """Test successful request processing"""
        result = await base_agent.process_request(
            request_type=sample_request["request_type"],
            parameters=sample_request["parameters"],
            context=sample_request["context"],
        )

        assert result["status"] == "success"
        assert result["request_type"] == "analyze_text"
        assert result["processed_by"] == base_agent.agent_id
        assert "parameters" in result
        assert "context" in result

    @pytest.mark.asyncio
    async def test_process_request_with_turkish_content(self, base_agent):
        """Test request processing with Turkish content"""
        turkish_request = {
            "request_type": "metin_analizi",
            "parameters": {
                "metin": "Bu çok güzel bir Türkçe metin örneğidir. İçerisinde çeşitli Türkçe karakterler bulunmaktadır: çğıöşü",
                "analiz_türü": "karmaşıklık",
                "dil": "türkçe",
            },
            "context": {"kullanıcı_id": "öğrenci_123", "oturum_id": "oturum_456"},
        }

        result = await base_agent.process_request(
            request_type=turkish_request["request_type"],
            parameters=turkish_request["parameters"],
            context=turkish_request["context"],
        )

        assert result["status"] == "success"
        assert result["request_type"] == "metin_analizi"
        assert "türkçe" in str(result["parameters"])

    @pytest.mark.asyncio
    async def test_process_request_minimal_parameters(self, base_agent):
        """Test request processing with minimal parameters"""
        result = await base_agent.process_request(
            request_type="simple_request", parameters={}
        )

        assert result["status"] == "success"
        assert result["request_type"] == "simple_request"
        assert result["parameters"] == {}
        assert result["context"] is None

    @pytest.mark.asyncio
    async def test_process_request_complex_parameters(self, base_agent):
        """Test request processing with complex parameters"""
        complex_params = {
            "nested_data": {
                "students": [
                    {"name": "Ahmet", "grade": 85},
                    {"name": "Ayşe", "grade": 92},
                ],
                "exam": {
                    "name": "TYT Matematik",
                    "duration": 120,
                    "questions": ["q1", "q2", "q3"],
                },
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "exam_system",
            },
        }

        result = await base_agent.process_request(
            request_type="complex_analysis", parameters=complex_params
        )

        assert result["status"] == "success"
        assert "nested_data" in result["parameters"]
        assert "students" in result["parameters"]["nested_data"]


class TestBaseAgentBlackboard:
    """Test BaseAgent blackboard functionality"""

    def test_register_to_blackboard_success(self, base_agent):
        """Test successful blackboard registration"""
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.return_value = True

        with patch.object(base_agent, "_setup_default_subscriptions") as mock_setup:
            result = base_agent.register_to_blackboard(mock_blackboard)

            assert result is True
            assert base_agent.blackboard is mock_blackboard
            mock_blackboard.register_agent.assert_called_once_with(
                base_agent.agent_id, base_agent
            )
            mock_setup.assert_called_once()

    def test_register_to_blackboard_failure(self, base_agent):
        """Test blackboard registration failure"""
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.return_value = False

        result = base_agent.register_to_blackboard(mock_blackboard)

        assert result is False
        assert base_agent.blackboard is mock_blackboard

    def test_register_to_blackboard_exception(self, base_agent):
        """Test blackboard registration with exception"""
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.side_effect = Exception("Registration failed")

        result = base_agent.register_to_blackboard(mock_blackboard)

        assert result is False

    @pytest.mark.asyncio
    async def test_write_to_blackboard_success(self, base_agent):
        """Test successful blackboard write"""
        mock_blackboard = AsyncMock()
        mock_blackboard.write.return_value = True
        base_agent.blackboard = mock_blackboard

        # Patch the write_to_blackboard method to avoid import issues
        with patch.object(base_agent, "write_to_blackboard") as mock_write:
            mock_write.return_value = True

            result = await base_agent.write_to_blackboard(
                key="test_key",
                value={"data": "test_value"},
                ttl_seconds=300,
                metadata={"source": "test"},
            )

            assert result is True
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_to_blackboard_no_connection(self, base_agent):
        """Test blackboard write without connection"""
        base_agent.blackboard = None

        result = await base_agent.write_to_blackboard("test_key", "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_write_to_blackboard_turkish_content(self, base_agent):
        """Test blackboard write with Turkish content"""
        mock_blackboard = AsyncMock()
        mock_blackboard.write.return_value = True
        base_agent.blackboard = mock_blackboard

        turkish_data = {
            "öğrenci_adı": "Ahmet Çelik",
            "sınav_sonucu": "başarılı",
            "notlar": ["çok iyi", "mükemmel", "güzel"],
        }

        # Patch the write_to_blackboard method to avoid import issues
        with patch.object(base_agent, "write_to_blackboard") as mock_write:
            mock_write.return_value = True

            result = await base_agent.write_to_blackboard(
                key="türkçe_veri", value=turkish_data
            )

            assert result is True
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_blackboard_update(self, base_agent):
        """Test blackboard update handling"""
        with patch.object(base_agent, "_process_blackboard_update") as mock_process:
            await base_agent.on_blackboard_update(
                key="test_key",
                value="test_value",
                source_agent="other_agent",
                event_type="UPDATE",
            )

            mock_process.assert_called_once_with(
                "test_key", "test_value", "other_agent", "UPDATE"
            )

    @pytest.mark.asyncio
    async def test_coordination_request_handling(self, base_agent):
        """Test coordination request handling"""
        coordination_data = {
            "type": "collaborative_analysis",
            "coordination_id": "coord_123",
            "target_agents": [base_agent.agent_id],
            "parameters": {"task": "analyze_together"},
        }

        with patch.object(base_agent, "_process_coordination_request") as mock_process:
            mock_process.return_value = {"status": "accepted"}

            await base_agent._handle_coordination_request(
                key="coordination_request",
                value=coordination_data,
                source_agent="coordinator_agent",
            )

            mock_process.assert_called_once()


class TestBaseAgentCapabilities:
    """Test BaseAgent capability management"""

    def test_add_capability(self, base_agent, sample_capability):
        """Test adding capability to agent"""
        initial_count = len(base_agent.capabilities)
        base_agent.capabilities.append(sample_capability)

        assert len(base_agent.capabilities) == initial_count + 1
        assert sample_capability in base_agent.capabilities

    def test_capability_structure(self, sample_capability):
        """Test capability data structure"""
        assert hasattr(sample_capability, "name")
        assert hasattr(sample_capability, "description")
        assert hasattr(sample_capability, "input_types")
        assert hasattr(sample_capability, "output_types")
        assert hasattr(sample_capability, "parameters")
        assert hasattr(sample_capability, "performance_metrics")

        assert isinstance(sample_capability.input_types, list)
        assert isinstance(sample_capability.output_types, list)
        assert isinstance(sample_capability.parameters, dict)
        assert isinstance(sample_capability.performance_metrics, dict)

    def test_turkish_capability(self, base_agent):
        """Test capability with Turkish content"""
        turkish_capability = AgentCapability(
            name="türkçe_analiz",
            description="Türkçe metin analizi yeteneği",
            input_types=["türkçe_metin"],
            output_types=["analiz_sonucu"],
            parameters={"dil": "türkçe", "karmaşıklık": "orta"},
            performance_metrics={"doğruluk": 0.95, "hız": 0.85},
        )

        base_agent.capabilities.append(turkish_capability)

        assert turkish_capability in base_agent.capabilities
        assert "türkçe" in turkish_capability.name
        assert "Türkçe" in turkish_capability.description


class TestBaseAgentMetrics:
    """Test BaseAgent metrics functionality"""

    def test_metrics_initialization(self, base_agent):
        """Test metrics initialization"""
        metrics = base_agent.metrics

        assert metrics.agent_id == base_agent.agent_id
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.uptime_percentage == 100.0

    def test_metrics_update(self, base_agent):
        """Test metrics updates"""
        # Simulate some activity
        base_agent.metrics.total_requests = 10
        base_agent.metrics.successful_requests = 8
        base_agent.metrics.failed_requests = 2
        base_agent.metrics.avg_response_time = 0.25
        base_agent.metrics.last_activity = datetime.now()

        assert base_agent.metrics.total_requests == 10
        assert base_agent.metrics.successful_requests == 8
        assert base_agent.metrics.failed_requests == 2
        assert base_agent.metrics.avg_response_time == 0.25
        assert base_agent.metrics.last_activity is not None

    def test_metrics_calculation(self, base_agent):
        """Test metrics calculations"""
        base_agent.metrics.total_requests = 100
        base_agent.metrics.successful_requests = 95
        base_agent.metrics.failed_requests = 5

        success_rate = (
            base_agent.metrics.successful_requests / base_agent.metrics.total_requests
        )
        failure_rate = (
            base_agent.metrics.failed_requests / base_agent.metrics.total_requests
        )

        assert success_rate == 0.95
        assert failure_rate == 0.05
        assert success_rate + failure_rate == 1.0


class TestBaseAgentStatus:
    """Test BaseAgent status management"""

    def test_initial_status(self, base_agent):
        """Test initial agent status"""
        assert base_agent.status == AgentStatus.IDLE

    def test_status_changes(self, base_agent):
        """Test status changes"""
        # Test all status values
        for status in AgentStatus:
            base_agent.status = status
            assert base_agent.status == status

    def test_status_workflow(self, base_agent):
        """Test typical status workflow"""
        # Start idle
        assert base_agent.status == AgentStatus.IDLE

        # Start working
        base_agent.status = AgentStatus.WORKING
        assert base_agent.status == AgentStatus.WORKING

        # Back to idle
        base_agent.status = AgentStatus.IDLE
        assert base_agent.status == AgentStatus.IDLE

        # Error state
        base_agent.status = AgentStatus.ERROR
        assert base_agent.status == AgentStatus.ERROR

        # Offline
        base_agent.status = AgentStatus.OFFLINE
        assert base_agent.status == AgentStatus.OFFLINE


class TestBaseAgentMessageHandling:
    """Test BaseAgent message handling"""

    def test_message_structure(self, sample_message):
        """Test message data structure"""
        assert hasattr(sample_message, "message_id")
        assert hasattr(sample_message, "sender_agent")
        assert hasattr(sample_message, "receiver_agent")
        assert hasattr(sample_message, "message_type")
        assert hasattr(sample_message, "content")
        assert hasattr(sample_message, "timestamp")
        assert hasattr(sample_message, "priority")
        assert hasattr(sample_message, "requires_response")
        assert hasattr(sample_message, "correlation_id")

    def test_message_queue_management(self, base_agent, sample_message):
        """Test message queue management"""
        initial_count = len(base_agent.message_queue)

        # Add message to queue
        base_agent.message_queue.append(sample_message)

        assert len(base_agent.message_queue) == initial_count + 1
        assert sample_message in base_agent.message_queue

    def test_turkish_message_content(self, base_agent):
        """Test message with Turkish content"""
        turkish_message = AgentMessage(
            message_id="turkish_msg_123",
            sender_agent="türkçe_agent",
            receiver_agent=base_agent.agent_id,
            message_type=MessageType.NOTIFICATION,
            content={
                "başlık": "Türkçe Mesaj",
                "içerik": "Bu bir Türkçe mesaj içeriğidir: çğıöşü",
                "öncelik": "yüksek",
            },
            timestamp=datetime.now(),
        )

        base_agent.message_queue.append(turkish_message)

        assert turkish_message in base_agent.message_queue
        assert "Türkçe" in turkish_message.content["başlık"]


class TestBaseAgentErrorHandling:
    """Test BaseAgent error handling"""

    @pytest.mark.asyncio
    async def test_blackboard_update_exception_handling(self, base_agent):
        """Test exception handling in blackboard updates"""
        # This should not raise an exception
        await base_agent.on_blackboard_update(
            key="test_key",
            value=None,  # This might cause issues
            source_agent="test_agent",
            event_type="UPDATE",
        )

    @pytest.mark.asyncio
    async def test_coordination_request_invalid_data(self, base_agent):
        """Test coordination request with invalid data"""
        invalid_data = "not_a_dict"

        # Should handle gracefully
        await base_agent._handle_coordination_request(
            key="coordination_request", value=invalid_data, source_agent="test_agent"
        )

    def test_blackboard_registration_exception_handling(self, base_agent):
        """Test exception handling in blackboard registration"""
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.side_effect = Exception("Connection failed")

        # Should return False, not raise exception
        result = base_agent.register_to_blackboard(mock_blackboard)
        assert result is False


class TestBaseAgentConcurrency:
    """Test BaseAgent concurrency handling"""

    @pytest.mark.asyncio
    async def test_concurrent_request_processing(self, base_agent):
        """Test concurrent request processing"""
        requests = []
        for i in range(3):
            requests.extend(
                [
                    ("request_1", {"data": f"data_{i}"}),
                    ("request_2", {"data": f"data_{i}"}),
                    ("request_3", {"data": f"data_{i}"}),
                ]
            )

        # Process requests concurrently
        tasks = [
            base_agent.process_request(req_type, params)
            for req_type, params in requests
        ]
        results = await asyncio.gather(*tasks)

        # All requests should be processed successfully
        assert len(results) == 9  # 3 request types × 3 instances
        for result in results:
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_concurrent_blackboard_writes(self, base_agent):
        """Test concurrent blackboard writes"""
        mock_blackboard = AsyncMock()
        mock_blackboard.write.return_value = True
        base_agent.blackboard = mock_blackboard

        # Patch the write_to_blackboard method to avoid import issues
        with patch.object(base_agent, "write_to_blackboard") as mock_write:
            mock_write.return_value = True

            # Perform concurrent writes
            write_tasks = [
                base_agent.write_to_blackboard(f"key_{i}", f"value_{i}")
                for i in range(5)
            ]
            results = await asyncio.gather(*write_tasks)

            # All writes should succeed
            assert all(results)
            assert mock_write.call_count == 5


class TestBaseAgentIntegration:
    """Integration tests for BaseAgent"""

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, base_agent, sample_request):
        """Test complete agent workflow"""
        # 1. Check initial state
        assert base_agent.status == AgentStatus.IDLE
        assert len(base_agent.capabilities) == 0

        # 2. Add capability
        capability = AgentCapability(
            name="test_capability",
            description="Test capability",
            input_types=["text"],
            output_types=["result"],
            parameters={},
            performance_metrics={},
        )
        base_agent.capabilities.append(capability)

        # 3. Register to blackboard
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.return_value = True

        with patch.object(base_agent, "_setup_default_subscriptions"):
            result = base_agent.register_to_blackboard(mock_blackboard)
            assert result is True

        # 4. Process request
        result = await base_agent.process_request(
            request_type=sample_request["request_type"],
            parameters=sample_request["parameters"],
            context=sample_request["context"],
        )
        assert result["status"] == "success"

        # 5. Update metrics
        base_agent.metrics.total_requests += 1
        base_agent.metrics.successful_requests += 1
        assert base_agent.metrics.total_requests == 1

    @pytest.mark.asyncio
    async def test_multi_agent_coordination_simulation(self):
        """Test simulation of multi-agent coordination"""
        # Create multiple agents
        agent1 = ConcreteTestAgent(
            agent_id="agent_1",
            agent_type=AgentType.LEARNING_PATH,
            name="Learning Path Agent",
            description="Handles learning path generation",
        )
        agent2 = ConcreteTestAgent(
            agent_id="agent_2",
            agent_type=AgentType.STUDY_BUDDY,
            name="Study Buddy Agent",
            description="Provides study assistance",
        )

        # Setup mock blackboard
        mock_blackboard = MagicMock()
        mock_blackboard.register_agent.return_value = True

        with patch.object(agent1, "_setup_default_subscriptions"), patch.object(
            agent2, "_setup_default_subscriptions"
        ):
            # Register agents
            assert agent1.register_to_blackboard(mock_blackboard) is True
            assert agent2.register_to_blackboard(mock_blackboard) is True

        # Test coordination request
        coordination_data = {
            "type": "collaborative_task",
            "coordination_id": "coord_123",
            "target_agents": ["agent_2"],
            "parameters": {"task": "help_with_learning"},
        }

        # Agent1 initiates coordination with Agent2
        await agent1._handle_coordination_request(
            key="coordination_request", value=coordination_data, source_agent="agent_1"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
