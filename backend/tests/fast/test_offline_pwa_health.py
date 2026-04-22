"""
Hızlı testler: J6 `GET /api/v1/offline/health`, J7 `GET /api/v1/sync/health` (DB ping).
DB gerçek bağlantısı yok; `get_db_session_context` mock.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.offline_sync_api import router as offline_router
from api.pwa_sync_api import router as pwa_combined_router


class _OkDbContext:
    """Async context manager: başarılı `db.execute`"""

    async def __aenter__(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FailDbContext:
    """Async context manager: açılışta hata (degraded yolu)"""

    async def __aenter__(self):
        raise OSError("db unavailable")

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def health_client() -> TestClient:
    app = FastAPI()
    app.include_router(offline_router)
    app.include_router(pwa_combined_router)
    return TestClient(app, raise_server_exceptions=True)


@patch("api.offline_sync_api.get_db_session_context", return_value=_OkDbContext())
def test_offline_health_ok(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/offline/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "offline_sync"
    assert data["database"] is True


@patch("api.offline_sync_api.get_db_session_context", return_value=_FailDbContext())
def test_offline_health_degraded(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/offline/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "degraded"
    assert data["database"] is False


@patch("api.pwa_sync_api.get_db_session_context", return_value=_OkDbContext())
def test_pwa_sync_health_ok(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/sync/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "pwa_sync"
    assert data["database"] is True


@patch("api.pwa_sync_api.get_db_session_context", return_value=_FailDbContext())
def test_pwa_sync_health_degraded(
    _mock: MagicMock, health_client: TestClient
) -> None:
    r = health_client.get("/api/v1/sync/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "degraded"
    assert data["database"] is False
