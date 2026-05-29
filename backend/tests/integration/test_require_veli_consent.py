"""require_veli_consent: pending minor → 403, granted/adult → geçer.

Strict-rollback fixture (5434), dependency doğrudan çağrılır (HTTP yok).
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
    os.getenv("USE_POSTGRES_TESTS") != "true", reason="gerçek DB gerektirir"
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


async def _make_profile(db, uid, veli_onay):
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, created_at, updated_at) VALUES "
            "(:id, :e, :u, 'x', 'T', 'C', CAST('STUDENT' AS userrole), TRUE, FALSE, "
            "0, 1, 1200, FALSE, FALSE, NOW(), NOW()) ON CONFLICT (id) DO NOTHING"
        ),
        {"id": uid, "e": f"{uid}@t.com", "u": uid},
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "(:id, :u, 11, :vo, 'veli@t.com', 0.0, 0, 0, 0, 0.0, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": f"prof-{uid}", "u": uid, "vo": veli_onay},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_pending_minor_blocked(db_session):
    from fastapi import HTTPException

    from core.dependencies import (
        AuthenticatedUser,
        UserRole,
        require_veli_consent,
    )

    await _make_profile(db_session, "rvc-pending", veli_onay=False)
    user = AuthenticatedUser(
        id="rvc-pending", username="x", role=UserRole.STUDENT, email="x@t.com"
    )
    with pytest.raises(HTTPException) as exc:
        await require_veli_consent(current_user=user, db=db_session)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_granted_minor_allowed(db_session):
    from core.dependencies import (
        AuthenticatedUser,
        UserRole,
        require_veli_consent,
    )

    await _make_profile(db_session, "rvc-granted", veli_onay=True)
    user = AuthenticatedUser(
        id="rvc-granted", username="x", role=UserRole.STUDENT, email="x@t.com"
    )
    out = await require_veli_consent(current_user=user, db=db_session)
    assert out is user  # geçer, user döner
