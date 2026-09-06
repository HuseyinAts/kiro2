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


# NEDEN BU IKI TEST YENIDEN YAZILDI (6 Eyl 2026):
# Onceki halleri `{"service": "clustering", "status": "ok"}` bekliyordu; bu
# sekil `api/clustering_api.py`teki IKINCI `@router.get("/health")` rotasina
# aitti ve FastAPI ayni yolda ILK rotayi servis ettigi icin O ROTA HIC
# CALISMIYORDU. Yani testler bir kusuru degil, var olmayan bir ucu
# olcuyordu ve yapisal olarak hicbir zaman gecemezdi. Olu rota kaldirildi;
# bu testler artik GERCEKTEN servis edilen ucun sozlesmesini olcuyor
# (kardes olcumler: tests/e2e/test_golden_flows.py:5597 ve
# tests/fast/test_chroma_semantic_health.py:52 ile ayni sekil).
#
# OLCULEN SEY: DB ping'i basarili/basarisiz oldugunda `database` bayragi.
# `status` alani DB'ye DEGIL, sklearn'in varligina bagli (uc oyle tasarlanmis)
# -- bu yuzden burada `status` uzerinden iddia YAPILMIYOR, aksi halde test
# olcmedigi bir seyi olcuyormus gibi gorunurdu.
@patch("api.clustering_api.get_db_session_context", return_value=_OkDbContext())
def test_clustering_health_db_up_database_true(
    _m: MagicMock,
) -> None:
    app = FastAPI()
    app.include_router(clustering_router)
    c = TestClient(app)
    r = c.get("/api/v1/clustering/health")
    assert r.status_code == 200
    d = r.json()
    assert d["service"] == "concept_clustering"
    assert d["database"] is True
    assert d["status"] != "unhealthy"


@patch("api.clustering_api.get_db_session_context", return_value=_FailDbContext())
def test_clustering_health_db_down_database_false(
    _m: MagicMock,
) -> None:
    app = FastAPI()
    app.include_router(clustering_router)
    c = TestClient(app)
    r = c.get("/api/v1/clustering/health")
    assert r.status_code == 200
    d = r.json()
    assert d["service"] == "concept_clustering"
    assert d["database"] is False
    assert d["status"] != "unhealthy"
