"""Veli onay endpoint testleri (public verify/withdraw).

Endpoint, app'in get_db'sini kullanır; testte get_db strict-rollback session'a
override edilir ki seed (uncommitted savepoint) endpoint'e görünsün ve 5434'e
kalıcı yazma olmasın.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="endpoint testleri gerçek DB gerektirir",
)


@pytest_asyncio.fixture
async def db_session():
    """5434/kiro2 strict-rollback session (Task 4 ile aynı desen)."""
    dsn = os.environ.get("KVKK_VERIFY_DSN")
    if not dsn:
        pytest.skip("KVKK_VERIFY_DSN ayarlı değil (5434 strict-rollback fixture)")
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif dsn.startswith("postgresql+psycopg2://"):
        dsn = dsn.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(dsn, poolclass=NullPool)
    conn = await engine.connect()
    trans = await conn.begin()
    maker = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()
        await conn.close()
        await engine.dispose()


def _client_with_db(db):
    """app + get_db override → endpoint test session'ını paylaşır."""
    from core.dependencies import get_db
    from main import app

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    return app, get_db, AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_verify_endpoint_grants(db_session):
    db = db_session
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, created_at, updated_at) VALUES "
            "('vep-1', 'vep1@t.com', 'vep1', 'x', 'T', 'C', CAST('STUDENT' AS userrole), "
            "TRUE, FALSE, 0, 1, 1200, FALSE, FALSE, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        )
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "('prof-vep-1', 'vep-1', 11, FALSE, 'veli@t.com', 0.0, 0, 0, 0, 0.0, "
            "NOW(), NOW()) ON CONFLICT (id) DO NOTHING"
        )
    )
    await db.commit()

    from services.veli_onay_service import VeliOnayService

    token = await VeliOnayService(db).request_consent("vep-1", "veli@t.com")

    app, get_db, client = _client_with_db(db)
    try:
        async with client:
            resp = await client.post(
                "/api/v1/auth/veli-onay/verify", json={"token": token}
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "granted"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_verify_invalid_token_returns_400(db_session):
    app, get_db, client = _client_with_db(db_session)
    try:
        async with client:
            resp = await client.post(
                "/api/v1/auth/veli-onay/verify", json={"token": "yok-boyle-token"}
            )
        assert resp.status_code == 400
        assert resp.status_code < 500  # 500 OLMAMALI (middleware kuralı)
    finally:
        app.dependency_overrides.pop(get_db, None)
