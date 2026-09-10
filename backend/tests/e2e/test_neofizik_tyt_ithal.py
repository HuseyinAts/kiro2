"""Neofizik TYT ithalinin (0015 + neofizik_tyt_ithal.py) bekcisi.

TYT kitabi AYT'den iki noktada AYRILIR, bekciler bunu dogrular:

1. CEVAP KAYNAGI TEK: kitabin basili anahtari. Soru tekrar cozulmedi (urun
   karari), bu yuzden `explanation` NULL kalir ve metadata'da
   `cozum_dogrulamasi='yapilmadi_urun_karari'` izi durur. Uretilmemis bir
   cozumun sonradan "varmis gibi" gorunmesini bu bekci engeller.

2. TURETIK ALANLAR SABIT DEGIL: readability_score (Atesman) ve
   morphology_complexity repo'nun kendi servislerinden HESAPLANIR. AYT
   ithali bunlari 50.0 / 0.5 sabitiyle yazmisti; TYT'de tek bir sabit
   degere cokmediklerini olcen bekciler var.

Ithal PASIFTIR: is_active=FALSE, is_ai_generated=TRUE, review_status='PENDING'
-- yani hicbir satir `v_safe_for_beta` kapisindan gecmez. 0014'un AYT icin
yaptigi toplu beta onayi TYT icin HENUZ VERILMEDI; bekci bunu da dogrular,
boylece kapinin yanlislikla acilmasi sessiz kalmaz.

Bu dosya SONUCU dogrular -- ithal script'inin ya da view'in SQL'ini
tekrarlamaz.

Gercek Postgres yoksa ya da TYT verisi henuz ithal edilmemisse SKIP olur.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

# BILEREK golden_flow ISARETSIZ -- test_neofizik_ithal.py ile ayni gerekce:
# neofizik_tyt_ithal.py elle calistirilan bir ithalat script'i, hicbir
# migration ya da seed akisinda degil.

_KAYNAK = "Neofizik TYT Fizik Soru Bankasi"
_ASGARI = 800  # kitapta olculen 891; esik altinda kalmasi ithal kaybi demektir


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


async def _tyt_sayisi(session: AsyncSession) -> int:
    sonuc = await session.execute(
        text(
            "SELECT count(*) FROM question_bank b "
            "JOIN question_metadata m ON m.id = b.id WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    return int(sonuc.scalar() or 0)


async def _gerekli(session: AsyncSession) -> int:
    n = await _tyt_sayisi(session)
    if n == 0:
        pytest.skip(f"{_KAYNAK} henuz ithal edilmemis")
    return n


@pytest.mark.asyncio
async def test_neofizik_tyt_ithal_edildi(db_session: AsyncSession):
    """Kitabin sorulari DB'de ve sayi kitaptan olculen buyuklukte."""
    n = await _gerekli(db_session)
    assert n >= _ASGARI, f"beklenen >= {_ASGARI}, bulunan {n}"


@pytest.mark.asyncio
async def test_neofizik_tyt_pasif_ve_kapi_disinda(db_session: AsyncSession):
    """Ithal PASIF: aktif satir da, kapidan gecen satir da olmamali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE b.is_active), "
            "       count(*) FILTER (WHERE b.is_ai_generated IS NOT TRUE), "
            "       count(*) FILTER (WHERE b.review_status <> 'PENDING'), "
            "       count(*) FILTER (WHERE EXISTS ("
            "           SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id)) "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    aktif, ai_degil, onayli, kapida = sonuc.one()
    assert aktif == 0, f"{aktif} satir is_active -- pasif ithal sozlesmesi bozuldu"
    assert ai_degil == 0, f"{ai_degil} satirda is_ai_generated isareti dusmus"
    assert onayli == 0, f"{onayli} satirin review_status'u PENDING degil"
    assert kapida == 0, f"{kapida} satir v_safe_for_beta kapisindan geciyor"


@pytest.mark.asyncio
async def test_neofizik_tyt_anahtar_dolu_bir_sikka_isaret_ediyor(
    db_session: AsyncSession,
):
    """R5: cevap anahtari BOS OLMAYAN bir sikka isaret etmeli (sifir tolerans)."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FROM question_bank b "
            "  JOIN question_metadata m ON m.id = b.id "
            "  JOIN question_content c ON c.id = b.id "
            " WHERE m.source_book = :k AND ("
            "   c.correct_answer IS NULL OR btrim(coalesce(CASE c.correct_answer "
            "     WHEN 'A' THEN c.option_a WHEN 'B' THEN c.option_b "
            "     WHEN 'C' THEN c.option_c WHEN 'D' THEN c.option_d "
            "     WHEN 'E' THEN c.option_e END, '')) = '')"
        ),
        {"k": _KAYNAK},
    )
    assert sonuc.scalar() == 0


@pytest.mark.asyncio
async def test_neofizik_tyt_cozum_uretilmedi(db_session: AsyncSession):
    """Cevap yalnizca kitabin basili anahtarindan; uydurma cozum yazilmamis."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE c.explanation IS NOT NULL), "
            "       count(*) FILTER (WHERE m.pipeline_metadata->>'cozum_dogrulamasi' "
            "                        <> 'yapilmadi_urun_karari'), "
            "       count(*) FILTER (WHERE m.pipeline_metadata->>'cevap_kaynagi' "
            "                        <> 'kitap_anahtari') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "  JOIN question_content c ON c.id = b.id WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    aciklama, iz_yok, baska_kaynak = sonuc.one()
    assert aciklama == 0, f"{aciklama} satirda explanation dolu -- cozum uretilmedi"
    assert iz_yok == 0, f"{iz_yok} satirda cozum_dogrulamasi izi eksik/yanlis"
    assert (
        baska_kaynak == 0
    ), f"{baska_kaynak} satirin cevap kaynagi kitap anahtari degil"


@pytest.mark.asyncio
async def test_neofizik_tyt_okunabilirlik_hesaplanmis(db_session: AsyncSession):
    """readability tek bir sabite cokmemis; Atesman indeksi gercekten hesaplanmis."""
    n = await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(DISTINCT m.readability_score), "
            "       count(*) FILTER (WHERE m.readability_score = 50.0), "
            "       count(*) FILTER (WHERE m.readability_score IS NULL "
            "                           OR m.morphology_complexity IS NULL) "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    oku_cesit, sabit50, bos = sonuc.one()
    assert bos == 0, f"{bos} satirda turetik alan NULL"
    assert oku_cesit > 50, f"readability yalnizca {oku_cesit} farkli deger aliyor"
    assert sabit50 < n // 2, f"{sabit50}/{n} satir hala 50.0 sabitinde"


@pytest.mark.asyncio
async def test_neofizik_tyt_morfoloji_durustce_isaretli(db_session: AsyncSession):
    """Morfoloji Zemberek'siz hesaplandi ve SABIT cikti -- bu ACIKCA yazili olmali.

    Alan bilgi tasimiyor (bkz. ithal script docstring'i). Tehlike, ileride
    birinin bu sabiti "olculmus morfolojik karmasiklik" sanmasidir; bekci
    kaynak isaretinin dusmesini yakalar. Zemberek acilip --meta-guncelle
    kosuldugunda isaret degisecek ve bu test o degisikligi gorunur kilacak.
    """
    n = await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE m.pipeline_metadata->>'morfoloji_kaynagi' "
            "                        IS NULL), "
            "       count(DISTINCT m.pipeline_metadata->>'morfoloji_kaynagi'), "
            "       min(m.pipeline_metadata->>'morfoloji_kaynagi') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    isaretsiz, cesit, kaynak = sonuc.one()
    assert isaretsiz == 0, f"{isaretsiz}/{n} satirda morfoloji kaynak isareti yok"
    assert cesit == 1, f"{cesit} farkli morfoloji kaynagi -- karisik parti"
    assert kaynak.startswith(
        ("heuristik_", "zemberek_")
    ), f"taninmayan morfoloji kaynagi: {kaynak}"


@pytest.mark.asyncio
async def test_neofizik_tyt_sinav_turu_ve_yil(db_session: AsyncSession):
    """exam_type TYT; osym_year YALNIZ basili yil etiketi olan cikmis sorularda."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE m.exam_type <> 'TYT'), "
            "       count(*) FILTER (WHERE m.osym_year IS NOT NULL), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata->>'cikmis_soru')::bool), "
            "       count(*) FILTER (WHERE m.osym_year IS NOT NULL "
            "         AND (m.pipeline_metadata->>'cikmis_soru')::bool IS NOT TRUE) "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    tyt_disi, yil_dolu, cikmis, yanlis_damga = sonuc.one()
    assert tyt_disi == 0, f"{tyt_disi} satirin exam_type'i TYT degil"
    assert (
        yanlis_damga == 0
    ), f"{yanlis_damga} cikmis-olmayan soruya sinav yili damgasi vurulmus"
    assert (
        yil_dolu == cikmis
    ), f"cikmis soru {cikmis} ama yil dolu {yil_dolu} -- ikisi birebir olmali"


@pytest.mark.asyncio
async def test_neofizik_tyt_sorulari_yaprak_konuya_bagli(db_session: AsyncSession):
    """Her soru 0015'in kurdugu FIZ-NEOT yapraklarindan birine bagli olmali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FROM question_bank b "
            "  JOIN question_metadata m ON m.id = b.id "
            "  JOIN topic_hierarchy t ON t.id = b.primary_topic_id "
            " WHERE m.source_book = :k AND ("
            "   t.code NOT LIKE 'FIZ-NEOT-U%%-%%' OR EXISTS ("
            "     SELECT 1 FROM topic_hierarchy c WHERE c.parent_id = t.id))"
        ),
        {"k": _KAYNAK},
    )
    assert sonuc.scalar() == 0


@pytest.mark.asyncio
async def test_neofizik_tyt_gorsel_bayrakli_sorularda_varlik_kayitli(
    db_session: AsyncSession,
):
    """`gorsel` bayrakli sorularin buyuk cogunlugunda cikarilmis varlik olmali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE m.pipeline_metadata->'bayraklar' ? 'gorsel'), "
            "       count(*) FILTER (WHERE m.pipeline_metadata->'bayraklar' ? 'gorsel' "
            "         AND jsonb_array_length(m.pipeline_metadata->'gorsel_varliklar') > 0) "
            "  FROM question_bank b "
            "  JOIN (SELECT id, pipeline_metadata::jsonb AS pipeline_metadata, source_book "
            "          FROM question_metadata) m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    bayrakli, varlikli = sonuc.one()
    if bayrakli == 0:
        pytest.skip("gorsel bayrakli soru yok")
    assert (
        varlikli / bayrakli >= 0.80
    ), f"gorsel bayrakli {bayrakli} sorunun yalnizca {varlikli}'sinde varlik var"
