"""Faz 0 Step 3 — BaseRepository tenant scoping cross-tenant izolasyon kanıtı.

Tasarımın #1 riski (sessiz cross-tenant PII sızıntısı) için doğrudan test:
2 org + 2 user → org_A repo'su org_B satırlarını GÖRMEMELİ; unscoped hepsini görür.
In-memory SQLite motoru ile izole ve deterministik çalışır.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.user_models import Organization, User
from repositories.base import BaseRepository


@pytest_asyncio.fixture
async def seeded():
    """2 org + 2 user oluştur, in-memory SQLite motoru ile test et."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Organization.__table__.create)
        await conn.run_sync(User.__table__.create)

    sm = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    tag = uuid.uuid4().hex[:8]
    org_a, org_b = f"testorg_a_{tag}", f"testorg_b_{tag}"
    ua, ub = f"tu_a_{tag}", f"tu_b_{tag}"

    async with sm() as s:
        org1 = Organization(id=org_a, name=org_a, org_type="ozel_okul", status="active", kvkk_role="controller", license_seats=0)
        org2 = Organization(id=org_b, name=org_b, org_type="ozel_okul", status="active", kvkk_role="controller", license_seats=0)
        s.add_all([org1, org2])

        u1 = User(
            id=ua,
            organization_id=org_a,
            email=f"{ua}@t.z",
            username=ua,
            password_hash="x",
            first_name="Test",
            last_name="User",
            role="STUDENT",
            is_active=True,
            is_2fa_enabled=False,
        )
        u2 = User(
            id=ub,
            organization_id=org_b,
            email=f"{ub}@t.z",
            username=ub,
            password_hash="x",
            first_name="Test",
            last_name="User",
            role="STUDENT",
            is_active=True,
            is_2fa_enabled=False,
        )
        s.add_all([u1, u2])
        await s.commit()

    yield {"sm": sm, "org_a": org_a, "org_b": org_b, "ua": ua, "ub": ub}
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
