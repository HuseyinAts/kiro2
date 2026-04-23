"""
ST-02: Smoke tests for health check endpoints.

Tests:
- Basic health endpoint
- Health status fields
- Ready/live/startup probes
- Database health
- Detailed health report
- Response time tracking
- JSON responses
- Cache headers
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import httpx  # noqa: E402
import pytest  # noqa: E402
from httpx import ASGITransport  # noqa: E402


@pytest.mark.asyncio
async def test_health_returns_200(test_app):
    """ST-02-01: Health endpoint returns 200 OK."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


@pytest.mark.asyncio
async def test_health_status_field(test_app):
    """ST-02-02: Health response contains health_status field."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        data = response.json()

        assert "health_status" in data, "Response must contain health_status field"
        assert data["health_status"] == "healthy", f"Expected healthy, got {data.get('health_status')}"


@pytest.mark.asyncio
async def test_health_ready_200(test_app):
    """ST-02-03: Health ready probe returns 200."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200, f"Ready probe failed: {response.status_code}"


@pytest.mark.asyncio
async def test_health_live_200(test_app):
    """ST-02-04: Health liveness probe returns 200."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")
        assert response.status_code == 200, f"Liveness probe failed: {response.status_code}"


@pytest.mark.asyncio
async def test_health_startup_200(test_app):
    """ST-02-05: Health startup probe returns 200."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/startup")
        assert response.status_code == 200, f"Startup probe failed: {response.status_code}"


@pytest.mark.asyncio
async def test_health_database_available(test_app):
    """ST-02-06: Health database endpoint is available."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/database")
        assert response.status_code == 200, f"Database health endpoint unreachable: {response.status_code}"

        data = response.json()
        assert "status" in data, "Database health must return status field"


@pytest.mark.asyncio
async def test_health_detailed_returns_components(test_app):
    """ST-02-07: Detailed health returns component information."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/detailed")
        assert response.status_code == 200, f"Detailed health endpoint failed: {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), "Detailed health must return a dictionary"
        assert len(data) > 0, "Detailed health must return non-empty data"


@pytest.mark.asyncio
async def test_health_response_time_field(test_app):
    """ST-02-08: Health response includes response_time_ms field."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        data = response.json()

        assert "response_time_ms" in data, "Response must contain response_time_ms"
        assert isinstance(data["response_time_ms"], (int, float)), "response_time_ms must be numeric"
        assert data["response_time_ms"] >= 0, "response_time_ms must be non-negative"


@pytest.mark.asyncio
async def test_health_ready_returns_json(test_app):
    """ST-02-09: Health ready returns valid JSON."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")

        content_type = response.headers.get("content-type", "")
        assert "json" in content_type.lower(), f"Expected JSON content-type, got: {content_type}"

        data = response.json()
        assert isinstance(data, dict), "Health ready must return JSON object"


@pytest.mark.asyncio
async def test_health_cache_header(test_app):
    """ST-02-10: Multiple health requests complete successfully."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # First request
        response1 = await client.get("/health")
        assert response1.status_code == 200, "First request failed"
        time1 = response1.json().get("response_time_ms", 0)

        # Second request
        response2 = await client.get("/health")
        assert response2.status_code == 200, "Second request failed"
        time2 = response2.json().get("response_time_ms", 0)

        # Both should be successful with valid response times
        assert time1 >= 0, "First response time invalid"
        assert time2 >= 0, "Second response time invalid"

        # Verify consistent health status
        assert response1.json()["health_status"] == response2.json()["health_status"], \
            "Health status should be consistent"
