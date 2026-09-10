"""Neofizik pasif ithalinin (0013 + scripts/kitap/neofizik_ithal.py) bekcisi.

10 Eyl 2026: Neofizik AYT Fizik Soru Bankasi 2025'in 1218 sorusu OCR/VLM
hattiyla cikarilip question_bank'a PASIF ithal edildi. Metin insan gozuyle
onaylanmadigi icin ithal sozlesmesi su: her satir `is_active=false`,
`is_ai_generated=true`, `review_status='PENDING'`.

Kapinin (`v_safe_for_beta`, D9/D10) sozlesmesi
`(is_ai_generated = false OR review_status = 'APPROVED')` istiyor; iki alan
birlikte bu satirlari kapinin DISINDA tutuyor. Bu dosya SONUCU dogrular --
ithal script'inin ya da view'in SQL'ini tekrarlamaz (tekrarlamak, D9/D10
sirasinda duzeltmeye calistigimiz kod<->view drift'inin ta kendisi olurdu).

Ayrica 0012'nin acikca gosterdigi dersi burada ONCEDEN uyguluyoruz: cevap
anahtarinin dolu bir sikka isaret etmesi (R5) ithal ANINDA denetlenir
(neofizik_ithal.py::_on_kontrol) ve burada bir kez daha DB uzerinde
dogrulanir -- OSYM'de bu kontrol ithal sonrasi kesfedilmisti.

Gercek Postgres yoksa ya da Neofizik verisi henuz ithal edilmemisse SKIP
olur; sahte motorla (sqlite) YANLIS pozitif donmez (bkz tests/e2e/pg_dsn.py).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

# BILEREK golden_flow ISARETSIZ -- test_osym_aktiflestirme.py ile ayni gerekce:
# neofizik_ithal.py elle calistirilan bir ithalat script'i, hicbir migration
# ya da seed akisinda degil. golden-flows.yml taze/tohumlanmis Postgres'e
# karsi kostugu icin bu dosya orada HER ZAMAN skip ederdi ve skip-butcesini
# (azami 5, bkz pytest.ini) bosuna tuketirdi.

_KAYNAK = "Neofizik AYT Fizik Soru Bankasi 2025"


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
        raise  # pytest.skip() zaten firlatir -- akis analizi icin acik hale getirir

    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


async def _neofizik_ids(session: AsyncSession) -> list[str]:
    sonuc = await session.execute(
        text(
            "SELECT b.id FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "WHERE m.source_book = :kaynak"
        ),
        {"kaynak": _KAYNAK},
    )
    return [r[0] for r in sonuc.fetchall()]


@pytest.mark.asyncio
async def test_neofizik_ithal_edildi(db_session):
    """Ithal gerceklesti ve her satirin metni + 5 sikki + cevabi var."""
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    eksik = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FROM question_content c
                 WHERE c.id = ANY(:ids)
                   AND (btrim(coalesce(c.question_text, '')) = ''
                        OR btrim(coalesce(c.option_a, '')) = ''
                        OR btrim(coalesce(c.option_b, '')) = ''
                        OR btrim(coalesce(c.option_c, '')) = ''
                        OR btrim(coalesce(c.option_d, '')) = ''
                        OR btrim(coalesce(c.option_e, '')) = ''
                        OR c.correct_answer IS NULL)
                """
            ),
            {"ids": ids},
        )
    ).scalar()
    assert eksik == 0, f"{eksik} Neofizik satirinda metin/sik/cevap eksik"


@pytest.mark.asyncio
async def test_neofizik_sorulari_pasif_ve_ai_isaretli(db_session):
    """Ithal sozlesmesi: is_active=false, is_ai_generated=true, review_status='PENDING'."""
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    satir = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FILTER (WHERE b.is_active IS TRUE)            AS aktif,
                       count(*) FILTER (WHERE b.is_public IS TRUE)            AS acik,
                       count(*) FILTER (WHERE b.is_ai_generated IS NOT TRUE)  AS ai_isaretsiz,
                       count(*) FILTER (WHERE b.review_status <> 'PENDING')   AS beklemiyor
                  FROM question_bank b WHERE b.id = ANY(:ids)
                """
            ),
            {"ids": ids},
        )
    ).one()
    assert satir.aktif == 0, f"{satir.aktif} Neofizik satiri is_active=true"
    assert satir.acik == 0, f"{satir.acik} Neofizik satiri is_public=true"
    assert satir.ai_isaretsiz == 0, (
        f"{satir.ai_isaretsiz} satirda is_ai_generated=true degil -- "
        "OCR kaynakli icerik AI uretimi olarak isaretlenmeli"
    )
    assert (
        satir.beklemiyor == 0
    ), f"{satir.beklemiyor} satirda review_status 'PENDING' degil"


@pytest.mark.asyncio
async def test_neofizik_sorulari_kapidan_gecmiyor(db_session):
    """Asil bekci: hicbir Neofizik satiri servis kapisindan (v_safe_for_beta) gecmemeli."""
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    sonuc = await db_session.execute(
        text(
            "SELECT x.id FROM unnest(CAST(:ids AS text[])) AS x(id) "
            "WHERE EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id) "
            "LIMIT 5"
        ),
        {"ids": ids},
    )
    sizanlar = [r[0] for r in sonuc.fetchall()]
    assert not sizanlar, (
        f"{len(sizanlar)}+ Neofizik sorusu kapidan gecti -- insan onayi olmadan "
        f"servis edilebilir durumda: {sizanlar}"
    )


@pytest.mark.asyncio
async def test_neofizik_anahtar_dolu_bir_sikka_isaret_ediyor(db_session):
    """R5 (0012'nin dersi): dogru cevap harfinin isaret ettigi sik BOS olamaz."""
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    bozuk = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FROM question_content c
                 WHERE c.id = ANY(:ids)
                   AND (c.correct_answer IS NULL
                        OR c.correct_answer NOT IN ('A','B','C','D','E')
                        OR btrim(coalesce(CASE c.correct_answer
                                WHEN 'A' THEN c.option_a WHEN 'B' THEN c.option_b
                                WHEN 'C' THEN c.option_c WHEN 'D' THEN c.option_d
                                WHEN 'E' THEN c.option_e END, '')) = '')
                """
            ),
            {"ids": ids},
        )
    ).scalar()
    assert bozuk == 0, f"{bozuk} Neofizik satirinda cevap anahtari gecersiz (R5)"


@pytest.mark.asyncio
async def test_neofizik_sorulari_yaprak_konuya_bagli(db_session):
    """0013 agaci kuruldu: sorular FIZ kokune degil, FIZ-NEO-* yapragina bagli."""
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    kokte = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FROM question_bank b
                  JOIN topic_hierarchy t ON t.id = b.primary_topic_id
                 WHERE b.id = ANY(:ids) AND t.code NOT LIKE 'FIZ-NEO-%'
                """
            ),
            {"ids": ids},
        )
    ).scalar()
    assert kokte == 0, (
        f"{kokte} Neofizik sorusu FIZ-NEO-* yapragina bagli degil "
        "(0013 migration kosmadan mi ithal edildi?)"
    )


@pytest.mark.asyncio
async def test_neofizik_gorsel_bayrakli_sorularda_varlik_kayitli(db_session):
    """Sekle atif yapan sorularda gorsel varlik referansi bulunmali.

    902 sorunun koku sekle atif yapiyor; metin tek basina yeterli degil.
    pipeline_metadata->'gorsel_varliklar' bos ise soru ileride aktiflestirilse
    bile ogrenciye eksik gosterilir -- OSYM'deki sik_bos hatasinin ayni sinifi.
    """
    ids = await _neofizik_ids(db_session)
    if not ids:
        pytest.skip("Neofizik verisi ithal edilmemis")

    satir = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FILTER (
                          WHERE (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'gorsel')  AS gorselli,
                       count(*) FILTER (
                          WHERE (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'gorsel'
                            AND jsonb_array_length(
                                coalesce(m.pipeline_metadata::jsonb -> 'gorsel_varliklar',
                                         '[]'::jsonb)) = 0)                              AS varliksiz
                  FROM question_metadata m WHERE m.id = ANY(:ids)
                """
            ),
            {"ids": ids},
        )
    ).one()
    if not satir.gorselli:
        pytest.skip("gorsel bayrakli Neofizik sorusu yok")
    oran = satir.varliksiz / satir.gorselli
    assert oran <= 0.05, (
        f"gorsel bayrakli {satir.gorselli} sorunun {satir.varliksiz} tanesinde "
        f"(%{100 * oran:.1f}) gorsel varlik referansi yok"
    )
