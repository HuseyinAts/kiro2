"""
TDD RED evidence + regression guard for #485 Task 1.

admin.py ve osym_questions_api.py'deki ham SQL sorguları question_bank'ın
69-alan split'inden (S210, 0fd9b8413) ÖNCEKİ şemayı varsayıyor: question_text,
correct_answer, option_a-e (-> question_content), exam_type/subject_area/
osym_year (-> question_metadata), difficulty_level/irt_*/is_calibrated/
is_calib_pool/quality_score (-> question_statistics) artık question_bank'ta
YOK. Her sorgu UndefinedColumn ile patlıyor (bkz. .claude/sessions/latest.md,
psql kanıtı).

Bu dosya GERÇEK Postgres'e karşı (mock DB DEĞİL) çalışır — S228'in ölçtüğü
"mock dalı hep koşuyordu" tuzağına düşmemek için (bkz. test_admin_api.py'nin
AsyncMock DB'si aynı bug'ı hiç yakalayamazdı).
"""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

from core.dependencies import AuthenticatedUser, get_current_user  # noqa: E402
from core.dependencies import get_db as admin_get_db  # noqa: E402
from models.enums_db import UserRole  # noqa: E402

LIVE_DSN = "postgresql+asyncpg://kiro2_app:kiro2_app_rls_2026@localhost:5434/kiro2"

pytestmark = pytest.mark.asyncio


def _make_admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="admin-1", username="admin", role=UserRole.ADMIN, email="admin@test.com"
    )


def _make_student_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="student-1",
        username="student",
        role=UserRole.STUDENT,
        email="student@test.com",
    )


@pytest_asyncio.fixture
async def live_db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(LIVE_DSN)
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"live Postgres {LIVE_DSN} ulasilamiyor: {exc}")

    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def admin_client(live_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from api.admin import router as admin_router

    app = FastAPI()
    app.include_router(admin_router)

    async def _override_user() -> AuthenticatedUser:
        return _make_admin_user()

    async def _override_db():
        yield live_db

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[admin_get_db] = _override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def osym_client(live_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from api.osym_questions_api import get_db as osym_get_db
    from api.osym_questions_api import router as osym_router

    app = FastAPI()
    app.include_router(osym_router)

    async def _override_user() -> AuthenticatedUser:
        return _make_student_user()

    async def _override_db():
        yield live_db

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[osym_get_db] = _override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# admin.py
# ---------------------------------------------------------------------------


async def test_admin_dashboard_stats_no_500(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/admin/dashboard/stats")
    assert resp.status_code == 200, resp.text


async def test_admin_content_questions_list_no_500(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/admin/content/questions")
    assert resp.status_code == 200, resp.text


async def test_admin_content_search_no_500(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/admin/content/search", params={"q": "test"})
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# osym_questions_api.py
# ---------------------------------------------------------------------------


async def test_osym_statistics_no_500(osym_client: AsyncClient):
    resp = await osym_client.get("/api/v1/osym/statistics")
    assert resp.status_code == 200, resp.text


async def test_osym_subjects_no_500(osym_client: AsyncClient):
    resp = await osym_client.get("/api/v1/osym/subjects")
    assert resp.status_code == 200, resp.text


async def test_osym_random_questions_no_500(osym_client: AsyncClient):
    resp = await osym_client.get("/api/v1/osym/random-questions", params={"count": 2})
    assert resp.status_code == 200, resp.text


async def test_osym_practice_exam_no_500(osym_client: AsyncClient):
    resp = await osym_client.get("/api/v1/osym/practice-exam")
    assert resp.status_code == 200, resp.text


async def test_osym_questions_no_500(osym_client: AsyncClient):
    resp = await osym_client.get("/api/v1/osym/questions", params={"limit": 2})
    assert resp.status_code == 200, resp.text
