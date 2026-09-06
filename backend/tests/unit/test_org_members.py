"""Faz 1 B2B — Okul onboarding: üye ekle/rol-değiştir/deaktive et servis mantığı (TDD).

Gerçek postgres (port 5434), fonksiyon-scope fixture: her test taze temp org + kullanıcı
enjekte eder, tag-prefix ile kendini temizler (izole). `org_service` saf iş mantığı;
tenant izolasyon (RLS) ayrı test edilir (test_tenant_scoping_isolation.py). Koltuk/DPA
`billing_service` üzerinden doğrulanır.

Kapsanan kurallar:
- add: email-yok 404, zaten-üye 409, başka-kuruma-ait 409 (cross-tenant claim guard),
  koltuk-dolu 409 (sadece STUDENT/TEACHER sayılır), geçersiz-rol 400, inaktif-üye reaktive,
  ekleme users.organization_id'yi claim eder.
- update: rol değiştir, son-SCHOOL_ADMIN demote/deaktive 409 (lockout guard).
- remove: soft-deactivate, son-admin 409, üye-yok 404.
"""

import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.dependencies import get_current_membership
from services import org_service
from services.org_service import OrgMemberError

LEGACY_ORG = "org_legacy_default"


def _pg_async_url() -> str:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if "postgresql" not in raw:
        pytest.skip("gerçek postgres yok")
    # OLCUM (6 Eyl 2026, ikinci katman): burada `database="kiro2"` de vardi ve
    # sifre duzeltildikten sonra CI'da
    # `asyncpg.InvalidCatalogNameError: database "kiro2" does not exist`
    # aliyorduk -- cunku CI'in DATABASE_URL'i `kiro2_test` veritabanini
    # gosteriyor, test ise onu "kiro2" ile EZIYORDU. host/port ezmesi
    # korunuyor (yerelde de CI'da da postgres 5434'te), ama veritabani adi
    # artik ortamdan geliyor: tek bir DSN kaynagi, iki ortamda da dogru.
    url = make_url(raw).set(host="localhost", port=5434)
    # OLCUM (6 Eyl 2026): burada `str(url)` vardi ve CI'da
    # `asyncpg.InvalidPasswordError: password authentication failed for user
    # "postgres"` uretiyordu. Sebep SQLAlchemy'nin varsayilani:
    # `URL.__str__()` = `render_as_string(hide_password=True)`, yani sifreyi
    # `***` ile MASKELER ve o maske DSN'e literal sifre olarak gider.
    # Olculdu:
    #   str(url)                             -> postgresql://postgres:***@...
    #   render_as_string(hide_password=False)-> postgresql://postgres:<gercek>@...
    # Bu hata simdiye kadar gorunmuyordu cunku pytest `-x` ile suite daha
    # erken duruyordu (bkz. SS10.55).
    # NOT: `render_as_string` SQLAlchemy stub'larinda Any donuyor; mypy
    # `no-any-return` vermesin diye acik str annotation.
    dsn: str = url.render_as_string(hide_password=False)
    return dsn.replace("postgresql://", "postgresql+asyncpg://")


@pytest_asyncio.fixture
async def seeded():
    """Taze temp org (koltuk limiti=2, 1 aktif STUDENT → used=1), 2 org, temp plan,
    ve 5 kullanıcı: admin(SCHOOL_ADMIN), student(STUDENT), free1/free2(LEGACY, üyeliksiz),
    other(org2, üyeliksiz — cross-tenant test için)."""
    eng = create_async_engine(_pg_async_url())
    sm = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    tag = uuid.uuid4().hex[:8]
    org = f"onborg_{tag}"
    org2 = f"onbother_{tag}"
    plan_code = f"onbplan_{tag}"
    emails = {
        "admin": f"onb_{tag}_admin@t.z",
        "student": f"onb_{tag}_stu@t.z",
        "free1": f"onb_{tag}_free1@t.z",
        "free2": f"onb_{tag}_free2@t.z",
        "other": f"onb_{tag}_other@t.z",
        "legacymember": f"onb_{tag}_legmem@t.z",
    }
    # key -> (uid, email, organization_id, org_role|None)
    people = {
        "admin": (f"onbu_{tag}_admin", emails["admin"], org, "SCHOOL_ADMIN"),
        "student": (f"onbu_{tag}_stu", emails["student"], org, "STUDENT"),
        "free1": (f"onbu_{tag}_free1", emails["free1"], LEGACY_ORG, None),
        "free2": (f"onbu_{tag}_free2", emails["free2"], LEGACY_ORG, None),
        "other": (f"onbu_{tag}_other", emails["other"], org2, None),
        # LEGACY üye: users.organization_id=LEGACY + LEGACY_ORG'da aktif üyelik
        # (claim sırasında stale üyeliğin deaktive edildiğini test etmek için)
        "legacymember": (
            f"onbu_{tag}_legmem",
            emails["legacymember"],
            LEGACY_ORG,
            "STUDENT",
        ),
    }
    async with sm() as s:
        for oid in (org, org2):
            await s.execute(
                text(
                    "INSERT INTO organizations (id,name,org_type,status,kvkk_role,"
                    "license_seats,created_at,updated_at) VALUES "
                    "(:i,:i,'ozel_okul','trial','controller',0,now(),now())"
                ),
                {"i": oid},
            )
        pid = str(uuid.uuid4())
        await s.execute(
            text("INSERT INTO plans (id,code,name,seat_limit) VALUES (:i,:c,:c,2)"),
            {"i": pid, "c": plan_code},
        )
        await s.execute(
            text(
                "INSERT INTO organization_licenses (id,organization_id,plan_id,"
                "seat_count,status,created_at,updated_at) VALUES "
                "(gen_random_uuid()::text,:o,:p,2,'active',now(),now())"
            ),
            {"o": org, "p": pid},
        )
        for uid, email, oid, role in people.values():
            await s.execute(
                text(
                    "INSERT INTO users (id,organization_id,email,username,password_hash,"
                    "first_name,last_name,role,is_active) VALUES "
                    "(:i,:o,:e,:u,'x','T','U','STUDENT',true)"
                ),
                {"i": uid, "o": oid, "e": email, "u": uid},
            )
            if role is not None:
                await s.execute(
                    text(
                        "INSERT INTO org_memberships (id,organization_id,user_id,"
                        "org_role,is_active,created_at) VALUES "
                        "(gen_random_uuid()::text,:o,:u,:r,true,now())"
                    ),
                    {"o": oid, "u": uid, "r": role},
                )
        await s.commit()
    yield {
        "sm": sm,
        "org": org,
        "org2": org2,
        "plan_code": plan_code,
        "emails": emails,
        "people": people,
    }
    async with sm() as s:
        await s.execute(
            text(
                "DELETE FROM org_memberships WHERE organization_id IN (:o,:o2) OR user_id LIKE :p"
            ),
            {"o": org, "o2": org2, "p": f"onbu_{tag}_%"},
        )
        await s.execute(
            text("DELETE FROM organization_licenses WHERE organization_id=:o"),
            {"o": org},
        )
        await s.execute(
            text("DELETE FROM data_processing_agreements WHERE organization_id=:o"),
            {"o": org},
        )
        await s.execute(
            text("DELETE FROM users WHERE id LIKE :p"), {"p": f"onbu_{tag}_%"}
        )
        await s.execute(
            text("DELETE FROM organizations WHERE id IN (:o,:o2)"),
            {"o": org, "o2": org2},
        )
        await s.execute(text("DELETE FROM plans WHERE code=:c"), {"c": plan_code})
        await s.commit()
    await eng.dispose()


# ---- add_member --------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_member_success_claims_user(seeded):
    async with seeded["sm"]() as s:
        m = await org_service.add_member(
            s, seeded["org"], seeded["emails"]["free1"], "STUDENT"
        )
        assert m["org_role"] == "STUDENT"
        uid = seeded["people"]["free1"][0]
        row = (
            await s.execute(
                text(
                    "SELECT is_active FROM org_memberships "
                    "WHERE organization_id=:o AND user_id=:u"
                ),
                {"o": seeded["org"], "u": uid},
            )
        ).first()
        assert row is not None and row[0] is True
        claimed = (
            await s.execute(
                text("SELECT organization_id FROM users WHERE id=:u"), {"u": uid}
            )
        ).scalar()
        assert claimed == seeded["org"]


@pytest.mark.asyncio
async def test_add_member_email_not_found_404(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.add_member(s, seeded["org"], "yok@nope.z", "STUDENT")
    assert e.value.status_code == 404


@pytest.mark.asyncio
async def test_add_member_duplicate_409(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.add_member(
                s, seeded["org"], seeded["emails"]["student"], "STUDENT"
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_add_member_cross_tenant_409(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.add_member(
                s, seeded["org"], seeded["emails"]["other"], "STUDENT"
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_add_member_seat_limit_409(seeded):
    async with seeded["sm"]() as s:
        # used=1, limit=2 → free1 STUDENT OK (used→2)
        await org_service.add_member(
            s, seeded["org"], seeded["emails"]["free1"], "STUDENT"
        )
        # dolu → free2 STUDENT 409
        with pytest.raises(OrgMemberError) as e:
            await org_service.add_member(
                s, seeded["org"], seeded["emails"]["free2"], "STUDENT"
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_add_non_seat_role_ignores_limit(seeded):
    async with seeded["sm"]() as s:
        await org_service.add_member(
            s, seeded["org"], seeded["emails"]["free1"], "STUDENT"
        )  # used→2 (dolu)
        # PARENT koltuk tüketmez → dolu olsa da eklenir
        m = await org_service.add_member(
            s, seeded["org"], seeded["emails"]["free2"], "PARENT"
        )
        assert m["org_role"] == "PARENT"


@pytest.mark.asyncio
async def test_add_member_invalid_role_400(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.add_member(
                s, seeded["org"], seeded["emails"]["free1"], "KING"
            )
    assert e.value.status_code == 400


@pytest.mark.asyncio
async def test_add_reactivates_inactive_member(seeded):
    async with seeded["sm"]() as s:
        uid = seeded["people"]["student"][0]
        await org_service.remove_member(s, seeded["org"], uid)  # deaktive
        m = await org_service.add_member(
            s, seeded["org"], seeded["emails"]["student"], "TEACHER"
        )
        assert m["org_role"] == "TEACHER"
        row = (
            await s.execute(
                text(
                    "SELECT is_active, org_role FROM org_memberships "
                    "WHERE organization_id=:o AND user_id=:u"
                ),
                {"o": seeded["org"], "u": uid},
            )
        ).first()
        assert row[0] is True and row[1] == "TEACHER"


# ---- update_member -----------------------------------------------------------


@pytest.mark.asyncio
async def test_update_member_role_change(seeded):
    async with seeded["sm"]() as s:
        m = await org_service.update_member(
            s, seeded["org"], seeded["people"]["student"][0], org_role="TEACHER"
        )
        assert m["org_role"] == "TEACHER"


@pytest.mark.asyncio
async def test_update_last_admin_demote_409(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.update_member(
                s, seeded["org"], seeded["people"]["admin"][0], org_role="TEACHER"
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_update_last_admin_deactivate_409(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.update_member(
                s, seeded["org"], seeded["people"]["admin"][0], is_active=False
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_update_second_admin_allows_demote(seeded):
    async with seeded["sm"]() as s:
        # student → SCHOOL_ADMIN (artık 2 admin)
        await org_service.update_member(
            s, seeded["org"], seeded["people"]["student"][0], org_role="SCHOOL_ADMIN"
        )
        # orijinal admin demote artık serbest
        m = await org_service.update_member(
            s, seeded["org"], seeded["people"]["admin"][0], org_role="TEACHER"
        )
        assert m["org_role"] == "TEACHER"


@pytest.mark.asyncio
async def test_update_member_not_found_404(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.update_member(
                s, seeded["org"], "onbu_yok_uid", org_role="TEACHER"
            )
    assert e.value.status_code == 404


# ---- remove_member -----------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_member_soft_deactivate(seeded):
    async with seeded["sm"]() as s:
        uid = seeded["people"]["student"][0]
        await org_service.remove_member(s, seeded["org"], uid)
        active = (
            await s.execute(
                text(
                    "SELECT is_active FROM org_memberships "
                    "WHERE organization_id=:o AND user_id=:u"
                ),
                {"o": seeded["org"], "u": uid},
            )
        ).scalar()
        assert active is False


@pytest.mark.asyncio
async def test_remove_last_admin_409(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.remove_member(
                s, seeded["org"], seeded["people"]["admin"][0]
            )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_remove_nonmember_404(seeded):
    async with seeded["sm"]() as s:
        with pytest.raises(OrgMemberError) as e:
            await org_service.remove_member(s, seeded["org"], "onbu_yok_uid")
    assert e.value.status_code == 404


# ---- review fix'leri (S200) --------------------------------------------------


@pytest.mark.asyncio
async def test_add_member_email_case_insensitive(seeded):
    """Emailler lowercase saklanır; admin BÜYÜK harf girse de kullanıcı bulunmalı."""
    async with seeded["sm"]() as s:
        m = await org_service.add_member(
            s, seeded["org"], seeded["emails"]["free1"].upper(), "STUDENT"
        )
        assert m["org_role"] == "STUDENT"


@pytest.mark.asyncio
async def test_add_member_deactivates_stale_membership(seeded):
    """LEGACY üyeyi claim ederken eski (LEGACY_ORG) üyeliği deaktive edilmeli —
    tek-aktif-üyelik = users.organization_id (dual-membership authz açığını kapatır)."""
    async with seeded["sm"]() as s:
        uid = seeded["people"]["legacymember"][0]
        await org_service.add_member(
            s, seeded["org"], seeded["emails"]["legacymember"], "TEACHER"
        )
        legacy_active = (
            await s.execute(
                text(
                    "SELECT is_active FROM org_memberships "
                    "WHERE organization_id=:o AND user_id=:u"
                ),
                {"o": LEGACY_ORG, "u": uid},
            )
        ).scalar()
        assert legacy_active is False
        new = (
            await s.execute(
                text(
                    "SELECT is_active, org_role FROM org_memberships "
                    "WHERE organization_id=:o AND user_id=:u"
                ),
                {"o": seeded["org"], "u": uid},
            )
        ).first()
        assert new[0] is True and new[1] == "TEACHER"


@pytest.mark.asyncio
async def test_get_current_membership_scoped_to_tenant(seeded):
    """Aynı kullanıcı iki org'da üye ise, get_current_membership operated-tenant'a
    göre rolü döndürmeli (cross-tenant authz divergence fix)."""
    async with seeded["sm"]() as s:
        uid = seeded["people"]["student"][0]  # org'da STUDENT
        # aynı kullanıcıya org2'de SCHOOL_ADMIN üyeliği ver
        await s.execute(
            text(
                "INSERT INTO org_memberships (id,organization_id,user_id,org_role,"
                "is_active,created_at) VALUES "
                "(gen_random_uuid()::text,:o,:u,'SCHOOL_ADMIN',true,now())"
            ),
            {"o": seeded["org2"], "u": uid},
        )
        await s.commit()
        cu = SimpleNamespace(id=uid)
        m_org = await get_current_membership(
            organization_id=seeded["org"], current_user=cu, db=s
        )
        assert m_org["org_role"] == "STUDENT"
        m_org2 = await get_current_membership(
            organization_id=seeded["org2"], current_user=cu, db=s
        )
        assert m_org2["org_role"] == "SCHOOL_ADMIN"
