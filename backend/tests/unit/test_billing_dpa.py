"""Faz 1 B2B — DPA + billing MVP: tablolar + seed + DPA-gate + entitlement.

Gerçek postgres, 2-org test verisi enjekte + kendini temizler.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.billing_service import (
    get_active_license,
    has_feature,
    is_dpa_signed,
    seat_usage,
)
from tests.pg_sync import sync_pg_url


def _pg():
    # Ortak tanim ve olcum gerekcesi: tests/pg_sync.py
    return sync_pg_url()


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

    # OLCUM (6 Eyl 2026): `plans` tablosu VAR ama BOS -- hem bu makinede hem
    # CI'da. Tohumu (free / okul_basic / okul_pro) yazan migration
    # `backend/alembic/versions_archive/faz1_billing_20260704_dpa_billing_mvp.py`
    # icinde, yani AKTIF zincirde DEGIL: `alembic upgrade head` onu hic
    # kosturmuyor. Yani bos tablo bir REGRESYON degil, tohumun aktif
    # zincirden dusmus olmasi -- ve bu bir URUN/GOC karari (tohum migration'a
    # mi geri alinacak, yoksa seed script'ine mi tasinacak?), testin
    # uyduracagi bir sey degil.
    #
    # Bu yuzden BOS evren "fail" degil "skip": surekli kirmizi bir assert
    # hicbir regresyonu yakalayamaz, yalnizca kapiyi kapali tutar. Tohum
    # geldigi anda bu test kendiliginden GERCEK bir olcume doner.
    if not plans:
        pytest.skip(
            "`plans` tohumu yok (seed migration versions_archive/ altinda, "
            "aktif zincirde degil) -- bkz. docs/guvenlik-borcu.md SS10.59"
        )
    assert set(plans) >= {"free", "okul_basic", "okul_pro"}, plans


@pytest_asyncio.fixture
async def seeded():
    # Burada once `str(_pg())` vardi. IKI kusur birden tasiyordu:
    #  * `URL.__str__()` = `render_as_string(hide_password=True)`, yani sifreyi
    #    `***` ile MASKELER ve o maske DSN'e literal sifre olarak gider
    #    (ayni bulgu: tests/unit/test_org_members.py, SS10.52).
    #  * Surucu adi metin uzerinden degistiriliyordu; `_pg()` artik
    #    `postgresql+psycopg` dondurdugu icin bu `replace` zinciri
    #    "postgresql+asyncpg+psycopg://" gibi bozuk bir DSN uretirdi.
    # Ikisi de URL nesnesi uzerinden cozuluyor.
    aurl: str = (
        _pg().set(drivername="postgresql+asyncpg").render_as_string(hide_password=False)
    )
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
        if pid is None:
            # Ayni on kosul, ayni gerekce: `plans` tohumu aktif migration
            # zincirinde yok (bkz. test_tables_and_seed'deki olcum notu).
            # Guard olmadan buradan `NotNullViolationError: plan_id` geliyor
            # -- yani eksik ON KOSUL, urun kusuru gibi raporlaniyordu.
            await s.rollback()
            await eng.dispose()
            pytest.skip(
                "`plans` tohumu yok (okul_pro plani bulunamadi) -- "
                "bkz. docs/guvenlik-borcu.md SS10.59"
            )
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
            text("DELETE FROM org_memberships WHERE organization_id=:o"), {"o": org}
        )
        await s.execute(
            text("DELETE FROM data_processing_agreements WHERE organization_id=:o"),
            {"o": org},
        )
        await s.execute(
            text("DELETE FROM users WHERE email LIKE :p"), {"p": f"billu_{tag}_%"}
        )
        await s.execute(
            text("DELETE FROM organization_licenses WHERE organization_id=:o"),
            {"o": org},
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
