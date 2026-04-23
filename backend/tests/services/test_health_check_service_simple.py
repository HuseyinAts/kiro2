"""
Simple Health Check Service Tests
Learning Path Video Yükleme Sorunu Çözümü - Task 4

Simple unit tests that don't require full database setup
"""

from datetime import datetime

import pytest

from services.health_check_service import ComponentHealth, HealthStatus, SystemHealth


class TestComponentHealth:
    """ComponentHealth tests"""

    def test_component_health_creation(self):
        """Test ComponentHealth creation"""
        component = ComponentHealth(
            name="Test Component", status=HealthStatus.HEALTHY, response_time_ms=15.5
        )

        assert component.name == "Test Component"
        assert component.status == HealthStatus.HEALTHY
        assert component.response_time_ms == 15.5
        assert component.error_message is None
        assert component.last_check is None
        assert component.details is None

    def test_component_health_to_dict(self):
        """Test ComponentHealth to_dict"""
        component = ComponentHealth(
            name="Test",
            status=HealthStatus.HEALTHY,
            response_time_ms=15.5,
            error_message=None,
            last_check=datetime(2025, 1, 1, 12, 0, 0),
            details={"key": "value"},
        )

        result = component.to_dict()

        assert result["name"] == "Test"
        assert result["status"] == "healthy"
        assert result["response_time_ms"] == 15.5
        assert result["error_message"] is None
        assert result["last_check"] == "2025-01-01T12:00:00"
        assert result["details"]["key"] == "value"

    def test_component_health_to_dict_with_error(self):
        """Test ComponentHealth to_dict with error"""
        component = ComponentHealth(
            name="Failed Component",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=100.0,
            error_message="Connection failed",
            last_check=datetime(2025, 1, 1, 12, 0, 0),
        )

        result = component.to_dict()

        assert result["name"] == "Failed Component"
        assert result["status"] == "unhealthy"
        assert result["error_message"] == "Connection failed"


class TestSystemHealth:
    """SystemHealth tests"""

    def test_system_health_creation(self):
        """Test SystemHealth creation"""
        components = [
            ComponentHealth("API", HealthStatus.HEALTHY, 10.0),
            ComponentHealth("DB", HealthStatus.HEALTHY, 20.0),
        ]

        system_health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components=components,
            metrics={"test": 123},
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        assert system_health.overall_status == HealthStatus.HEALTHY
        assert len(system_health.components) == 2
        assert system_health.metrics["test"] == 123

    def test_system_health_to_dict(self):
        """Test SystemHealth to_dict"""
        components = [ComponentHealth("API", HealthStatus.HEALTHY, 10.0)]
        system_health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components=components,
            metrics={"test": 123},
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        result = system_health.to_dict()

        assert result["overall_status"] == "healthy"
        assert len(result["components"]) == 1
        assert result["metrics"]["test"] == 123
        assert result["timestamp"] == "2025-01-01T12:00:00"


class TestHealthStatus:
    """HealthStatus enum tests"""

    def test_health_status_values(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_comparison(self):
        """Test HealthStatus comparison"""
        assert HealthStatus.HEALTHY == HealthStatus.HEALTHY
        assert HealthStatus.HEALTHY != HealthStatus.DEGRADED
        assert HealthStatus.DEGRADED != HealthStatus.UNHEALTHY


class TestHealthCheckServiceLogic:
    """Test HealthCheckService logic without external dependencies"""

    def test_determine_overall_status_all_healthy(self):
        """Test overall status - all healthy"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()
        components = [
            ComponentHealth("API", HealthStatus.HEALTHY, 10.0),
            ComponentHealth("DB", HealthStatus.HEALTHY, 20.0),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        result = service._determine_overall_status(components)

        assert result == HealthStatus.HEALTHY

    def test_determine_overall_status_one_degraded(self):
        """Test overall status - one degraded"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()
        components = [
            ComponentHealth("API", HealthStatus.DEGRADED, 10.0),
            ComponentHealth("DB", HealthStatus.HEALTHY, 20.0),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        result = service._determine_overall_status(components)

        assert result == HealthStatus.DEGRADED

    def test_determine_overall_status_one_unhealthy(self):
        """Test overall status - one unhealthy"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()
        components = [
            ComponentHealth("API", HealthStatus.HEALTHY, 10.0),
            ComponentHealth(
                "DB", HealthStatus.UNHEALTHY, 20.0, error_message="DB down"
            ),
            ComponentHealth("Cache", HealthStatus.HEALTHY, 5.0),
        ]

        result = service._determine_overall_status(components)

        assert result == HealthStatus.UNHEALTHY

    def test_determine_overall_status_multiple_issues(self):
        """Test overall status - multiple issues (unhealthy takes precedence)"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()
        components = [
            ComponentHealth("API", HealthStatus.DEGRADED, 10.0),
            ComponentHealth(
                "DB", HealthStatus.UNHEALTHY, 20.0, error_message="DB down"
            ),
            ComponentHealth("Cache", HealthStatus.DEGRADED, 5.0),
        ]

        result = service._determine_overall_status(components)

        assert result == HealthStatus.UNHEALTHY

    def test_get_uptime_seconds(self):
        """Test uptime calculation"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()
        uptime = service._get_uptime_seconds()

        # Should return a non-negative integer
        assert isinstance(uptime, int)
        assert uptime >= 0


class TestHealthCheckServiceSingleton:
    """Test singleton pattern"""

    def test_get_health_check_service_singleton(self):
        """Test that get_health_check_service returns same instance"""
        # Reset singleton for test
        import services.health_check_service as hcs_module
        from services.health_check_service import get_health_check_service

        hcs_module._health_check_service = None

        service1 = get_health_check_service()
        service2 = get_health_check_service()

        assert service1 is service2

    def test_health_check_service_lazy_init(self):
        """Test lazy initialization of dependencies"""
        from services.health_check_service import HealthCheckService

        service = HealthCheckService()

        # Dependencies should be None initially
        assert service._youtube_api is None
        assert service._cache_service is None

        # Accessing properties should initialize them
        youtube_api = service.youtube_api
        assert youtube_api is not None

        cache_service = service.cache_service
        assert cache_service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
