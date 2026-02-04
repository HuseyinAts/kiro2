"""
Multi-Agent Blackboard Sistemi Test Dosyası
Teknofest 2025 - Eğitim Eylemci Projesi

Bu test dosyası:
- MultiAgentBlackboard sınıfının tüm fonksiyonlarını test eder
- Agent koordinasyonu senaryolarını test eder
- WebSocket gerçek zamanlı senkronizasyon testleri içerir
- Performans ve güvenilirlik testleri yapar
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from agents.base_agent import AgentType, BaseAgent
from algorithms.agent_synergy_examples import SynergyResult, get_synergy_orchestrator

# Test edilecek modüller
from algorithms.multi_agent_blackboard import (
    BlackboardData,
    BlackboardEvent,
    EventType,
    Priority,
    get_blackboard,
    reset_blackboard,
)


class MockAgent(BaseAgent):
    """Test için mock agent sınıfı"""

    def __init__(self, agent_id: str, agent_type: AgentType):
        super().__init__(
            agent_id, agent_type, f"Mock {agent_id}", f"Mock agent for testing"
        )
        self.received_updates = []
        self.coordination_responses = {}

    async def process_request(
        self, request_type: str, parameters: Dict[str, Any], context=None
    ):
        """Mock process request"""
        return {
            "success": True,
            "agent_id": self.agent_id,
            "request_type": request_type,
            "parameters": parameters,
        }

    async def _process_blackboard_update(
        self, key: str, value: Any, source_agent: str, event_type
    ):
        """Blackboard güncellemelerini kaydet"""
        self.received_updates.append(
            {
                "key": key,
                "value": value,
                "source_agent": source_agent,
                "event_type": event_type,
                "timestamp": datetime.now(),
            }
        )

    async def _process_coordination_request(
        self, coordination_type: str, parameters: Dict[str, Any], source_agent: str
    ):
        """Koordinasyon talebini işle"""
        response = {
            "status": "success",
            "agent_id": self.agent_id,
            "coordination_type": coordination_type,
            "response_data": f"Mock response from {self.agent_id}",
            "timestamp": datetime.now().isoformat(),
        }

        self.coordination_responses[coordination_type] = response
        return response


@pytest.fixture
def blackboard():
    """Test için temiz blackboard instance'ı"""
    reset_blackboard()
    return get_blackboard()


@pytest.fixture
def mock_agents():
    """Test için mock agent'lar"""
    agents = [
        MockAgent("learning_path_agent", AgentType.LEARNING_PATH),
        MockAgent("study_buddy_agent", AgentType.STUDY_BUDDY),
        MockAgent("accessibility_agent", AgentType.ACCESSIBILITY),
    ]
    return agents


@pytest.fixture
def synergy_orchestrator():
    """Test için sinerji orkestratörü"""
    return get_synergy_orchestrator()


class TestMultiAgentBlackboard:
    """MultiAgentBlackboard sınıfı testleri"""

    def test_blackboard_initialization(self, blackboard):
        """Blackboard başlatma testi"""
        assert blackboard is not None
        assert len(blackboard.blackboard) == 0
        assert len(blackboard.registered_agents) == 0
        assert len(blackboard.event_history) == 0
        assert blackboard.metrics["total_writes"] == 0
        assert blackboard.metrics["total_reads"] == 0

    def test_agent_registration(self, blackboard, mock_agents):
        """Agent kayıt testi"""
        agent = mock_agents[0]

        # Agent'ı kaydet
        success = blackboard.register_agent(agent.agent_id, agent)
        assert success is True
        assert agent.agent_id in blackboard.registered_agents

        # Aynı agent'ı tekrar kaydetmeye çalış
        success = blackboard.register_agent(agent.agent_id, agent)
        assert success is False

    @pytest.mark.asyncio
    async def test_write_and_read_data(self, blackboard):
        """Veri yazma ve okuma testi"""
        key = "test_key"
        value = {"message": "test data", "number": 42}
        source_agent = "test_agent"

        # Veri yaz
        success = await blackboard.write(key, value, source_agent)
        assert success is True
        assert blackboard.metrics["total_writes"] == 1

        # Veri oku
        read_value = blackboard.read(key, "reader_agent")
        assert read_value == value
        assert blackboard.metrics["total_reads"] == 1

        # Olmayan veri oku
        none_value = blackboard.read("nonexistent_key", "reader_agent")
        assert none_value is None

    @pytest.mark.asyncio
    async def test_data_ttl(self, blackboard):
        """TTL (Time To Live) testi"""
        key = "ttl_test_key"
        value = "ttl_test_value"
        source_agent = "test_agent"

        # 1 saniye TTL ile veri yaz
        success = await blackboard.write(key, value, source_agent, ttl_seconds=1)
        assert success is True

        # Hemen oku - veri olmalı
        read_value = blackboard.read(key, "reader_agent")
        assert read_value == value

        # 2 saniye bekle
        await asyncio.sleep(2)

        # Tekrar oku - veri olmamalı (TTL dolmuş)
        read_value = blackboard.read(key, "reader_agent")
        assert read_value is None

    @pytest.mark.asyncio
    async def test_data_deletion(self, blackboard):
        """Veri silme testi"""
        key = "delete_test_key"
        value = "delete_test_value"
        source_agent = "test_agent"

        # Veri yaz
        await blackboard.write(key, value, source_agent)
        assert blackboard.read(key, "reader_agent") == value

        # Veri sil
        success = await blackboard.delete(key, source_agent)
        assert success is True

        # Veri okunamaz olmalı
        read_value = blackboard.read(key, "reader_agent")
        assert read_value is None

        # Olmayan veriyi silmeye çalış
        success = await blackboard.delete("nonexistent_key", source_agent)
        assert success is False

    def test_agent_subscription(self, blackboard, mock_agents):
        """Agent abonelik testi"""
        agent = mock_agents[0]

        # Agent'ı kaydet
        blackboard.register_agent(agent.agent_id, agent)

        # Agent'ı olaylara abone et
        success = blackboard.subscribe(
            agent_name=agent.agent_id,
            event_types=[EventType.DATA_WRITTEN, EventType.DATA_UPDATED],
            key_patterns=["test_*"],
            priority_filter=Priority.MEDIUM,
        )
        assert success is True
        assert len(blackboard.subscriptions[agent.agent_id]) == 1

        # Kayıtlı olmayan agent'ı abone etmeye çalış
        success = blackboard.subscribe(
            agent_name="nonexistent_agent",
            event_types=[EventType.DATA_WRITTEN],
            key_patterns=["*"],
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_event_notification(self, blackboard, mock_agents):
        """Event bildirim testi"""
        agent = mock_agents[0]

        # Agent'ı kaydet ve abone et
        blackboard.register_agent(agent.agent_id, agent)
        agent.register_to_blackboard(blackboard)

        # Veri yaz (event tetikler)
        key = "notification_test"
        value = "notification_value"
        await blackboard.write(key, value, "other_agent")

        # Kısa bir süre bekle (async notification için)
        await asyncio.sleep(0.1)

        # Agent'ın update aldığını kontrol et
        assert len(agent.received_updates) > 0
        update = agent.received_updates[0]
        assert update["key"] == key
        assert update["value"] == value
        assert update["source_agent"] == "other_agent"

    @pytest.mark.asyncio
    async def test_coordination_request(self, blackboard, mock_agents):
        """Koordinasyon talebi testi"""
        # Agent'ları kaydet
        for agent in mock_agents:
            blackboard.register_agent(agent.agent_id, agent)
            agent.register_to_blackboard(blackboard)

        requester = mock_agents[0]
        target_agents = [agent.agent_id for agent in mock_agents[1:]]

        # Koordinasyon talep et
        result = await blackboard.request_coordination(
            requester_agent=requester.agent_id,
            target_agents=target_agents,
            coordination_type="test_coordination",
            parameters={"test_param": "test_value"},
            timeout_seconds=5,
        )

        assert result["success"] is True
        assert "coordination_id" in result
        assert len(result["responses"]) == len(target_agents)

    @pytest.mark.asyncio
    async def test_coordination_timeout(self, blackboard, mock_agents):
        """Koordinasyon timeout testi"""
        agent = mock_agents[0]
        blackboard.register_agent(agent.agent_id, agent)

        # Yanıt vermeyen agent'a koordinasyon talep et
        result = await blackboard.request_coordination(
            requester_agent="test_requester",
            target_agents=["nonexistent_agent"],
            coordination_type="timeout_test",
            parameters={},
            timeout_seconds=1,  # Kısa timeout
        )

        assert result["success"] is False
        assert result["error"] == "coordination_timeout"

    def test_metrics_collection(self, blackboard):
        """Metrik toplama testi"""
        initial_metrics = blackboard.get_metrics()
        assert "total_writes" in initial_metrics
        assert "total_reads" in initial_metrics
        assert "registered_agents" in initial_metrics

        # Bazı işlemler yap
        blackboard.register_agent("test_agent", Mock())

        updated_metrics = blackboard.get_metrics()
        assert updated_metrics["registered_agents"] == 1

    def test_websocket_connection_management(self, blackboard):
        """WebSocket bağlantı yönetimi testi"""
        mock_websocket = Mock()
        connection_id = "test_connection"

        # Bağlantı ekle
        blackboard.add_websocket_connection(connection_id, mock_websocket)
        assert connection_id in blackboard.websocket_connections

        # Bağlantı kaldır
        blackboard.remove_websocket_connection(connection_id)
        assert connection_id not in blackboard.websocket_connections

    def test_event_history_management(self, blackboard):
        """Event geçmişi yönetimi testi"""
        # Maksimum geçmiş boyutunu küçük ayarla
        blackboard.max_history_size = 3

        # Birkaç event ekle
        for i in range(5):
            event = BlackboardEvent(
                event_id=f"event_{i}",
                event_type=EventType.DATA_WRITTEN,
                key=f"key_{i}",
                value=f"value_{i}",
                source_agent="test_agent",
            )
            blackboard._add_to_history(event)

        # Geçmiş boyutu sınırda kalmalı
        assert len(blackboard.event_history) == 3

        # Son event'ler korunmalı
        assert blackboard.event_history[-1].event_id == "event_4"

    @pytest.mark.asyncio
    async def test_cleanup_expired_data(self, blackboard):
        """Süresi dolmuş veri temizleme testi"""
        # Süresi dolmuş veri ekle
        key = "expired_key"
        value = "expired_value"

        # Manuel olarak süresi dolmuş veri oluştur
        blackboard.blackboard[key] = BlackboardData(
            key=key,
            value=value,
            source_agent="test_agent",
            timestamp=datetime.now(),
            ttl=datetime.now() - timedelta(seconds=1),  # 1 saniye önce dolmuş
        )

        # Temizleme işlemini çalıştır
        await blackboard._cleanup_expired_data()

        # Veri silinmiş olmalı
        assert key not in blackboard.blackboard


class TestAgentSynergyOrchestrator:
    """Agent Sinerji Orkestratörü testleri"""

    @pytest.mark.asyncio
    async def test_visual_learner_synergy(self, synergy_orchestrator):
        """Görsel öğrenci sinerji testi"""
        student_id = "test_student_123"

        # Mock blackboard yanıtları
        with patch.object(
            synergy_orchestrator, "_wait_for_blackboard_data"
        ) as mock_wait:
            mock_wait.side_effect = [
                {
                    "style": "visual",
                    "weak_subject": "matematik",
                    "current_level": "medium",
                },
                {"questions": ["q1", "q2"], "visual_elements": True},
                {"infographic": "math_infographic.png", "accessibility": "enhanced"},
            ]

            result = await synergy_orchestrator.execute_visual_learner_synergy(
                student_id
            )

            assert result.success is True
            assert result.scenario_name == "visual_learner_synergy"
            assert len(result.participating_agents) == 3
            assert result.synergy_score > 0
            assert result.coordination_time_ms > 0

    @pytest.mark.asyncio
    async def test_performance_adaptation_synergy(self, synergy_orchestrator):
        """Performans adaptasyon sinerji testi"""
        student_id = "test_student_456"
        performance_data = {
            "success_rate": 0.45,
            "weak_areas": ["algebra", "geometry"],
            "timestamp": datetime.now(),
        }

        # Mock koordinasyon yanıtı
        with patch.object(
            synergy_orchestrator.blackboard, "request_coordination"
        ) as mock_coord:
            mock_coord.return_value = {
                "success": True,
                "responses": {
                    "learning_path_agent": {
                        "data": {"new_resources": ["resource1", "resource2"]}
                    },
                    "study_buddy_agent": {
                        "data": {"difficulty_adjustment": "decreased"}
                    },
                    "accessibility_agent": {
                        "data": {"simplified_content": "simplified_math.html"}
                    },
                },
            }

            result = await synergy_orchestrator.execute_performance_adaptation_synergy(
                student_id, performance_data
            )

            assert result.success is True
            assert result.scenario_name == "performance_adaptation_synergy"
            assert "new_resources" in result.results
            assert "difficulty_adjustment" in result.results
            assert "simplified_content" in result.results

    @pytest.mark.asyncio
    async def test_exam_preparation_synergy(self, synergy_orchestrator):
        """Sınav hazırlık sinerji testi"""
        student_id = "test_student_789"
        exam_type = "TYT"
        days_until_exam = 7

        # Mock paralel görev yanıtları
        with patch.object(
            synergy_orchestrator, "_request_learning_path_plan"
        ) as mock_plan, patch.object(
            synergy_orchestrator, "_request_intensive_questions"
        ) as mock_questions, patch.object(
            synergy_orchestrator, "_request_exam_accessibility"
        ) as mock_access:
            mock_plan.return_value = {"intensive_plan": "7_day_tyt_plan"}
            mock_questions.return_value = {"question_sets": ["set1", "set2", "set3"]}
            mock_access.return_value = {
                "accessibility_features": ["large_text", "high_contrast"]
            }

            result = await synergy_orchestrator.execute_exam_preparation_synergy(
                student_id, exam_type, days_until_exam
            )

            assert result.success is True
            assert result.scenario_name == "exam_preparation_synergy"
            assert result.results["exam_type"] == exam_type
            assert result.results["days_until_exam"] == days_until_exam

    def test_synergy_score_calculation(self, synergy_orchestrator):
        """Sinerji skoru hesaplama testi"""
        # Tüm agent'lar yanıt verdi, hızlı koordinasyon
        agent_responses = [
            {"success": True, "data": "response1"},
            {"success": True, "data": "response2"},
            {"success": True, "data": "response3"},
        ]
        coordination_time = 800  # 800ms

        score = synergy_orchestrator._calculate_synergy_score(
            agent_responses, coordination_time
        )

        assert score > 80  # Yüksek skor bekleniyor
        assert score <= 100

        # Bazı agent'lar yanıt vermedi, yavaş koordinasyon
        agent_responses = [
            {"success": True, "data": "response1"},
            None,
            {"success": False},
        ]
        coordination_time = 15000  # 15 saniye

        score = synergy_orchestrator._calculate_synergy_score(
            agent_responses, coordination_time
        )

        assert score < 50  # Düşük skor bekleniyor
        assert score >= 0

    def test_synergy_metrics(self, synergy_orchestrator):
        """Sinerji metrikleri testi"""
        # Başlangıçta metrikler boş olmalı
        metrics = synergy_orchestrator.get_synergy_metrics()
        assert metrics["total_scenarios"] == 0
        assert metrics["success_rate"] == 0.0

        # Mock sinerji sonuçları ekle
        synergy_orchestrator.synergy_history = [
            SynergyResult(
                scenario_name="test_scenario_1",
                participating_agents=["agent1", "agent2"],
                coordination_time_ms=1000,
                success=True,
                results={},
                synergy_score=85.5,
            ),
            SynergyResult(
                scenario_name="test_scenario_2",
                participating_agents=["agent1", "agent3"],
                coordination_time_ms=2000,
                success=False,
                results={},
                synergy_score=0.0,
            ),
        ]

        metrics = synergy_orchestrator.get_synergy_metrics()
        assert metrics["total_scenarios"] == 2
        assert metrics["successful_scenarios"] == 1
        assert metrics["success_rate"] == 50.0
        assert metrics["average_synergy_score"] == 42.75
        assert metrics["best_synergy_score"] == 85.5
        assert metrics["fastest_coordination"] == 1000


class TestBaseAgentBlackboardIntegration:
    """BaseAgent blackboard entegrasyonu testleri"""

    def test_agent_blackboard_registration(self, blackboard):
        """Agent blackboard kayıt testi"""
        agent = MockAgent("test_agent", AgentType.LEARNING_PATH)

        # Agent'ı blackboard'a kaydet
        success = agent.register_to_blackboard(blackboard)
        assert success is True
        assert agent.blackboard is blackboard

        # Varsayılan abonelikler kurulmuş olmalı
        assert len(blackboard.subscriptions[agent.agent_id]) > 0

    @pytest.mark.asyncio
    async def test_agent_blackboard_write_read(self, blackboard):
        """Agent blackboard yazma/okuma testi"""
        agent = MockAgent("test_agent", AgentType.STUDY_BUDDY)
        agent.register_to_blackboard(blackboard)

        # Agent blackboard'a veri yazsın
        key = "agent_test_key"
        value = {"agent_data": "test_value"}

        success = await agent.write_to_blackboard(key, value)
        assert success is True

        # Agent blackboard'dan veri okusun
        read_value = agent.read_from_blackboard(key)
        assert read_value == value

    @pytest.mark.asyncio
    async def test_agent_coordination_request(self, blackboard, mock_agents):
        """Agent koordinasyon talebi testi"""
        # Agent'ları kaydet
        for agent in mock_agents:
            agent.register_to_blackboard(blackboard)

        requester = mock_agents[0]
        target_agents = [agent.agent_id for agent in mock_agents[1:]]

        # Agent koordinasyon talep etsin
        result = await requester.request_coordination(
            target_agents=target_agents,
            coordination_type="test_coordination",
            parameters={"test": "value"},
            timeout_seconds=5,
        )

        assert result["success"] is True
        assert len(result["responses"]) == len(target_agents)

    def test_agent_metrics(self, blackboard):
        """Agent metrikleri testi"""
        agent = MockAgent("metrics_test_agent", AgentType.ACCESSIBILITY)
        agent.register_to_blackboard(blackboard)

        metrics = agent.get_agent_metrics()

        assert metrics["agent_id"] == "metrics_test_agent"
        assert metrics["agent_type"] == "accessibility"
        assert metrics["blackboard_connected"] is True
        assert "metrics" in metrics
        assert "last_activity" in metrics


@pytest.mark.asyncio
async def test_integration_full_scenario():
    """Tam entegrasyon senaryosu testi"""
    # Temiz blackboard
    reset_blackboard()
    blackboard = get_blackboard()

    # Mock agent'lar oluştur
    learning_agent = MockAgent("learning_path_agent", AgentType.LEARNING_PATH)
    study_agent = MockAgent("study_buddy_agent", AgentType.STUDY_BUDDY)
    access_agent = MockAgent("accessibility_agent", AgentType.ACCESSIBILITY)

    agents = [learning_agent, study_agent, access_agent]

    # Agent'ları kaydet
    for agent in agents:
        agent.register_to_blackboard(blackboard)

    # Sinerji orkestratörü
    orchestrator = get_synergy_orchestrator()

    # Senaryo 1: Öğrenme stili tespiti
    await blackboard.write(
        "learning_style_result_student123",
        {"style": "visual", "confidence": 0.9},
        "learning_path_agent",
    )

    # Senaryo 2: Koordineli yanıt
    result = await blackboard.request_coordination(
        requester_agent="system",
        target_agents=["learning_path_agent", "study_buddy_agent"],
        coordination_type="content_adaptation",
        parameters={"student_id": "student123", "style": "visual"},
        timeout_seconds=10,
    )

    assert result["success"] is True

    # Senaryo 3: Metrik kontrolü
    metrics = blackboard.get_metrics()
    assert metrics["total_writes"] >= 1
    assert metrics["registered_agents"] == 3
    assert metrics["coordination_requests"] >= 1

    # Temizlik
    blackboard.cleanup()


if __name__ == "__main__":
    # Test'leri çalıştır
    pytest.main([__file__, "-v", "--tb=short"])
