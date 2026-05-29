"""VeliOnayService akış testleri (postgres test DB).

Strict-rollback fixture: KVKK_VERIFY_DSN env'inden (5434/kiro2 prod şeması) bağlanır,
join_transaction_mode="create_savepoint" ile servis commit()'leri savepoint'e yazar;
dıştaki transaction test sonunda rollback edilir → sıfır kalıcı yazma.
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="VeliOnayService gerçek DB gerektirir (USE_POSTGRES_TESTS=true)",
)


@pytest_asyncio.fixture
async def db_session():
    """5434/kiro2'ye strict-rollback session. Global broken db_session'ı override eder."""
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


async def _seed_minor(db, user_id="vtest-child-1"):
    """Test için minor user + student_profile (veli_onay=False) oluştur."""
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, created_at, updated_at) VALUES "
            "(:id, :email, :uname, 'x', 'Test', 'Child', CAST('STUDENT' AS userrole), "
            "TRUE, FALSE, 0, 1, 1200, FALSE, FALSE, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": user_id, "email": f"{user_id}@t.com", "uname": user_id},
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "(:id, :uid, 11, FALSE, 'veli@t.com', 0.0, 0, 0, 0, 0.0, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": f"prof-{user_id}", "uid": user_id},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_request_then_verify_grants_consent(db_session):
    db = db_session
    await _seed_minor(db, "vtest-child-1")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-1", "veli@t.com")
    assert token and len(token) >= 32

    result = await svc.verify_and_grant(token, ip="1.2.3.4", ua="pytest")
    assert result.success is True
    assert result.status == "granted"

    row = (
        await db.execute(
            text("SELECT veli_onay FROM student_profiles WHERE user_id = :u"),
            {"u": "vtest-child-1"},
        )
    ).first()
    assert row[0] is True  # veli_onay flip


@pytest.mark.asyncio
async def test_verify_is_idempotent_after_grant(db_session):
    db = db_session
    await _seed_minor(db, "vtest-child-2")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-2", "veli@t.com")
    await svc.verify_and_grant(token)
    again = await svc.verify_and_grant(token)
    assert again.success is True
    assert again.status == "granted"  # idempotent, hata değil


@pytest.mark.asyncio
async def test_invalid_token_rejected(db_session):
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db_session)
    result = await svc.verify_and_grant("gecersiz-token-xyz")
    assert result.success is False
    assert result.error_code == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_withdraw_flips_veli_onay_false(db_session):
    db = db_session
    await _seed_minor(db, "vtest-child-3")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-3", "veli@t.com")
    await svc.verify_and_grant(token)
    ok = await svc.withdraw(token)
    assert ok is True
    row = (
        await db.execute(
            text("SELECT veli_onay FROM student_profiles WHERE user_id = :u"),
            {"u": "vtest-child-3"},
        )
    ).first()
    assert row[0] is False
