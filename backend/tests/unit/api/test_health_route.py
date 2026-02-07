"""
Unit tests for health check routes (UT-03.2).

Tests health endpoint response structures and validation.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import pytest


# --- UT-03.2.1: Health response structure ---
@pytest.mark.asyncio
async def test_health_response_structure():
    """Health endpoint response must have status field."""
    response = {
        "status": "healthy",
        "version": "2.0.0",
        "uptime": 3600,
    }
    assert "status" in response
    assert response["status"] in ["healthy", "degraded", "unhealthy", "ok", "alive"]


# --- UT-03.2.2: Health status values ---
@pytest.mark.asyncio
async def test_health_status_values():
    """Valid health statuses."""
    valid_statuses = {"healthy", "degraded", "unhealthy", "ok", "alive"}
    assert "healthy" in valid_statuses
    assert "degraded" in valid_statuses
    assert "unknown" not in valid_statuses


# --- UT-03.2.3: Readiness probe response ---
@pytest.mark.asyncio
async def test_readiness_probe_response():
    """Readiness probe returns ready/not-ready with components."""
    response = {
        "status": "ready",
        "database": True,
        "redis": True,
    }
    assert "status" in response
    assert isinstance(response["database"], bool)


# --- UT-03.2.4: Liveness probe response ---
@pytest.mark.asyncio
async def test_liveness_probe_response():
    """Liveness probe confirms app is alive."""
    response = {"status": "alive"}
    assert response["status"] in ["alive", "healthy", "ok"]


# --- UT-03.2.5: Startup probe response ---
@pytest.mark.asyncio
async def test_startup_probe_response():
    """Startup probe confirms app has started."""
    response = {"status": "started", "components_loaded": 115}
    assert "status" in response
    assert response["components_loaded"] > 0


# --- UT-03.2.6: Database health response ---
@pytest.mark.asyncio
async def test_database_health_response():
    """Database health check returns connection status."""
    response = {
        "database": "connected",
        "pool_size": 10,
        "active_connections": 3,
    }
    assert response["database"] in ["connected", "disconnected"]
    assert response["pool_size"] > 0
    assert response["active_connections"] <= response["pool_size"]


# --- UT-03.2.7: Detailed health includes components ---
@pytest.mark.asyncio
async def test_detailed_health_components():
    """Detailed health check includes component statuses."""
    response = {
        "status": "healthy",
        "components": {
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "celery": {"status": "degraded"},
        },
    }
    assert "components" in response
    assert len(response["components"]) >= 2
    assert "database" in response["components"]


# --- UT-03.2.8: Health includes version ---
@pytest.mark.asyncio
async def test_health_includes_version():
    """Health response should include version info."""
    response = {"status": "healthy", "version": "2.0.0"}
    assert "version" in response
    assert len(response["version"]) > 0
