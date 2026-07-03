"""Faz 0 Step 3 — BaseRepository tenant scoping cross-tenant izolasyon kanıtı.

Tasarımın #1 riski (sessiz cross-tenant PII sızıntısı) için doğrudan test:
2 org + 2 user → org_A repo'su org_B satırlarını GÖRMEMELİ; unscoped hepsini görür.
Gerçek postgres, kendi kendini temizler.
"""

import os
import uuid

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.user_models import User
from repositories.base import BaseRepository


def _async_url():
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "")
    if "postgresql" not in raw:
        pytest.skip("gerçek postgres DATABASE_URL yok")
    raw = raw.replace("postgresql://", "postgresql+asyncpg://")
    if "+asyncpg" not in raw:
        raw = raw.replace("postgresql", "postgresql+asyncpg", 1)
    return str(make_url(raw).set(host="localhost", port=5434, database="kiro2"))


@pytest_asyncio.fixture
async def seeded():
    """2 org + 2 user oluştur, testten sonra temizle."""
    eng = create_async_engine(_async_url())
    sm = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    tag = uuid.uuid4().hex[:8]
    org_a, org_b = f"testorg_a_{tag}", f"testorg_b_{tag}"
    ua, ub = f"tu_a_{tag}", f"tu_b_{tag}"
    async with sm() as s:
        for oid in (org_a, org_b):
            await s.execute(
                text(
                    "INSERT INTO organizations (id,name,org_type,status,kvkk_role,"
                    "license_seats,created_at,updated_at) VALUES "
                    "(:i,:n,'ozel_okul','active','controller',0,now(),now())"
                ),
                {"i": oid, "n": oid},
            )
        for uid, oid in ((ua, org_a), (ub, org_b)):
            await s.execute(
                text(
                    "INSERT INTO users (id,organization_id,email,username,password_hash,"
                    "first_name,last_name,role,is_active) "
                    "VALUES (:i,:o,:e,:u,'x','Test','User','STUDENT',true)"
                ),
                {"i": uid, "o": oid, "e": f"{uid}@t.z", "u": uid},
            )
        await s.commit()
    yield {"sm": sm, "org_a": org_a, "org_b": org_b, "ua": ua, "ub": ub}
    async with sm() as s:
        await s.execute(
            text("DELETE FROM users WHERE id IN (:a,:b)"), {"a": ua, "b": ub}
        )
        await s.execute(
            text("DELETE FROM organizations WHERE id IN (:a,:b)"),
            {"a": org_a, "b": org_b},
        )
        await s.commit()
    await eng.dispose()


@pytest.mark.asyncio
async def test_scoped_repo_sees_only_own_tenant(seeded):
    async with seeded["sm"]() as s:
        repo_a = BaseRepository(User, s, organization_id=seeded["org_a"])
        ids_a = {u.id for u in await repo_a.get_all(limit=1000)}
        assert seeded["ua"] in ids_a, "kendi kullanıcısını görmeli"
        assert seeded["ub"] not in ids_a, (
            "SIZINTI: org_B kullanıcısı org_A'da görünüyor"
        )


@pytest.mark.asyncio
async def test_cross_tenant_get_by_id_blocked(seeded):
    async with seeded["sm"]() as s:
        repo_a = BaseRepository(User, s, organization_id=seeded["org_a"])
        # org_A repo'su org_B kullanıcısını id ile çekemez
        assert await repo_a.get_by_id(seeded["ub"]) is None, (
            "SIZINTI: cross-tenant get_by_id"
        )
        # kendi kullanıcısını çekebilir
        assert (await repo_a.get_by_id(seeded["ua"])) is not None


@pytest.mark.asyncio
async def test_unscoped_repo_sees_all(seeded):
    """org_id verilmezse (backward-compat) filtre yok — her iki user görünür."""
    async with seeded["sm"]() as s:
        repo = BaseRepository(User, s)  # organization_id=None
        ids = {u.id for u in await repo.get_all(limit=1000)}
        assert seeded["ua"] in ids and seeded["ub"] in ids
