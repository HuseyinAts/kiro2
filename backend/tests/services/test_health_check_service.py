"""
Health Check Service Tests
Learning Path Video Yükleme Sorunu Çözümü - Task 4

Unit tests for HealthCheckService
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from services.health_check_service import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_check_service,
)


class TestHealthCheckService:
    """HealthCheckService test suite"""

    @pytest.fixture
    def mock_youtube_api(self):
        """Mock YouTube API"""
        api = Mock()
        api.api_key = "test-api-key"
        return api

    @pytest.fixture
    def mock_cache_service(self):
        """Mock Cache Service"""
        cache = Mock()
        cache.async_client = AsyncMock()
        cache.sync_client = Mock()
        cache._make_key = Mock(side_effect=lambda k: f"test:{k}")
        cache._deserialize = Mock(return_value={})
        return cache

    @pytest.fixture
    def health_service(self, mock_youtube_api, mock_cache_service):
        """Health check service instance"""
        return HealthCheckService(
            youtube_api=mock_youtube_api, cache_service=mock_cache_service
        )

    @pytest.mark.asyncio
    async def test_check_youtube_api_healthy(self, health_service, mock_youtube_api):
        """Test YouTube API health check - healthy"""
        # Arrange
        mock_youtube_api.api_key = "valid-api-key"

        # Act
        result = await health_service._check_youtube_api()

        # Assert
        assert result.name == "YouTube API"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms >= 0
        assert result.error_message is None
        assert result.details["api_key_configured"] is True

    @pytest.mark.asyncio
    async def test_check_youtube_api_degraded(self, health_service, mock_youtube_api):
        """Test YouTube API health check - degraded (test mode)"""
        # Arrange
        mock_youtube_api.api_key = "test-youtube-api-key"

        # Act
        result = await health_service._check_youtube_api()

        # Assert
        assert result.name == "YouTube API"
        assert result.status == HealthStatus.DEGRADED
        assert result.error_message is not None
        assert "test mode" in result.error_message.lower()
        assert result.details["test_mode"] is True

    @pytest.mark.asyncio
    async def test_check_youtube_api_unhealthy(self, health_service, mock_youtube_api):
        """Test YouTube API health check - unhealthy"""
        # Arrange
        mock_youtube_api.api_key = None

        # Act
        result = await health_service._check_youtube_api()

        # Assert
        assert result.name == "YouTube API"
        assert result.status == HealthStatus.DEGRADED  # No key = degraded

    @pytest.mark.asyncio
    async def test_check_database_healthy(self, health_service):
        """Test database health check - healthy"""
        # Arrange
        with patch("services.health_check_service.db_manager") as mock_db:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_db.async_session_factory.return_value = mock_session
            mock_db.async_engine.url = "postgresql://test"

            # Act
            result = await health_service._check_database()

            # Assert
            assert result.name == "Database"
            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms >= 0
            assert result.error_message is None

    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self, health_service):
        """Test database health check - unhealthy"""
        # Arrange
        with patch("services.health_check_service.db_manager") as mock_db:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_db.async_session_factory.return_value = mock_session

            # Act
            result = await health_service._check_database()

            # Assert
            assert result.name == "Database"
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error_message is not None
            assert "Connection failed" in result.error_message

    @pytest.mark.asyncio
    async def test_check_cache_healthy(self, health_service, mock_cache_service):
        """Test cache health check - healthy"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.info = AsyncMock(
            return_value={
                "connected_clients": 5,
                "used_memory_human": "1.5M",
                "uptime_in_seconds": 3600,
            }
        )
        mock_cache_service.async_client = mock_client

        # Act
        result = await health_service._check_cache()

        # Assert
        assert result.name == "Redis Cache"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms >= 0
        assert result.error_message is None
        assert result.details["connected_clients"] == 5

    @pytest.mark.asyncio
    async def test_check_cache_unhealthy(self, health_service, mock_cache_service):
        """Test cache health check - unhealthy"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_cache_service.async_client = mock_client

        # Act
        result = await health_service._check_cache()

        # Assert
        assert result.name == "Redis Cache"
        assert result.status == HealthStatus.UNHEALTHY
        assert result.error_message is not None
        assert "Redis connection failed" in result.error_message

    def test_determine_overall_status_healthy(self, health_service):
        """Test overall status determination - all healthy"""
        # Arrange
        components = [
            ComponentHealth("API", HealthStatus.HEALTHY, 10.0),
            ComponentHealth("DB", HealthStatus.HEALTHY, 20.0),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        # Act
        result = health_service._determine_overall_status(components)

        # Assert
        assert result == HealthStatus.HEALTHY

    def test_determine_overall_status_degraded(self, health_service):
        """Test overall status determination - one degraded"""
        # Arrange
        components = [
            ComponentHealth("API", HealthStatus.DEGRADED, 10.0),
            ComponentHealth("DB", HealthStatus.HEALTHY, 20.0),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        # Act
        result = health_service._determine_overall_status(components)

        # Assert
        assert result == HealthStatus.DEGRADED

    def test_determine_overall_status_unhealthy(self, health_service):
        """Test overall status determination - one unhealthy"""
        # Arrange
        components = [
            ComponentHealth("API", HealthStatus.HEALTHY, 10.0),
            ComponentHealth(
                "DB", HealthStatus.UNHEALTHY, 20.0, error_message="DB down"
            ),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        # Act
        result = health_service._determine_overall_status(components)

        # Assert
        assert result == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_collect_metrics(self, health_service, mock_cache_service):
        """Test metrics collection"""
        # Arrange
        mock_cache_service.sync_client.get = Mock(return_value=None)

        # Act
        result = await health_service._collect_metrics()

        # Assert
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert "total_requests_24h" in result
        assert "success_rate_24h" in result
        assert "cache_hit_rate_1h" in result

    @pytest.mark.asyncio
    async def test_check_health_full(self, health_service, mock_cache_service):
        """Test full health check"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.info = AsyncMock(return_value={})
        mock_cache_service.async_client = mock_client
        mock_cache_service.sync_client.get = Mock(return_value=None)

        with patch("services.health_check_service.db_manager") as mock_db:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_db.async_session_factory.return_value = mock_session
            mock_db.async_engine.url = "postgresql://test"

            # Act
            result = await health_service.check_health()

            # Assert
            assert isinstance(result, SystemHealth)
            assert result.overall_status in [
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthStatus.UNHEALTHY,
            ]
            assert len(result.components) == 3
            assert result.metrics is not None
            assert result.timestamp is not None

    def test_component_health_to_dict(self):
        """Test ComponentHealth to_dict"""
        # Arrange
        component = ComponentHealth(
            name="Test",
            status=HealthStatus.HEALTHY,
            response_time_ms=15.5,
            error_message=None,
            last_check=datetime(2025, 1, 1, 12, 0, 0),
            details={"key": "value"},
        )

        # Act
        result = component.to_dict()

        # Assert
        assert result["name"] == "Test"
        assert result["status"] == "healthy"
        assert result["response_time_ms"] == 15.5
        assert result["error_message"] is None
        assert result["last_check"] == "2025-01-01T12:00:00"
        assert result["details"]["key"] == "value"

    def test_system_health_to_dict(self):
        """Test SystemHealth to_dict"""
        # Arrange
        components = [ComponentHealth("API", HealthStatus.HEALTHY, 10.0)]
        system_health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components=components,
            metrics={"test": 123},
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        # Act
        result = system_health.to_dict()

        # Assert
        assert result["overall_status"] == "healthy"
        assert len(result["components"]) == 1
        assert result["metrics"]["test"] == 123
        assert result["timestamp"] == "2025-01-01T12:00:00"

    def test_get_health_check_service_singleton(self):
        """Test singleton pattern"""
        # Act
        service1 = get_health_check_service()
        service2 = get_health_check_service()

        # Assert
        assert service1 is service2
