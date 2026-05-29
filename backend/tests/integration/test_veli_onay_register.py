"""Minor register → veli_consent pending kaydı oluşur.

get_db strict-rollback session'a override edilir; register handler aynı
transaction'a yazar, test sonunda rollback (5434'e kalıcı yazma yok).
"""

import os
import uuid

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
    reason="gerçek DB gerektirir",
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


@pytest.mark.asyncio
async def test_minor_register_creates_pending_consent(db_session):
    from core.dependencies import get_db
    from main import app

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    email = f"minor-{uuid.uuid4().hex[:8]}@t.com"
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "sifre": "Guclu!Parola123",
                    "ad_soyad": "Kucuk Ogrenci",
                    "rol": "ogrenci",
                    "birth_date": "2015-01-01",  # minor
                    "veli_email": "veli@t.com",
                },
            )
        assert resp.status_code in (200, 201), resp.text

        row = (
            await db_session.execute(
                text(
                    "SELECT vc.status FROM veli_consent vc JOIN users u "
                    "ON u.id = vc.child_user_id WHERE u.email = :e"
                ),
                {"e": email},
            )
        ).first()
        assert row is not None
        assert row[0] == "pending"
    finally:
        app.dependency_overrides.pop(get_db, None)
