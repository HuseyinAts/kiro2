"""
Comprehensive tests for api/monitoring.py
Tests monitoring API endpoints - Clean rewrite
"""
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth_dependencies import authenticate_user
from core.dependencies import AuthenticatedUser
from models.enums_db import UserRole


async def _monitoring_test_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="monitor-test-admin",
        username="monitor_admin",
        role=UserRole.ADMIN,
        email=None,
        permissions=["*"],
        exp=None,
    )

from core.auth_dependencies import authenticate_user
from core.dependencies import AuthenticatedUser
from models.enums_db import UserRole


async def _monitoring_test_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="monitor-test-admin",
        username="monitor_admin",
        role=UserRole.ADMIN,
        email=None,
        permissions=["*"],
        exp=None,
    )


# Mock missing modules before importing
@pytest.fixture(scope="module", autouse=True)
def setup_mocks():
    """Setup global mocks for missing modules"""
    # Mock performance_monitor module
    mock_monitor = MagicMock()
    mock_monitor.is_monitoring = False
    mock_monitor.get_api_performance_summary.return_value = {}
    mock_monitor.get_db_performance_summary.return_value = {}
    mock_monitor.get_system_performance_summary.return_value = {}
    mock_monitor.export_metrics_to_prometheus.return_value = "# metrics"
    mock_monitor.start_monitoring = AsyncMock()
    mock_monitor.stop_monitoring = AsyncMock()

    sys.modules["core.performance_monitor"] = MagicMock(
        performance_monitor=mock_monitor
    )

    # RBAC: test kullanıcısı gerçek DB rol kaydı olmadan admin uçlarına erişsin
    from core.rbac_system import AuthorizationResult, get_rbac_manager

    _rbac = get_rbac_manager()
    _rbac_orig_check = _rbac.check_permission
    _rbac.check_permission = AsyncMock(
        return_value=AuthorizationResult(granted=True, reason="test_allow")
    )

    yield

    _rbac.check_permission = _rbac_orig_check


@pytest.fixture
def test_app():
    """Create test app with monitoring router"""
    from api.monitoring import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[authenticate_user] = _monitoring_test_user
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


# Health Check Tests
class TestHealthEndpoint:
    """Test /api/v1/monitoring/health endpoint"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    @patch("api.monitoring.get_db_session")
    def test_health_check_success(self, mock_db, mock_monitor, mock_logger, client):
        """Test basic health check"""
        # Mock database
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.execute = AsyncMock()
        mock_db.return_value = mock_session
        mock_monitor.is_monitoring = True

        response = client.get("/api/v1/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    @patch("api.monitoring.get_db_session")
    def test_health_check_structure(self, mock_db, mock_monitor, mock_logger, client):
        """Test health check response structure"""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.execute = AsyncMock()
        mock_db.return_value = mock_session
        mock_monitor.is_monitoring = True

        response = client.get("/api/v1/monitoring/health")
        data = response.json()

        assert "status" in data["data"]
        assert "timestamp" in data["data"]
        assert "version" in data["data"]
        assert "services" in data["data"]


# Performance Endpoint Tests
class TestPerformanceEndpoints:
    """Test performance monitoring endpoints"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_api_performance(self, mock_monitor, mock_logger, client):
        """Test API performance endpoint"""
        mock_monitor.get_api_performance_summary.return_value = {
            "avg_response_time_ms": 150.5
        }

        response = client.get("/api/v1/monitoring/performance/api")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_database_performance(self, mock_monitor, mock_logger, client):
        """Test database performance endpoint"""
        mock_monitor.get_db_performance_summary.return_value = {
            "avg_execution_time_ms": 50.2
        }

        response = client.get("/api/v1/monitoring/performance/database")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_system_performance(self, mock_monitor, mock_logger, client):
        """Test system performance endpoint"""
        mock_monitor.get_system_performance_summary.return_value = {
            "cpu": {"avg_percent": 45.0}
        }

        response = client.get("/api/v1/monitoring/performance/system")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_performance_summary(self, mock_monitor, mock_logger, client):
        """Test comprehensive performance summary"""
        mock_monitor.get_api_performance_summary.return_value = {}
        mock_monitor.get_db_performance_summary.return_value = {}
        mock_monitor.get_system_performance_summary.return_value = {}

        response = client.get("/api/v1/monitoring/performance/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_performance" in data["data"]
        assert "database_performance" in data["data"]
        assert "system_performance" in data["data"]


# Prometheus Metrics Tests
class TestPrometheusMetrics:
    """Test Prometheus metrics endpoint"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_prometheus_metrics(self, mock_monitor, mock_logger, client):
        """Test Prometheus metrics export"""
        mock_monitor.export_metrics_to_prometheus.return_value = (
            "# metrics\nmetric_name 100"
        )

        response = client.get("/api/v1/monitoring/metrics/prometheus")

        assert response.status_code == 200
        assert "metric_name" in response.text


# Bottlenecks Detection Tests
class TestBottlenecksDetection:
    """Test bottleneck detection endpoint"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_no_bottlenecks(self, mock_monitor, mock_logger, client):
        """Test when no bottlenecks detected"""
        mock_monitor.get_api_performance_summary.return_value = {
            "avg_response_time_ms": 100
        }
        mock_monitor.get_db_performance_summary.return_value = {
            "avg_execution_time_ms": 50
        }
        mock_monitor.get_system_performance_summary.return_value = {
            "cpu": {"avg_percent": 30},
            "memory": {"avg_percent": 40},
        }

        response = client.get("/api/v1/monitoring/bottlenecks")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["bottlenecks"]) == 0

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_api_bottleneck(self, mock_monitor, mock_logger, client):
        """Test API bottleneck detection"""
        mock_monitor.get_api_performance_summary.return_value = {
            "avg_response_time_ms": 1500
        }
        mock_monitor.get_db_performance_summary.return_value = {
            "avg_execution_time_ms": 50
        }
        mock_monitor.get_system_performance_summary.return_value = {
            "cpu": {"avg_percent": 30},
            "memory": {"avg_percent": 40},
        }

        response = client.get("/api/v1/monitoring/bottlenecks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["bottlenecks"]) > 0
        assert any(b["type"] == "api_performance" for b in data["data"]["bottlenecks"])

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_cpu_bottleneck(self, mock_monitor, mock_logger, client):
        """Test CPU bottleneck detection"""
        mock_monitor.get_api_performance_summary.return_value = {
            "avg_response_time_ms": 100
        }
        mock_monitor.get_db_performance_summary.return_value = {
            "avg_execution_time_ms": 50
        }
        mock_monitor.get_system_performance_summary.return_value = {
            "cpu": {"avg_percent": 90},
            "memory": {"avg_percent": 40},
        }

        response = client.get("/api/v1/monitoring/bottlenecks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["bottlenecks"]) > 0
        assert any(b["type"] == "cpu_usage" for b in data["data"]["bottlenecks"])


# Monitoring Control Tests
class TestMonitoringControl:
    """Test monitoring start/stop endpoints"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_start_monitoring(self, mock_monitor, mock_logger, client):
        """Test starting monitoring"""
        mock_monitor.is_monitoring = False
        mock_monitor.start_monitoring = AsyncMock()

        response = client.post("/api/v1/monitoring/monitoring/start")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_start_monitoring_already_running(self, mock_monitor, mock_logger, client):
        """Test starting when already running"""
        mock_monitor.is_monitoring = True

        response = client.post("/api/v1/monitoring/monitoring/start")

        assert response.status_code == 200
        data = response.json()
        assert "already running" in data["message"]

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_stop_monitoring(self, mock_monitor, mock_logger, client):
        """Test stopping monitoring"""
        mock_monitor.is_monitoring = True
        mock_monitor.stop_monitoring = AsyncMock()

        response = client.post("/api/v1/monitoring/monitoring/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_stop_monitoring_not_running(self, mock_monitor, mock_logger, client):
        """Test stopping when not running"""
        mock_monitor.is_monitoring = False

        response = client.post("/api/v1/monitoring/monitoring/stop")

        assert response.status_code == 200
        data = response.json()
        assert "not running" in data["message"]


# Query Parameter Validation Tests
class TestQueryValidation:
    """Test query parameter validation"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_hours_minimum_validation(self, mock_monitor, mock_logger, client):
        """Test hours parameter minimum"""
        response = client.get("/api/v1/monitoring/performance/api?hours=0")
        assert response.status_code == 422

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_hours_maximum_validation(self, mock_monitor, mock_logger, client):
        """Test hours parameter maximum"""
        response = client.get("/api/v1/monitoring/performance/api?hours=25")
        assert response.status_code == 422

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_hours_valid_range(self, mock_monitor, mock_logger, client):
        """Test valid hours parameter"""
        mock_monitor.get_api_performance_summary.return_value = {}

        response = client.get("/api/v1/monitoring/performance/api?hours=12")
        assert response.status_code == 200


# Error Handling Tests
class TestErrorHandling:
    """Test error handling"""

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_api_performance_error(self, mock_monitor, mock_logger, client):
        """Test API performance error handling"""
        mock_monitor.get_api_performance_summary.side_effect = Exception("Error")

        response = client.get("/api/v1/monitoring/performance/api")

        assert response.status_code == 500

    @patch("api.monitoring.logger")
    @patch("api.monitoring.performance_monitor")
    def test_system_performance_error(self, mock_monitor, mock_logger, client):
        """Test system performance error handling"""
        mock_monitor.get_system_performance_summary.side_effect = Exception("Error")

        response = client.get("/api/v1/monitoring/performance/system")

        assert response.status_code == 500
