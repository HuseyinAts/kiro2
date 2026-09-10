"""OSYM aktiflestirme (0011) davranissal bekcisi -- gercek PostgreSQL ister.

10 Eyl 2026: kullanici "OSYM sorularini aktiflestir" dedi. Duz `is_active=true`
yetmezdi -- olcum gosterdi ki gercek servis kapisi (`v_safe_for_beta`,
core/quality_gate.py) uc alan daha ister (review_status, quality_review_status,
pipeline_metadata sinyali) ve FIZ/BIO/EDB kokleri sifir alt konuya sahipti
(bekci test_icerigi_olan_dersin_alt_konusu_vardir bu OSYM verisiyle ilk kez
tetiklenirdi). 0011 + D9 (backend/migrations/D9_*.sql) bunlari birlikte
cozdu. Bu dosya SONUCU dogrular (0011'in KENDI SQL'ini tekrarlamaz --
tekrarlamak, duzeltmeye calistigimiz kod<->view drift'inin ta kendisi olurdu).

Gercek Postgres yoksa ya da OSYM verisi henuz ithal edilmemisse SKIP olur;
sahte motorla (sqlite) YANLIS pozitif donmez (bkz. tests/e2e/pg_dsn.py).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [pytest.mark.golden_flow]

_KAYNAKLAR = ("OSYM 2025 TYT", "OSYM 2025 AYT")
_KOKLER = ("FIZ", "BIO", "EDB")


@pytest_asyncio.fixture
async def db_session():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erisilemiyor: {type(exc).__name__}")

    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


async def _osym_ids(session: AsyncSession) -> list[str]:
    result = await session.execute(
        text(
            "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "WHERE m.source_book = ANY(:kaynaklar)"
        ),
        {"kaynaklar": list(_KAYNAKLAR)},
    )
    return [str(r[0]) for r in result.fetchall()]


@pytest.mark.asyncio
async def test_osym_sorulari_aktif(db_session):
    """0011 sonrasi: OSYM kaynakli tum sorular is_active olmali."""
    ids = await _osym_ids(db_session)
    if not ids:
        pytest.skip("OSYM verisi yok -- henuz ithal edilmemis")
    pasif = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_bank "
                "WHERE id = ANY(:ids) AND is_active IS NOT TRUE"
            ),
            {"ids": ids},
        )
    ).scalar()
    assert pasif == 0, f"{pasif}/{len(ids)} OSYM sorusu hala pasif"


@pytest.mark.asyncio
async def test_osym_sorulari_kalite_kapisindan_geciyor(db_session):
    """OSYM sorulari v_safe_for_beta icinde olmali (D9 sinyali + 0011 flip)."""
    ids = await _osym_ids(db_session)
    if not ids:
        pytest.skip("OSYM verisi yok -- henuz ithal edilmemis")
    result = await db_session.execute(
        text(
            """
            SELECT x.id FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE NOT EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id)
            """
        ),
        {"ids": ids},
    )
    disari_kalan = [r[0] for r in result.fetchall()]
    assert not disari_kalan, (
        f"{len(disari_kalan)}/{len(ids)} OSYM sorusu kalite kapisi disinda "
        f"(D9 SQL'i uygulanmamis olabilir -- bkz backend/migrations/D9_*.sql). "
        f"Ornek: {disari_kalan[:3]}"
    )


@pytest.mark.asyncio
async def test_bos_kokler_artik_alt_konuya_sahip(db_session):
    """FIZ/BIO/EDB: OSYM aktiflestirmesi sonrasi en az bir alt konu olmali.

    test_mufredat_agaci_saglik.py::test_icerigi_olan_dersin_alt_konusu_vardir
    ile ayni sozlesmeyi, yalniz bu ucu icin, gercek Postgres'te dogrular.
    """
    result = await db_session.execute(
        text(
            """
            SELECT r.code,
                   (SELECT count(*) FROM topic_hierarchy c
                     WHERE c.parent_id = r.id AND c.is_active IS TRUE) AS alt_konu,
                   (SELECT count(*) FROM question_bank b
                      JOIN question_metadata m ON m.id = b.id
                     WHERE m.subject_area = upper(r.name_tr)
                       AND b.is_active IS TRUE) AS soru
              FROM topic_hierarchy r
             WHERE r.code = ANY(:kokler) AND r.parent_id IS NULL
            """
        ),
        {"kokler": list(_KOKLER)},
    )
    rows = result.fetchall()
    if not rows or all(r.soru == 0 for r in rows):
        pytest.skip("OSYM verisi yok -- FIZ/BIO/EDB henuz aktif soru icermiyor")
    bos = [r for r in rows if r.soru > 0 and r.alt_konu == 0]
    assert (
        not bos
    ), f"Alt konusu olmayan bos kok(ler): {[(r.code, r.soru) for r in bos]}"
