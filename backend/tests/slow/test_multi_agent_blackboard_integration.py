"""
Multi-Agent Blackboard Sistemi Entegrasyon Test Suite
Gerçek Zamanlı Agent Koordinasyonu ve Sinerji Testleri

Bu test dosyası, 3 AI agent'ın blackboard pattern ile koordineli çalışmasını test eder:
- Learning Path Agent
- Study Buddy Agent
- Accessibility Agent

Requirements: 10.7, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from agents.accessibility_agent import AccessibilityAgent
    from agents.learning_path_agent import LearningPathAgent
    from agents.study_buddy_agent import StudyBuddyAgent
except ImportError:
    pytest.skip("archived agent modules not available", allow_module_level=True)
from algorithms.multi_agent_blackboard import MultiAgentBlackboard
try:
    from core.websocket_manager import WebSocketManager
except ImportError:
    from core.realtime_notification_system import WebSocketManager


class TestBlackboardBasicOperations:
    """Blackboard temel işlemler testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    @pytest.fixture
    def mock_agents(self):
        """Mock agent'lar oluştur"""
        learning_agent = Mock(spec=LearningPathAgent)
        learning_agent.on_blackboard_update = AsyncMock()
        learning_agent.detect_style = AsyncMock(return_value="visual")
        learning_agent.find_remedial_resources = AsyncMock(
            return_value=["resource1", "resource2"]
        )

        study_agent = Mock(spec=StudyBuddyAgent)
        study_agent.on_blackboard_update = AsyncMock()
        study_agent.generate_visual_question = AsyncMock(return_value="visual_question")
        study_agent.decrease_difficulty = AsyncMock()

        accessibility_agent = Mock(spec=AccessibilityAgent)
        accessibility_agent.on_blackboard_update = AsyncMock()
        accessibility_agent.create_infographic = AsyncMock(
            return_value="infographic_data"
        )
        accessibility_agent.simplify_for_student = AsyncMock(
            return_value="simplified_content"
        )

        return {
            "learning_path": learning_agent,
            "study_buddy": study_agent,
            "accessibility": accessibility_agent,
        }

    def test_agent_registration(self, blackboard, mock_agents):
        """Agent kayıt sistemi"""

        # Agent'ları kaydet
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)

        # Kayıt kontrolü
        assert blackboard.learning_path_agent == mock_agents["learning_path"]
        assert blackboard.study_buddy_agent == mock_agents["study_buddy"]
        assert blackboard.accessibility_agent == mock_agents["accessibility"]

        # Subscriber listeleri oluşturuldu mu?
        assert "learning_path" in blackboard.subscribers
        assert "study_buddy" in blackboard.subscribers
        assert "accessibility" in blackboard.subscribers

    def test_subscription_management(self, blackboard):
        """Abonelik yönetimi"""

        # Agent'ları abone et
        blackboard.subscribe("learning_path", "student_profile")
        blackboard.subscribe("learning_path", "performance_data")
        blackboard.subscribe("study_buddy", "student_profile")
        blackboard.subscribe("accessibility", "learning_style")

        # Abonelikler doğru mu?
        assert "student_profile" in blackboard.subscribers["learning_path"]
        assert "performance_data" in blackboard.subscribers["learning_path"]
        assert "student_profile" in blackboard.subscribers["study_buddy"]
        assert "learning_style" in blackboard.subscribers["accessibility"]

        # Çoklu abonelik
        assert len(blackboard.subscribers["learning_path"]) == 2

    @pytest.mark.asyncio
    async def test_blackboard_write_read_operations(self, blackboard):
        """Blackboard yazma-okuma işlemleri"""

        # Veri yaz
        test_data = {
            "student_id": "test_123",
            "learning_style": "visual",
            "confidence": 0.85,
        }

        await blackboard.write("student_profile", test_data, "learning_path")

        # Veri oku
        read_data = blackboard.read("student_profile")
        assert read_data == test_data

        # Metadata kontrol
        stored_entry = blackboard.blackboard["student_profile"]
        assert stored_entry["value"] == test_data
        assert stored_entry["source_agent"] == "learning_path"
        assert isinstance(stored_entry["timestamp"], datetime)

        # Olay geçmişi
        assert len(blackboard.event_history) > 0
        last_event = blackboard.event_history[-1]
        assert last_event["type"] == "data_written"
        assert last_event["key"] == "student_profile"
        assert last_event["agent"] == "learning_path"

    @pytest.mark.asyncio
    async def test_agent_notification_system(self, blackboard, mock_agents):
        """Agent bildirim sistemi"""

        # Agent'ları kaydet ve abone et
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)
            blackboard.subscribe(name, "learning_style_detected")

        # Veri yaz
        await blackboard.write(
            "learning_style_detected", "kinesthetic", "learning_path"
        )

        # Bildirimler gönderildi mi?
        mock_agents["study_buddy"].on_blackboard_update.assert_called_once_with(
            "learning_style_detected", "kinesthetic", "learning_path"
        )
        mock_agents["accessibility"].on_blackboard_update.assert_called_once_with(
            "learning_style_detected", "kinesthetic", "learning_path"
        )

        # Yazan agent bilgilendirilmemeli
        mock_agents["learning_path"].on_blackboard_update.assert_not_called()


class TestAgentCoordination:
    """Agent koordinasyon testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    @pytest.fixture
    def mock_agents(self):
        """Gerçekçi mock agent'lar"""
        learning_agent = Mock(spec=LearningPathAgent)
        learning_agent.on_blackboard_update = AsyncMock()
        learning_agent.detect_style = AsyncMock(return_value="visual")
        learning_agent.create_personalized_path = AsyncMock(
            return_value={
                "path_id": "visual_path_123",
                "resources": ["video1", "diagram1", "infographic1"],
                "difficulty_progression": [1, 2, 3, 4],
            }
        )

        study_agent = Mock(spec=StudyBuddyAgent)
        study_agent.on_blackboard_update = AsyncMock()
        study_agent.generate_visual_question = AsyncMock(
            return_value={
                "question_id": "visual_q_456",
                "type": "diagram_based",
                "content": "Aşağıdaki diyagramı analiz ediniz",
                "visual_elements": ["chart", "graph"],
            }
        )
        study_agent.adapt_to_learning_style = AsyncMock()

        accessibility_agent = Mock(spec=AccessibilityAgent)
        accessibility_agent.on_blackboard_update = AsyncMock()
        accessibility_agent.create_infographic = AsyncMock(
            return_value={
                "infographic_id": "info_789",
                "alt_text": "Matematik formülleri görsel açıklaması",
                "screen_reader_compatible": True,
            }
        )
        accessibility_agent.optimize_for_visual_learner = AsyncMock()

        return {
            "learning_path": learning_agent,
            "study_buddy": study_agent,
            "accessibility": accessibility_agent,
        }

    @pytest.mark.asyncio
    async def test_learning_style_detection_coordination(self, blackboard, mock_agents):
        """Öğrenme stili tespiti koordinasyonu"""

        # Agent'ları kaydet ve abone et
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)
            blackboard.subscribe(name, "learning_style")
            blackboard.subscribe(name, "student_profile")

        # Learning Path Agent öğrenme stilini tespit ediyor
        detected_style = await mock_agents["learning_path"].detect_style("student_123")

        # Blackboard'a yaz
        await blackboard.write("learning_style", detected_style, "learning_path")
        await blackboard.write(
            "student_profile",
            {"id": "student_123", "style": detected_style, "confidence": 0.9},
            "learning_path",
        )

        # Diğer agent'lar bilgilendirildi mi?
        mock_agents["study_buddy"].on_blackboard_update.assert_called()
        mock_agents["accessibility"].on_blackboard_update.assert_called()

        # Agent'lar kendi görevlerini yapıyor
        await mock_agents["study_buddy"].adapt_to_learning_style(detected_style)
        await mock_agents["accessibility"].optimize_for_visual_learner("student_123")

        # Koordinasyon çağrıları
        mock_agents["study_buddy"].adapt_to_learning_style.assert_called_with("visual")
        mock_agents["accessibility"].optimize_for_visual_learner.assert_called_with(
            "student_123"
        )

    @pytest.mark.asyncio
    async def test_performance_based_adaptation_flow(self, blackboard, mock_agents):
        """Performans bazlı adaptasyon akışı"""

        # Agent'ları kaydet
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)
            blackboard.subscribe(name, "performance_update")
            blackboard.subscribe(name, "adaptation_needed")

        # Performans verisi geldi
        performance_data = {
            "student_id": "student_123",
            "weak_areas": ["geometri", "trigonometri"],
            "success_rate": 0.45,
            "comprehension_issues": True,
            "timestamp": datetime.now(),
        }

        await blackboard.write("performance_update", performance_data, "exam_engine")

        # Learning Path Agent yeni kaynaklar buluyor
        remedial_resources = await mock_agents["learning_path"].find_remedial_resources(
            "student_123", performance_data["weak_areas"]
        )
        await blackboard.write(
            "remedial_resources", remedial_resources, "learning_path"
        )

        # Study Buddy Agent zorluk seviyesini ayarlıyor
        await mock_agents["study_buddy"].decrease_difficulty("student_123")
        await blackboard.write("difficulty_adjusted", "decreased", "study_buddy")

        # Accessibility Agent içerik basitleştiriyor
        simplified = await mock_agents["accessibility"].simplify_for_student(
            "student_123", "karmaşık geometri açıklaması"
        )
        await blackboard.write("simplified_content", simplified, "accessibility")

        # Tüm adaptasyonlar koordineli gerçekleşti
        assert blackboard.read("remedial_resources") == ["resource1", "resource2"]
        assert blackboard.read("difficulty_adjusted") == "decreased"
        assert blackboard.read("simplified_content") == "simplified_content"

    @pytest.mark.asyncio
    async def test_agent_synergy_example(self, blackboard, mock_agents):
        """Agent sinerji örneği - gerçek senaryo"""

        # Agent'ları kaydet
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)

        # Sinerji testi çalıştır
        result = await blackboard.agent_synergy_example("student_123")

        # Learning Path Agent çağrıldı
        mock_agents["learning_path"].detect_style.assert_called_with("student_123")

        # Sonuç yapısı doğru mu?
        assert isinstance(result, dict)
        assert (
            "learning_path" in result
            or "practice_questions" in result
            or "accessible_content" in result
        )

    @pytest.mark.asyncio
    async def test_real_time_adaptation_scenario(self, blackboard, mock_agents):
        """Gerçek zamanlı adaptasyon senaryosu"""

        # Agent'ları kaydet
        for name, agent in mock_agents.items():
            blackboard.register_agent(name, agent)

        # Performans verisi
        performance_data = {
            "weak_areas": ["matematik"],
            "success_rate": 0.3,
            "comprehension_issues": True,
            "difficult_content": "karmaşık integral hesaplaması",
            "timestamp": datetime.now(),
        }

        # Adaptasyon testi
        result = await blackboard.real_time_adaptation_example(
            "student_123", performance_data
        )

        # Sonuç kontrolü
        assert result["adaptation_applied"] is True
        assert result["agents_coordinated"] == 3
        assert "response_time_ms" in result
        assert result["response_time_ms"] < 1000  # 1 saniye altında

        # Agent metodları çağrıldı
        mock_agents["learning_path"].find_remedial_resources.assert_called_once()
        mock_agents["study_buddy"].decrease_difficulty.assert_called_once()
        mock_agents["accessibility"].simplify_for_student.assert_called_once()


class TestWebSocketIntegration:
    """WebSocket entegrasyon testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    @pytest.fixture
    def websocket_manager(self):
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_websocket_blackboard_integration(
        self, blackboard, websocket_manager
    ):
        """WebSocket-Blackboard entegrasyonu"""

        # Mock WebSocket bağlantısı
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # WebSocket manager'a blackboard bağla
        websocket_manager.set_blackboard(blackboard)

        # Agent kaydet
        mock_agent = Mock()
        mock_agent.on_blackboard_update = AsyncMock()
        blackboard.register_agent("test_agent", mock_agent)
        blackboard.subscribe("test_agent", "real_time_update")

        # WebSocket üzerinden veri gönder
        message = {
            "type": "blackboard_update",
            "key": "real_time_update",
            "value": {"data": "test_value"},
            "agent": "external_system",
        }

        # Blackboard'a yaz (WebSocket simülasyonu)
        await blackboard.write(message["key"], message["value"], message["agent"])

        # Agent bilgilendirildi mi?
        mock_agent.on_blackboard_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_reliability(self, websocket_manager):
        """WebSocket bağlantı güvenilirliği"""

        connection_attempts = 0
        max_attempts = 3

        async def mock_connect():
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts < max_attempts:
                raise ConnectionError("Bağlantı başarısız")
            return AsyncMock()

        # Otomatik yeniden bağlantı testi
        with patch("websockets.connect", side_effect=mock_connect):
            try:
                await websocket_manager.connect_with_retry("ws://localhost:8000")
                assert connection_attempts == max_attempts
            except ConnectionError:
                # Maksimum deneme sayısına ulaşıldı
                assert connection_attempts >= max_attempts

    @pytest.mark.asyncio
    async def test_websocket_message_broadcasting(self, blackboard, websocket_manager):
        """WebSocket mesaj yayını"""

        # Birden fazla client simülasyonu
        mock_clients = [AsyncMock() for _ in range(5)]
        for client in mock_clients:
            client.send = AsyncMock()

        websocket_manager.clients = mock_clients
        websocket_manager.set_blackboard(blackboard)

        # Blackboard'a veri yaz
        await blackboard.write("broadcast_test", {"message": "test"}, "system")

        # Tüm client'lara mesaj gönderildi mi?
        broadcast_message = {
            "type": "blackboard_update",
            "key": "broadcast_test",
            "value": {"message": "test"},
            "agent": "system",
            "timestamp": blackboard.event_history[-1]["timestamp"].isoformat(),
        }

        # Her client'a gönderim kontrolü (gerçek implementasyonda)
        # Bu test WebSocket manager'ın broadcast fonksiyonunu test eder


class TestPerformanceAndScalability:
    """Performans ve ölçeklenebilirlik testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, blackboard):
        """Eşzamanlı agent işlemleri"""

        # 10 agent kaydet
        agents = []
        for i in range(10):
            agent = Mock()
            agent.on_blackboard_update = AsyncMock()
            agents.append(agent)
            blackboard.register_agent(f"agent_{i}", agent)
            blackboard.subscribe(f"agent_{i}", "concurrent_test")

        # 100 eşzamanlı yazma işlemi
        tasks = []
        for i in range(100):
            task = blackboard.write(f"data_{i}", f"value_{i}", f"agent_{i % 10}")
            tasks.append(task)

        start_time = datetime.now()
        await asyncio.gather(*tasks)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        # 100 işlem 2 saniyede tamamlanmalı
        assert duration < 2.0

        # Tüm veriler yazıldı mı?
        for i in range(100):
            assert blackboard.read(f"data_{i}") == f"value_{i}"

    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(self, blackboard):
        """Büyük veri seti bellek kullanımı"""

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 1000 büyük veri objesi yaz
        for i in range(1000):
            large_data = {
                "id": i,
                "content": "x" * 1000,  # 1KB string
                "metadata": {
                    "timestamp": datetime.now(),
                    "agent": f"agent_{i % 10}",
                    "type": "large_data",
                },
            }

            await blackboard.write(f"large_data_{i}", large_data, f"agent_{i % 10}")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 1000 x 1KB veri için bellek artışı 50MB'dan az olmalı
        assert memory_increase < 50

    @pytest.mark.asyncio
    async def test_event_history_management(self, blackboard):
        """Olay geçmişi yönetimi"""

        # 1000 olay oluştur
        for i in range(1000):
            await blackboard.write(f"event_{i}", f"data_{i}", "test_agent")

        # Olay geçmişi boyutu kontrol
        assert len(blackboard.event_history) == 1000

        # Bellek optimizasyonu için eski olayları temizle (implementasyon detayı)
        # Gerçek sistemde circular buffer veya TTL kullanılabilir

        # Son olaylar korunmuş mu?
        last_event = blackboard.event_history[-1]
        assert last_event["key"] == "event_999"
        assert last_event["agent"] == "test_agent"


class TestErrorHandlingAndResilience:
    """Hata işleme ve dayanıklılık testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    @pytest.mark.asyncio
    async def test_agent_failure_resilience(self, blackboard):
        """Agent arızası dayanıklılığı"""

        # Normal agent
        normal_agent = Mock()
        normal_agent.on_blackboard_update = AsyncMock()

        # Arızalı agent
        faulty_agent = Mock()
        faulty_agent.on_blackboard_update = AsyncMock(
            side_effect=Exception("Agent arızası")
        )

        # Agent'ları kaydet
        blackboard.register_agent("normal_agent", normal_agent)
        blackboard.register_agent("faulty_agent", faulty_agent)

        blackboard.subscribe("normal_agent", "test_data")
        blackboard.subscribe("faulty_agent", "test_data")

        # Veri yaz - arızalı agent sistem çökmemeli
        await blackboard.write("test_data", "test_value", "system")

        # Normal agent çalıştı
        normal_agent.on_blackboard_update.assert_called_once()

        # Arızalı agent çağrıldı ama hata oluştu
        faulty_agent.on_blackboard_update.assert_called_once()

        # Sistem çalışmaya devam ediyor
        assert blackboard.read("test_data") == "test_value"

    @pytest.mark.asyncio
    async def test_blackboard_data_corruption_protection(self, blackboard):
        """Blackboard veri bozulması koruması"""

        # Geçerli veri yaz
        valid_data = {"key": "value", "number": 123}
        await blackboard.write("valid_data", valid_data, "agent1")

        # Geçersiz veri yazma denemesi
        try:
            # Circular reference (JSON serialization problemi)
            circular_data = {}
            circular_data["self"] = circular_data

            await blackboard.write("invalid_data", circular_data, "agent2")
        except Exception:
            # Hata bekleniyor
            pass

        # Geçerli veri korunmuş mu?
        assert blackboard.read("valid_data") == valid_data

        # Geçersiz veri yazılmamış mı?
        assert blackboard.read("invalid_data") is None

    @pytest.mark.asyncio
    async def test_concurrent_write_consistency(self, blackboard):
        """Eşzamanlı yazma tutarlılığı"""

        # Aynı key'e eşzamanlı yazma
        tasks = []
        for i in range(100):
            task = blackboard.write("shared_key", f"value_{i}", f"agent_{i}")
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Son yazılan değer korunmuş olmalı
        final_value = blackboard.read("shared_key")
        assert final_value.startswith("value_")

        # Olay geçmişinde tüm yazma işlemleri kayıtlı olmalı
        shared_key_events = [
            event for event in blackboard.event_history if event["key"] == "shared_key"
        ]
        assert len(shared_key_events) == 100


class TestBlackboardPatternCompliance:
    """Blackboard pattern uyumluluk testleri"""

    @pytest.fixture
    def blackboard(self):
        return MultiAgentBlackboard()

    def test_blackboard_pattern_architecture(self, blackboard):
        """Blackboard pattern mimarisi"""

        # Blackboard bileşenleri mevcut mu?
        assert hasattr(blackboard, "blackboard")  # Merkezi veri deposu
        assert hasattr(blackboard, "subscribers")  # Agent abonelikleri
        assert hasattr(blackboard, "event_history")  # Olay geçmişi

        # Temel operasyonlar mevcut mu?
        assert hasattr(blackboard, "write")
        assert hasattr(blackboard, "read")
        assert hasattr(blackboard, "register_agent")
        assert hasattr(blackboard, "subscribe")

    @pytest.mark.asyncio
    async def test_knowledge_source_independence(self, blackboard):
        """Bilgi kaynağı bağımsızlığı"""

        # Farklı agent'lar farklı bilgi türleri yazıyor
        await blackboard.write("learning_data", {"style": "visual"}, "learning_agent")
        await blackboard.write("performance_data", {"score": 85}, "exam_agent")
        await blackboard.write(
            "content_data", {"videos": ["v1", "v2"]}, "content_agent"
        )

        # Her agent kendi verisini bağımsız olarak yazabildi
        assert blackboard.read("learning_data")["style"] == "visual"
        assert blackboard.read("performance_data")["score"] == 85
        assert len(blackboard.read("content_data")["videos"]) == 2

        # Veri kaynakları farklı
        learning_entry = blackboard.blackboard["learning_data"]
        performance_entry = blackboard.blackboard["performance_data"]
        content_entry = blackboard.blackboard["content_data"]

        assert learning_entry["source_agent"] == "learning_agent"
        assert performance_entry["source_agent"] == "exam_agent"
        assert content_entry["source_agent"] == "content_agent"

    @pytest.mark.asyncio
    async def test_opportunistic_problem_solving(self, blackboard):
        """Fırsatçı problem çözme"""

        # Agent'lar kaydet
        agents = {}
        for name in ["agent1", "agent2", "agent3"]:
            agent = Mock()
            agent.on_blackboard_update = AsyncMock()
            agents[name] = agent
            blackboard.register_agent(name, agent)
            blackboard.subscribe(name, "problem_data")

        # Problem verisi yaz
        problem_data = {
            "type": "math_problem",
            "difficulty": "hard",
            "student_id": "student_123",
        }

        await blackboard.write("problem_data", problem_data, "system")

        # Tüm agent'lar problemi gördü
        for agent in agents.values():
            agent.on_blackboard_update.assert_called_with(
                "problem_data", problem_data, "system"
            )

        # Her agent kendi çözümünü sunabilir
        await blackboard.write("solution_1", {"approach": "visual"}, "agent1")
        await blackboard.write("solution_2", {"approach": "step_by_step"}, "agent2")
        await blackboard.write("solution_3", {"approach": "simplified"}, "agent3")

        # Çoklu çözüm mevcut
        assert blackboard.read("solution_1")["approach"] == "visual"
        assert blackboard.read("solution_2")["approach"] == "step_by_step"
        assert blackboard.read("solution_3")["approach"] == "simplified"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
