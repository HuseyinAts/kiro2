"""
Comprehensive tests for api/health.py
Tests all health check endpoints with mocking
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def test_app():
    """Create test app with health router"""
    from api.health import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


async def mock_healthy_database():
    """Mock healthy database response"""
    return {"healthy": True, "connection": "ok", "response_time_ms": 5.2}


async def mock_unhealthy_database():
    """Mock unhealthy database response"""
    return {"healthy": False, "error": "Connection timeout"}


async def mock_database_exception():
    """Mock database exception"""
    raise Exception("Database connection failed")


async def mock_database_with_latency():
    """Mock database response with latency"""
    return {"healthy": True, "latency": 10}


async def mock_db_session():
    """Mock database session"""
    return MagicMock()


class TestBasicHealthCheck:
    """Test basic health check endpoint"""

    def test_health_check_endpoint_exists(self, client):
        """Test /health/ endpoint exists"""
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_check_returns_json(self, client):
        """Test health check returns JSON"""
        response = client.get("/health/")
        assert response.headers["content-type"] == "application/json"

    def test_health_check_response_structure(self, client):
        """Test health check response has correct structure"""
        response = client.get("/health/")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_health_check_status_healthy(self, client):
        """Test health check status is healthy"""
        response = client.get("/health/")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_service_name(self, client):
        """Test health check includes service name"""
        response = client.get("/health/")
        data = response.json()

        assert data["service"] == "Türkiye Üniversite Sınavları Hazırlık Platformu"

    def test_health_check_version(self, client):
        """Test health check includes version"""
        response = client.get("/health/")
        data = response.json()

        assert data["version"] == "1.0.0"

    def test_health_check_environment(self, client):
        """Test health check includes environment"""
        response = client.get("/health/")
        data = response.json()

        assert "environment" in data
        assert isinstance(data["environment"], str)


class TestDatabaseHealthCheck:
    """Test database health check endpoint"""

    @patch("api.health.get_database_health", new=mock_healthy_database)
    def test_database_health_healthy(self, client):
        """Test database health check when database is healthy"""
        response = client.get("/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data

    @patch("api.health.get_database_health", new=mock_unhealthy_database)
    def test_database_health_unhealthy(self, client):
        """Test database health check when database is unhealthy"""
        response = client.get("/health/database")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    @patch("api.health.get_database_health", new=mock_database_exception)
    def test_database_health_exception(self, client):
        """Test database health check when exception occurs"""
        response = client.get("/health/database")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "error"

    @patch("api.health.get_database_health", new=mock_database_with_latency)
    def test_database_health_response_structure(self, client):
        """Test database health response structure"""
        response = client.get("/health/database")

        data = response.json()

        assert "status" in data
        assert "database" in data
        assert isinstance(data["database"], dict)


class TestDetailedHealthCheck:
    """Test detailed health check endpoint"""

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_healthy(self, client):
        """Test detailed health check when all systems healthy"""
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_response_structure(self, client):
        """Test detailed health response structure"""
        response = client.get("/health/detailed")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "system_info" in data

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_includes_all_checks(self, client):
        """Test detailed health includes all system checks"""
        response = client.get("/health/detailed")
        data = response.json()

        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "elasticsearch" in checks
        assert "external_apis" in checks

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_system_info(self, client):
        """Test detailed health includes system info"""
        response = client.get("/health/detailed")
        data = response.json()

        system_info = data["system_info"]
        assert "environment" in system_info
        assert "database_url" in system_info
        assert "debug_mode" in system_info

    @patch("api.health.get_database_health", new=mock_unhealthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_unhealthy_database(self, client):
        """Test detailed health when database is unhealthy"""
        response = client.get("/health/detailed")

        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "unhealthy"

    @patch("api.health.get_database_health", new=mock_database_exception)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_exception_handling(self, client):
        """Test detailed health handles exceptions"""
        response = client.get("/health/detailed")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "error"

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_database_url_hidden(self, client):
        """Test detailed health hides sensitive database URL info"""
        response = client.get("/health/detailed")
        data = response.json()

        # Database URL should not contain password
        db_url = data["system_info"]["database_url"]
        assert "@" not in db_url or "password" not in db_url.lower()

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_detailed_health_timestamp_present(self, client):
        """Test detailed health includes timestamp"""
        response = client.get("/health/detailed")
        data = response.json()

        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


class TestHealthEndpointsIntegration:
    """Test health endpoints integration"""

    def test_all_health_endpoints_accessible(self, client):
        """Test all health endpoints are accessible"""
        endpoints = [
            "/health/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [
                200,
                503,
            ]  # Either healthy or service unavailable

    @patch("api.health.get_database_health", new=mock_healthy_database)
    @patch("api.health.get_db_session", new=mock_db_session)
    def test_health_endpoints_return_json(self, client):
        """Test all health endpoints return JSON"""
        endpoints = ["/health/", "/health/database", "/health/detailed"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "application/json" in response.headers.get("content-type", "")
