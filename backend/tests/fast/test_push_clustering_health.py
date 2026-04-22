"""
GET /api/v1/push/health, GET /api/v1/clustering/health hızlı testler.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.clustering_api import router as clustering_router
from api.pwa_sync_api import push_router as push_only_router


class _OkDbContext:
    async def __aenter__(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FailDbContext:
    async def __aenter__(self):
        raise OSError("db down")

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_pwa_push_health_no_db() -> None:
    app = FastAPI()
    app.include_router(push_only_router)
    c = TestClient(app)
    r = c.get("/api/v1/push/health")
    assert r.status_code == 200
    d = r.json()
    assert d["service"] == "pwa_push"
    assert d["status"] == "ok"
    assert d["subscribe_implemented"] is False


@patch("api.clustering_api.get_db_session_context", return_value=_OkDbContext())
def test_clustering_health_ok(
    _m: MagicMock,
) -> None:
    app = FastAPI()
    app.include_router(clustering_router)
    c = TestClient(app)
    r = c.get("/api/v1/clustering/health")
    assert r.status_code == 200
    d = r.json()
    assert d["service"] == "clustering"
    assert d["status"] == "ok"
    assert d["database"] is True


@patch("api.clustering_api.get_db_session_context", return_value=_FailDbContext())
def test_clustering_health_degraded(
    _m: MagicMock,
) -> None:
    app = FastAPI()
    app.include_router(clustering_router)
    c = TestClient(app)
    r = c.get("/api/v1/clustering/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "degraded"
    assert d["database"] is False
