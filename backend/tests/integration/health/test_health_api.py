"""
Integration Tests - Health Dashboard API

Bu modul, health dashboard API endpoint'leri icin integration testler icerir.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# conftest.py handles sys.path setup
from app.health.dashboard_api import router as health_router


# Test app
def create_test_app():
    """Test icin FastAPI uygulamasi olusturur."""
    app = FastAPI()
    # Router zaten /api/v1/health prefix'ine sahip, ek prefix ekleme
    app.include_router(health_router)
    return app


@pytest.fixture
def app():
    """Test app fixture."""
    return create_test_app()


@pytest.fixture
async def client(app):
    """Async test client fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthDashboardAPI:
    """Health Dashboard API integration testleri."""

    @pytest.mark.asyncio
    async def test_get_endpoints_list(self, client):
        """Test: /endpoints listesi alinabilmeli."""
        response = await client.get("/api/v1/health/endpoints")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_metrics_overview(self, client):
        """Test: /metrics overview alinabilmeli."""
        response = await client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_endpoints" in data
        assert "healthy_count" in data
        assert "unhealthy_count" in data

    @pytest.mark.asyncio
    async def test_get_sla_report(self, client):
        """Test: /sla-report alinabilmeli."""
        response = await client.get("/api/v1/health/sla-report")

        assert response.status_code == 200
        data = response.json()
        assert "sla_compliance_rate" in data
        assert "period_start" in data
        assert "period_end" in data

    @pytest.mark.asyncio
    async def test_get_health_history_default(self, client):
        """Test: /history endpoint parametresi ile calisabilmeli."""
        response = await client.get("/api/v1/health/history?endpoint=/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert "endpoint" in data
        assert "data_points" in data
        assert "trend" in data

    @pytest.mark.asyncio
    async def test_get_health_history_with_days(self, client):
        """Test: /history days parametresi ile calisabilmeli."""
        response = await client.get("/api/v1/health/history?endpoint=/api/v1/users&days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_alerts_list(self, client):
        """Test: /alerts listesi alinabilmeli."""
        response = await client.get("/api/v1/health/alerts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestHealthDashboardMetrics:
    """Health Dashboard metrics testleri."""

    @pytest.mark.asyncio
    async def test_metrics_structure(self, client):
        """Test: Metrics yapisinda gerekli alanlar olmali."""
        response = await client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "total_endpoints",
            "healthy_count",
            "unhealthy_count",
            "degraded_count",
            "average_score",
            "average_response_time_ms",
            "overall_error_rate",
            "overall_uptime",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_health_percentage_bounds(self, client):
        """Test: Average score 0-100 arasinda olmali."""
        response = await client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        data = response.json()

        score = data.get("average_score", 0)
        assert 0 <= score <= 100


class TestHealthDashboardSLA:
    """Health Dashboard SLA testleri."""

    @pytest.mark.asyncio
    async def test_sla_report_structure(self, client):
        """Test: SLA report yapisinda gerekli alanlar olmali."""
        response = await client.get("/api/v1/health/sla-report")

        assert response.status_code == 200
        data = response.json()

        assert "sla_compliance_rate" in data
        assert "total_endpoints" in data
        assert "period_start" in data
        assert "period_end" in data

    @pytest.mark.asyncio
    async def test_sla_compliance_bounds(self, client):
        """Test: SLA compliance 0-100 arasinda olmali."""
        response = await client.get("/api/v1/health/sla-report")

        assert response.status_code == 200
        data = response.json()

        compliance = data.get("sla_compliance_rate", 0)
        assert 0 <= compliance <= 100


class TestHealthDashboardErrors:
    """Health Dashboard hata senaryolari testleri."""

    @pytest.mark.asyncio
    async def test_history_invalid_days(self, client):
        """Test: Gecersiz days parametresi hata vermeli."""
        response = await client.get("/api/v1/health/history?endpoint=/api/v1/users&days=-1")

        # FastAPI validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, client):
        """Test: Var olmayan endpoint 404 donmeli."""
        response = await client.get("/api/v1/health/nonexistent")

        assert response.status_code == 404
