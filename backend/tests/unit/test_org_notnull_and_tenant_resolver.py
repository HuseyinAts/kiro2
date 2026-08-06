"""Faz 0 Step 2b/3a — NOT NULL flip + get_current_tenant resolver.

- DB: kimlik çekirdeğinde organization_id NOT NULL olmalı.
- Resolver: users.organization_id'yi çözer, yoksa 403.
TDD: NOT NULL testi migration öncesi RED, sonrası GREEN.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]


def _engine():
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not raw.startswith("postgresql"):
        pytest.skip("gerçek postgres DATABASE_URL yok")
    return create_engine(
        make_url(raw).set(host="127.0.0.1", port=5434, database="kiro2")
    )


def test_org_id_not_null_enforced():
    eng = _engine()
    with eng.connect() as c:
        for t in IDENTITY_TABLES:
            nullable = c.execute(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert nullable == "NO", f"{t}.organization_id hâlâ nullable"


def test_get_current_tenant_importable():
    """Resolver import edilebilir + doğru imzaya sahip."""
    from core.dependencies import get_current_tenant

    assert callable(get_current_tenant)
    import inspect

    params = inspect.signature(get_current_tenant).parameters
    assert "current_user" in params and "db" in params


@pytest.mark.asyncio
async def test_resolver_returns_org_for_backfilled_user():
    """Gerçek backfill'li bir user için resolver org_legacy_default döndürmeli."""
    from unittest.mock import AsyncMock, MagicMock

    from core.dependencies import get_current_tenant

    eng = _engine()
    with eng.connect() as c:
        uid = c.execute(text("SELECT id FROM users LIMIT 1")).scalar()
        if uid is None:
            pytest.skip("users boş")
        expected = c.execute(
            text("SELECT organization_id FROM users WHERE id=:i"), {"i": uid}
        ).scalar()

    # mock db: resolver'ın SQL'ini taklit et
    fake_row = MagicMock()
    fake_row.__getitem__ = lambda self, i: expected
    result_proxy = MagicMock()
    result_proxy.first.return_value = fake_row
    db = AsyncMock()
    db.execute.return_value = result_proxy
    user = MagicMock()
    user.id = uid

    org = await get_current_tenant(current_user=user, db=db)
    assert org == str(expected)
