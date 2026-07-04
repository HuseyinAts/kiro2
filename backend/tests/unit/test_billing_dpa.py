"""Faz 1 B2B — DPA + billing MVP: tablolar + seed + DPA-gate + entitlement.

Gerçek postgres, 2-org test verisi enjekte + kendini temizler.
"""

import os
import uuid

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.billing_service import (
    get_active_license,
    has_feature,
    is_dpa_signed,
    seat_usage,
)


def _pg():
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if "postgresql" not in raw:
        pytest.skip("gerçek postgres yok")
    return make_url(raw).set(host="localhost", port=5434, database="kiro2")


def test_tables_and_seed():
    eng = create_engine(_pg())
    with eng.connect() as c:
        for t in (
            "plans",
            "organization_licenses",
            "data_processing_agreements",
            "invoices",
        ):
            n = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_name=:t"
                ),
                {"t": t},
            ).scalar()
            assert n == 1, f"{t} tablosu yok"
        plans = c.execute(text("SELECT code FROM plans")).scalars().all()
        assert set(plans) >= {"free", "okul_basic", "okul_pro"}, plans


@pytest_asyncio.fixture
async def seeded():
    raw = str(_pg())
    aurl = raw.replace("postgresql://", "postgresql+asyncpg://")
    if "+asyncpg" not in aurl:
        aurl = aurl.replace("postgresql", "postgresql+asyncpg", 1)
    eng = create_async_engine(aurl)
    sm = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    tag = uuid.uuid4().hex[:8]
    org = f"billorg_{tag}"
    async with sm() as s:
        await s.execute(
            text(
                "INSERT INTO organizations (id,name,org_type,status,kvkk_role,"
                "license_seats,created_at,updated_at) VALUES "
                "(:i,:i,'ozel_okul','trial','controller',0,now(),now())"
            ),
            {"i": org},
        )
        # okul_pro lisansı (sso feature'lı, 500 koltuk)
        pid = (
            await s.execute(text("SELECT id FROM plans WHERE code='okul_pro'"))
        ).scalar()
        await s.execute(
            text(
                "INSERT INTO organization_licenses (id,organization_id,plan_id,"
                "seat_count,status,created_at,updated_at) VALUES "
                "(gen_random_uuid()::text,:o,:p,10,'active',now(),now())"
            ),
            {"o": org, "p": pid},
        )
        # 3 aktif STUDENT üye (koltuk kullanımı)
        for i in range(3):
            uid = f"billu_{tag}_{i}"
            await s.execute(
                text(
                    "INSERT INTO users (id,organization_id,email,username,password_hash,"
                    "first_name,last_name,role,is_active) VALUES "
                    "(:i,:o,:e,:u,'x','T','U','STUDENT',true)"
                ),
                {"i": uid, "o": org, "e": f"{uid}@t.z", "u": uid},
            )
            await s.execute(
                text(
                    "INSERT INTO org_memberships (id,organization_id,user_id,org_role,"
                    "is_active,created_at) VALUES "
                    "(gen_random_uuid()::text,:o,:u,'STUDENT',true,now())"
                ),
                {"o": org, "u": uid},
            )
        await s.commit()
    yield {"sm": sm, "org": org, "tag": tag}
    async with sm() as s:
        await s.execute(
            text("DELETE FROM users WHERE email LIKE :p"), {"p": f"billu_{tag}_%"}
        )
        await s.execute(text("DELETE FROM organizations WHERE id=:o"), {"o": org})
        await s.commit()
    await eng.dispose()


@pytest.mark.asyncio
async def test_dpa_gate(seeded):
    async with seeded["sm"]() as s:
        # DPA yok → False (aktivasyon bloke)
        assert await is_dpa_signed(s, seeded["org"]) is False
        # signed DPA ekle → True
        await s.execute(
            text(
                "INSERT INTO data_processing_agreements (id,organization_id,version,"
                "status,signed_at,created_at) VALUES "
                "(gen_random_uuid()::text,:o,'v1','signed',now(),now())"
            ),
            {"o": seeded["org"]},
        )
        await s.commit()
        assert await is_dpa_signed(s, seeded["org"]) is True


@pytest.mark.asyncio
async def test_entitlement_and_seat(seeded):
    async with seeded["sm"]() as s:
        lic = await get_active_license(s, seeded["org"])
        assert lic is not None and lic["plan_code"] == "okul_pro"
        # entitlement: okul_pro sso=true, analytics=true; billing=yok
        assert await has_feature(s, seeded["org"], "sso") is True
        assert await has_feature(s, seeded["org"], "nonexistent") is False
        # seat: 3 aktif STUDENT üye, limit 500 → over_limit False
        su = await seat_usage(s, seeded["org"])
        assert su["used"] == 3 and su["limit"] == 500 and su["over_limit"] is False
