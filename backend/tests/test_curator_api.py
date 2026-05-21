"""
Curator API Tests — Faz 3.1

Admin-only `/api/v1/curator/{queue,verdict,stats}` endpoint'lerini test eder.

DB bağımlılığı mock'lanır (AsyncSession + execute). Auth dependency
`get_current_admin_user` override edilir. Bu pattern `test_api_cache.py`'den
alındı.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend on sys.path (tests are run from backend/ but conftest may not
# always inject — defensive)
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.curator import router as curator_router  # noqa: E402
from core.dependencies import get_current_admin_user, get_db  # noqa: E402


# ============================================================================
# Helpers
# ============================================================================
def _make_test_user(role: str = "admin", user_id: str = "admin-test-1"):
    """Test admin user (AuthenticatedUser şart değil — basit objekt yeterli)."""
    return SimpleNamespace(
        id=user_id,
        username=f"{role}_user",
        role=role,
        email=f"{role}@test.com",
        permissions=[],
        exp=None,
    )


def _override_admin():
    return _make_test_user(role="admin")


def _make_question_row(
    *,
    qid: str = "q-1",
    text: str = "Aşağıdakilerden hangisi doğrudur?",
    correct: str = "A",
    subject: str = "TURKCE",
    difficulty: str = "EASY",
    qstatus: str = "bronze_clean",
    image_url: str | None = "/static/crops/sayfa_0001_q1.png",
    misconception_tags=None,
    solution_steps=None,
    similar_question_ids=None,
    pipeline_metadata: dict | None = None,
):
    """ORM-like mock row (attribute access kullanır, dict değil)."""
    return SimpleNamespace(
        id=qid,
        question_text=text,
        option_a="Seçenek A",
        option_b="Seçenek B",
        option_c="Seçenek C",
        option_d="Seçenek D",
        option_e=None,
        correct_answer=correct,
        subject_area=subject,
        difficulty_level=difficulty,
        quality_review_status=qstatus,
        question_image_url=image_url,
        misconception_tags=misconception_tags,
        solution_steps=solution_steps,
        similar_question_ids=similar_question_ids,
        pipeline_metadata=pipeline_metadata,
        reviewed_by=None,
        is_active=True,
    )


def _make_db_mock(
    *,
    rows: list | None = None,
    total: int = 0,
    fetch_one_row=None,
    stats_row=None,
    fail_commit: bool = False,
):
    """AsyncSession mock.

    `execute()` her çağrıda sırayla farklı sonuçları döner. Sıra
    handler'ın sorgu sırasına göre planlanır.
    """
    db = AsyncMock()

    # Her execute çağrısı için ayrı bir result hazırlanır
    results: list = []

    def add_count_result(value: int):
        r = MagicMock()
        r.scalar.return_value = value
        results.append(r)

    def add_rows_result(rs: list):
        r = MagicMock()
        # Yeni implementation raw SQL + .mappings().all() kullanıyor.
        # Mock row'lar SimpleNamespace — vars() ile dict'e çevrilir,
        # böylece curator.py'deki SimpleNamespace(**dict(r)) tekrar
        # SimpleNamespace üretir.
        mapping_rows = [vars(row) if hasattr(row, "__dict__") else row for row in rs]
        mappings = MagicMock()
        mappings.all.return_value = mapping_rows
        r.mappings.return_value = mappings
        # Eski (defansif) scalars erişimi de tutuluyor
        scalars = MagicMock()
        scalars.all.return_value = rs
        r.scalars.return_value = scalars
        results.append(r)

    def add_single_row_result(rs):
        r = MagicMock()
        r.scalar_one_or_none.return_value = rs
        results.append(r)

    def add_stats_row(sr):
        r = MagicMock()
        r.first.return_value = sr
        results.append(r)

    if rows is not None:
        # /queue: önce count, sonra rows
        add_count_result(total)
        add_rows_result(rows)

    if fetch_one_row is not None:
        # /verdict: önce fetch, sonra audit insert (audit insert sonucu önemli değil)
        add_single_row_result(fetch_one_row)
        add_single_row_result(None)  # audit insert — kullanılmıyor

    if stats_row is not None:
        add_stats_row(stats_row)

    # execute() çağrıları için iterator
    iter_results = iter(results)

    async def fake_execute(*args, **kwargs):
        try:
            return next(iter_results)
        except StopIteration:
            # Beklenmeyen ekstra execute (örn. audit log) için boş döner
            empty = MagicMock()
            empty.scalar.return_value = 0
            empty.scalar_one_or_none.return_value = None
            empty.scalars.return_value.all.return_value = []
            empty.first.return_value = None
            return empty

    db.execute = fake_execute
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    if fail_commit:

        async def fake_commit():
            raise RuntimeError("simulated commit failure")

        db.commit = fake_commit

    return db


@pytest.fixture
def app():
    """FastAPI app sadece curator router ile."""
    app = FastAPI()
    app.include_router(curator_router)
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)


# ============================================================================
# Tests
# ============================================================================
class TestCuratorQueueAuth:
    """Auth gate: admin olmadan erişim engellenir."""

    def test_get_queue_requires_auth(self, client):
        """get_current_admin_user override edilmeden 401/403."""
        resp = client.get("/api/v1/curator/queue")
        assert resp.status_code in (401, 403)

    def test_get_queue_admin_allowed(self, app, client):
        """Admin user override + boş DB → 200 ve boş items."""
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(rows=[], total=0)

        resp = client.get("/api/v1/curator/queue")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 25


class TestCuratorQueueFilters:
    """Filtreleme ve pagination."""

    def test_get_queue_returns_items(self, app, client):
        rows = [_make_question_row(qid=f"q-{i}") for i in range(3)]
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(rows=rows, total=3)

        resp = client.get("/api/v1/curator/queue?per_page=10")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        item0 = data["items"][0]
        assert item0["id"] == "q-0"
        assert item0["correct_answer"] == "A"
        assert item0["subject_area"] == "TURKCE"
        assert item0["options"]["A"] == "Seçenek A"
        assert item0["options"]["E"] is None
        assert item0["image_url"].endswith(".png")

    def test_get_queue_invalid_status_rejected(self, app, client):
        """Bilinmeyen quality_review_status değeri 400 döner."""
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(rows=[], total=0)

        resp = client.get("/api/v1/curator/queue?status=not_a_real_status")
        assert resp.status_code == 400
        assert "not_a_real_status" in resp.text

    def test_get_queue_subject_filter_passes(self, app, client):
        """subject parametresi kabul edilir (case .upper() ile)."""
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(rows=[], total=0)

        resp = client.get("/api/v1/curator/queue?subject=matematik&difficulty=hard")
        assert resp.status_code == 200, resp.text

    def test_get_queue_pagination_params(self, app, client):
        """page/per_page parametrelerini yansıtır."""
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(rows=[], total=100)

        resp = client.get("/api/v1/curator/queue?page=3&per_page=50")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["page"] == 3
        assert data["per_page"] == 50
        assert data["total"] == 100


class TestCuratorVerdict:
    """POST /verdict — DB update, audit trail, status mapping."""

    def test_verdict_requires_auth(self, client):
        resp = client.post(
            "/api/v1/curator/verdict",
            json={"question_id": "q-1", "verdict": "verify"},
        )
        assert resp.status_code in (401, 403)

    def test_verdict_verify_updates_status(self, app, client):
        """verify → auto_judged_high mapping ve pipeline_metadata audit trail."""
        row = _make_question_row(qid="q-1", qstatus="bronze_clean")
        db = _make_db_mock(fetch_one_row=row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={
                "question_id": "q-1",
                "verdict": "verify",
                "notes": "Onaylandı, doğru çözüm",
                "reviewer_velocity_seconds": 42,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["question_id"] == "q-1"
        assert data["previous_status"] == "bronze_clean"
        assert data["new_status"] == "auto_judged_high"
        assert data["reviewed_by"] == "admin-test-1"

        # Row mutated correctly
        assert row.quality_review_status == "auto_judged_high"
        assert row.reviewed_by == "admin-test-1"
        assert row.pipeline_metadata is not None
        verdict_meta = row.pipeline_metadata["curator_verdict"]
        assert verdict_meta["verdict"] == "verify"
        assert verdict_meta["notes"] == "Onaylandı, doğru çözüm"
        assert verdict_meta["velocity_seconds"] == 42
        assert verdict_meta["previous_status"] == "bronze_clean"
        assert verdict_meta["reviewer_id"] == "admin-test-1"

    def test_verdict_reject_updates_status(self, app, client):
        """reject → rejected mapping."""
        row = _make_question_row(qid="q-2", qstatus="bronze_clean")
        db = _make_db_mock(fetch_one_row=row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={
                "question_id": "q-2",
                "verdict": "reject",
                "error_type": "wrong_answer_key",
                "reviewer_velocity_seconds": 15,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["new_status"] == "rejected"
        assert row.quality_review_status == "rejected"
        assert row.pipeline_metadata["curator_verdict"]["error_type"] == (
            "wrong_answer_key"
        )

    def test_verdict_archive_updates_status(self, app, client):
        """archive → archived mapping."""
        row = _make_question_row(qid="q-3", qstatus="pending")
        db = _make_db_mock(fetch_one_row=row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={"question_id": "q-3", "verdict": "archive"},
        )
        assert resp.status_code == 200, resp.text
        assert row.quality_review_status == "archived"

    def test_verdict_invalid_verdict_rejected(self, app, client):
        """Pydantic Literal validation: bilinmeyen verdict 422."""
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: _make_db_mock(
            fetch_one_row=_make_question_row(qid="q-x")
        )

        resp = client.post(
            "/api/v1/curator/verdict",
            json={"question_id": "q-x", "verdict": "unknown_verdict"},
        )
        assert resp.status_code == 422

    def test_verdict_question_not_found(self, app, client):
        """Eksik question_id → 404."""
        db = _make_db_mock(fetch_one_row=None)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={"question_id": "q-missing", "verdict": "verify"},
        )
        assert resp.status_code == 404

    def test_verdict_preserves_existing_pipeline_metadata(self, app, client):
        """pipeline_metadata mevcut alanları korunmalı (curator_verdict eklenir)."""
        existing_meta = {
            "ai_count": 3,
            "crop_file": "crops/sayfa_0001_q1.png",
            "v2_2_tier": "high",
        }
        row = _make_question_row(
            qid="q-4", qstatus="bronze_clean", pipeline_metadata=existing_meta
        )
        db = _make_db_mock(fetch_one_row=row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={"question_id": "q-4", "verdict": "verify"},
        )
        assert resp.status_code == 200, resp.text
        # Mevcut alanlar duruyor
        assert row.pipeline_metadata["ai_count"] == 3
        assert row.pipeline_metadata["crop_file"] == "crops/sayfa_0001_q1.png"
        # Yeni alan eklendi
        assert "curator_verdict" in row.pipeline_metadata

    def test_verdict_velocity_tracking(self, app, client):
        """reviewer_velocity_seconds pipeline_metadata'ya yazılır."""
        row = _make_question_row(qid="q-5")
        db = _make_db_mock(fetch_one_row=row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.post(
            "/api/v1/curator/verdict",
            json={
                "question_id": "q-5",
                "verdict": "verify",
                "reviewer_velocity_seconds": 87,
            },
        )
        assert resp.status_code == 200, resp.text
        assert row.pipeline_metadata["curator_verdict"]["velocity_seconds"] == 87


class TestCuratorStats:
    """GET /stats — dashboard metrics."""

    def test_stats_requires_auth(self, client):
        resp = client.get("/api/v1/curator/stats")
        assert resp.status_code in (401, 403)

    def test_stats_returns_counts(self, app, client):
        """SQL'in döndürdüğü stats_row Pydantic'e yansır."""
        stats_row = SimpleNamespace(
            bronze_clean_count=197,
            legacy_v3_unaudited_count=20231,
            pending_status_count=2775,
            verified_count=120,
            rejected_today=8,
            avg_velocity_sec=42.5,
        )
        db = _make_db_mock(stats_row=stats_row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.get("/api/v1/curator/stats")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["pending_count"] == 197  # alias for bronze_clean_count
        assert data["bronze_clean_count"] == 197
        assert data["legacy_v3_unaudited_count"] == 20231
        assert data["pending_status_count"] == 2775
        assert data["verified_count"] == 120
        assert data["rejected_today"] == 8
        assert data["avg_velocity_sec"] == 42.5

    def test_stats_handles_null_velocity(self, app, client):
        """Hiç verdict yokken AVG NULL döner — float|None'a düşmeli."""
        stats_row = SimpleNamespace(
            bronze_clean_count=0,
            legacy_v3_unaudited_count=0,
            pending_status_count=0,
            verified_count=0,
            rejected_today=0,
            avg_velocity_sec=None,
        )
        db = _make_db_mock(stats_row=stats_row)
        app.dependency_overrides[get_current_admin_user] = _override_admin
        app.dependency_overrides[get_db] = lambda: db

        resp = client.get("/api/v1/curator/stats")
        assert resp.status_code == 200, resp.text
        assert resp.json()["avg_velocity_sec"] is None
