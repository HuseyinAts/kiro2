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

10 Eyl 2026 (ek): push-oncesi ders-zorlayici hook'u 28 satirin (dogru sikki
GORSEL/GRAFIK oldugu icin metni BOS olan sorular, pipeline_metadata->
'bayraklar' icinde 'sik_bos' ile isaretli) cevap anahtarinin gecersiz
oldugunu buldu -- bkz backend/migrations/D10_safe_for_beta_exclude_sik_bos.sql
ve backend/alembic/versions/0012_osym_sikki_bos_pasif.py. Bu yuzden asagidaki
"tum OSYM sorulari aktif/kapidan gecer" testleri artik sik_bos bayrakli
28 satiri BILEREK haric tutuyor (`_osym_ids_servis_edilebilir`); onlar icin
ayri, TERS yonlu bir bekci var (`test_osym_sik_bos_sorulari_kapi_disinda`).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

# BILEREK golden_flow ISARETSIZ: golden-flows.yml CI isi taze/tohumlanmis
# bir Postgres'e karsi kosuyor -- kitapcik_ithal.py (291 OSYM sorusunun
# GERCEK verisi) hicbir migration/seed script'inde degil, elle calistirilan
# bir ithalat script'i. Yani bu dosyanin 4 testi o iste HER ZAMAN
# "OSYM verisi yok" ile skip eder (yapisal, gecici degil) -- golden_flow
# skip-butcesini (azami 5, bkz pytest.ini) bosuna tuketirdi. 10 Eyl 2026
# CI kosusunda tam bunu yapti: onceki 4 pre-existing skip + bu dosyanin 4
# skip'i = 8 > 5, gate FIRLADI. Bu bekci GERCEK bir dev/staging DB'ye
# (OSYM verisi ithal edilmis) karsi elle/ayri bir is akisinda kosmak icin
# -- golden_flow'un "her PR'da tohumlanmis DB'ye karsi kosar" sozlesmesine
# uymuyor.

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


async def _osym_ids_servis_edilebilir(session: AsyncSession) -> list[str]:
    """Tum OSYM sorulari EKSI sik_bos bayrakli 28 satir (bkz D10/0012).

    NULL-guvenli: 'bayraklar' anahtari hic yoksa (bugun 291/291'de VAR ama
    ileride farkli bir kaynak icin olmayabilir) satir YANLISLIKLA disari
    atilmasin diye D10'daki ayni savunmaci OR deseni kullanilir.
    """
    result = await session.execute(
        text(
            "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "WHERE m.source_book = ANY(:kaynaklar) "
            "AND (m.pipeline_metadata IS NULL "
            "     OR NOT m.pipeline_metadata::jsonb ? 'bayraklar' "
            "     OR NOT (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')"
        ),
        {"kaynaklar": list(_KAYNAKLAR)},
    )
    return [str(r[0]) for r in result.fetchall()]


async def _osym_ids_sik_bos(session: AsyncSession) -> list[str]:
    """Dogru sikki gorsel/grafik oldugu icin metni bos olan OSYM sorulari."""
    result = await session.execute(
        text(
            "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "WHERE m.source_book = ANY(:kaynaklar) "
            "AND (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos'"
        ),
        {"kaynaklar": list(_KAYNAKLAR)},
    )
    return [str(r[0]) for r in result.fetchall()]


@pytest.mark.asyncio
async def test_osym_sorulari_aktif(db_session):
    """0011 sonrasi: sik_bos DISINDAKI tum OSYM sorulari is_active olmali.

    sik_bos bayrakli 28 satir BILEREK haric -- onlar icin ters yonlu bekci
    asagida (`test_osym_sik_bos_sorulari_kapi_disinda`).
    """
    ids = await _osym_ids_servis_edilebilir(db_session)
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
    assert pasif == 0, f"{pasif}/{len(ids)} servis-edilebilir OSYM sorusu hala pasif"


@pytest.mark.asyncio
async def test_osym_sorulari_kalite_kapisindan_geciyor(db_session):
    """sik_bos DISINDAKI OSYM sorulari v_safe_for_beta icinde olmali."""
    ids = await _osym_ids_servis_edilebilir(db_session)
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
        f"{len(disari_kalan)}/{len(ids)} servis-edilebilir OSYM sorusu kalite "
        f"kapisi disinda (D9 SQL'i uygulanmamis olabilir -- bkz "
        f"backend/migrations/D9_*.sql). Ornek: {disari_kalan[:3]}"
    )


@pytest.mark.asyncio
async def test_osym_sik_bos_sorulari_kapi_disinda(db_session):
    """Dogru sikki gorsel/grafik olan (metni bos) 28 soru kapi DISINDA kalmali.

    Ters yonlu bekci: test_k2_anahtar_dolu_bir_sikka_isaret_ediyor
    (integration/test_icerik_gecerliligi.py) bu sinifin hicbir ornegini
    mv_safe_for_beta'da tolere etmez -- burada ayni sozlesmeyi is_active +
    v_safe_for_beta uzerinden, D10/0012'nin SONUCUNU dogrulayarak tekrarlar.
    """
    ids = await _osym_ids_sik_bos(db_session)
    if not ids:
        pytest.skip("OSYM verisi yok ya da sik_bos bayrakli satir yok")
    aktif_kalan = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_bank "
                "WHERE id = ANY(:ids) AND is_active IS TRUE"
            ),
            {"ids": ids},
        )
    ).scalar()
    assert aktif_kalan == 0, (
        f"{aktif_kalan}/{len(ids)} sik_bos bayrakli soru hala is_active=true "
        "(0012 uygulanmamis olabilir)"
    )
    result = await db_session.execute(
        text(
            """
            SELECT x.id FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id)
            """
        ),
        {"ids": ids},
    )
    kapidan_gecen = [r[0] for r in result.fetchall()]
    assert not kapidan_gecen, (
        f"{len(kapidan_gecen)}/{len(ids)} sik_bos bayrakli soru hala kapidan "
        "geciyor (D10 uygulanmamis olabilir -- bkz "
        "backend/migrations/D10_safe_for_beta_exclude_sik_bos.sql). "
        f"Ornek: {kapidan_gecen[:3]}"
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
