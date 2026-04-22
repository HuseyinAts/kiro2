"""`GET /api/v1/live-sessions/health` — `get_db_session_context` mock (DB yok)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.live_session_routes import router as live_router


class _OkDbContext:
    async def __aenter__(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FailDbContext:
    async def __aenter__(self):
        raise OSError("db unavailable")

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def health_client() -> TestClient:
    app = FastAPI()
    app.include_router(live_router)
    return TestClient(app, raise_server_exceptions=True)


@patch("api.live_session_routes.get_db_session_context", return_value=_OkDbContext())
def test_live_sessions_health_ok(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/live-sessions/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "live_sessions"
    assert data["database"] is True


@patch("api.live_session_routes.get_db_session_context", return_value=_FailDbContext())
def test_live_sessions_health_degraded(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/live-sessions/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "degraded"
    assert data["database"] is False
