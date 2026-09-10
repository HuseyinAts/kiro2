"""Neofizik TYT ithalinin (0015) ve beta toplu onayinin (0016) bekcisi.

10 Eyl 2026: 891 TYT sorusu OCR/VLM hattiyla cikarilip PASIF ithal edildi
(0015). Ayni gun urun sahibi bireysel insan denetimini ATLAYIP toplu denetimi
beta surumune ertelemeye karar verdi (0016): `sik_bos` bayragi TASIMAYAN 827
satir artik `is_active=true`, `review_status='APPROVED'`,
`quality_review_status='auto_judged_high'` -- yani kapidan GECIYORLAR.
`is_ai_generated` true KALIR.

TYT'nin AYT'DEN AYRILDIGI IKI NOKTA -- BEKCILER BUNU KORUR

1. CEVAP KAYNAGI TEK: kitabin basili anahtari. Sorular tekrar cozulmedi
   (urun karari), bu yuzden `explanation` NULL kalir ve her satirda
   `cozum_dogrulamasi='yapilmadi_urun_karari'` izi durur. Uretilmemis bir
   cozumun sonradan "varmis gibi" gorunmesini bir bekci engeller.

2. KONSENSUS GEREKCESI FARKLI. 0014 (AYT) `auto_judged_high`i cift okuma VE
   bagimsiz cozum-dogrulamasina dayandirmisti. TYT'de cozum dogrulamasi YOK;
   iki sinyal cift bagimsiz okuma ve basili anahtarin capraz kontrolu.
   Bir bekci `konsensus_sinyalleri` listesinin AYT'nin gerekcesine
   kaydirilmadigini dogrular -- kopyala-yapistir ile yanlis bir kalite
   beyani olusmasin diye.

Bu dosya SONUCU dogrular -- migration'in ya da view'in SQL'ini tekrarlamaz
(tekrarlamak, D9/D10'da duzeltmeye calistigimiz kod<->view drift'inin ta
kendisi olurdu).

Gercek Postgres yoksa ya da TYT verisi henuz ithal edilmemisse SKIP olur;
sahte motorla (sqlite) YANLIS pozitif donmez (bkz tests/e2e/pg_dsn.py).
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
_SINYALLER = ["cift_bagimsiz_okuma", "basili_anahtar_capraz_kontrolu"]


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


async def _bolunmus(session: AsyncSession) -> tuple[list[str], list[str]]:
    """(sik_bos TASIMAYAN idler, sik_bos TASIYAN idler)."""
    sonuc = await session.execute(
        text(
            "SELECT b.id, (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos' "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    temiz: list[str] = []
    bos: list[str] = []
    for sid, sik_bos in sonuc.fetchall():
        (bos if sik_bos else temiz).append(sid)
    return temiz, bos


@pytest.mark.asyncio
async def test_neofizik_tyt_ithal_edildi(db_session: AsyncSession):
    """Kitabin sorulari DB'de ve sayi kitaptan olculen buyuklukte."""
    n = await _gerekli(db_session)
    assert n >= _ASGARI, f"beklenen >= {_ASGARI}, bulunan {n}"


@pytest.mark.asyncio
async def test_neofizik_tyt_ai_isareti_korunuyor(db_session: AsyncSession):
    """0016 kapiyi acti ama KOKENI gizlemedi: is_ai_generated hala true.

    Kapidan gecirmenin kolay ama yanlis yolu `is_ai_generated=false` yazmakti
    (view'in oteki kolu). O yol DB'ye yanlis bir kaynak beyani birakirdi.
    """
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE b.is_ai_generated IS NOT TRUE), "
            "       count(*) FILTER (WHERE b.is_public IS TRUE) "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    ai_isaretsiz, acik = sonuc.one()
    assert ai_isaretsiz == 0, (
        f"{ai_isaretsiz} satirda is_ai_generated=true degil -- "
        "OCR kaynakli icerik AI uretimi olarak isaretli KALMALI"
    )
    assert acik == 0, f"{acik} TYT satiri is_public=true"


@pytest.mark.asyncio
async def test_neofizik_tyt_temiz_sorular_kapidan_geciyor(db_session: AsyncSession):
    """0016 sonrasi sozlesme: sik_bos TASIMAYAN her satir kapidan gecmeli."""
    temiz, _ = await _bolunmus(db_session)
    if not temiz:
        pytest.skip("TYT verisi ithal edilmemis")
    gecmeyen = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM unnest(CAST(:ids AS text[])) AS x(id) "
                "WHERE NOT EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id)"
            ),
            {"ids": temiz},
        )
    ).scalar()
    assert gecmeyen == 0, (
        f"{len(temiz)} temiz TYT sorusundan {gecmeyen} tanesi kapidan GECMIYOR "
        "-- 0016 kosmadi mi, yoksa kapi mi degisti?"
    )


@pytest.mark.asyncio
async def test_neofizik_tyt_sik_bos_sorulari_kapi_disinda(db_session: AsyncSession):
    """D10 kurali bozulmadi: sikki gorsel olan satirlar kapidan GECMEZ."""
    _, bos = await _bolunmus(db_session)
    if not bos:
        pytest.skip("sik_bos bayrakli TYT sorusu yok")
    gecen = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM unnest(CAST(:ids AS text[])) AS x(id) "
                "WHERE EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id)"
            ),
            {"ids": bos},
        )
    ).scalar()
    assert gecen == 0, (
        f"{gecen} sik_bos bayrakli TYT sorusu kapidan geciyor -- "
        "metin tabanli sunumda sikki eksik gorunur"
    )


@pytest.mark.asyncio
async def test_neofizik_tyt_toplu_onay_izi_kayitli(db_session: AsyncSession):
    """Toplu onay, bireysel denetimden AYIRT EDILEBILIR kalmali."""
    temiz, _ = await _bolunmus(db_session)
    if not temiz:
        pytest.skip("TYT verisi ithal edilmemis")
    sonuc = await db_session.execute(
        text(
            # IS DISTINCT FROM: anahtar HIC YOKSA ->> NULL doner ve duz <>
            # karsilastirmasi NULL uretir; FILTER onu saymaz, yani iz hic
            # yokken bekci YESIL kalirdi. 0016 oncesi kosumda tam olarak bu
            # goruldu ve boyle duzeltildi.
            "SELECT count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> 'onay_turu') "
            "                        IS DISTINCT FROM 'toplu_beta_sahibi'), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "                        'bireysel_denetim_yapildi') IS DISTINCT FROM 'false'), "
            "       count(*) FILTER (WHERE s.quality_review_status = 'human_verified') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "  LEFT JOIN question_statistics s ON s.id = b.id "
            " WHERE b.id = ANY(:ids)"
        ),
        {"ids": temiz},
    )
    onay_yok, denetim_yanlis, insan = sonuc.one()
    assert onay_yok == 0, f"{onay_yok} satirda onay_turu izi eksik/yanlis"
    assert (
        denetim_yanlis == 0
    ), f"{denetim_yanlis} satirda bireysel_denetim_yapildi=false degil"
    assert insan == 0, (
        f"{insan} satir 'human_verified' isaretli -- hicbir insan bu sorulari "
        "tek tek dogrulamadi"
    )


@pytest.mark.asyncio
async def test_neofizik_tyt_konsensus_gerekcesi_ayt_ye_kaymamis(
    db_session: AsyncSession,
):
    """TYT'nin iki sinyali AYT'ninkiyle AYNI DEGIL; beyan da ayni olmamali.

    0014 (AYT) `auto_judged_high`i cift okuma VE bagimsiz cozum-dogrulamasina
    dayandirmisti. TYT'de cozum dogrulamasi hic yapilmadi. Biri 0014'u
    kopyalayip TYT'ye uygularsa DB'de gercek olmayan bir kalite beyani
    olusur; bu bekci tam olarak onu yakalar.
    """
    temiz, _ = await _bolunmus(db_session)
    if not temiz:
        pytest.skip("TYT verisi ithal edilmemis")
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE NOT (m.pipeline_metadata::jsonb "
            "                        ? 'konsensus_sinyalleri')), "
            "       count(DISTINCT m.pipeline_metadata::jsonb ->> "
            "                      'konsensus_sinyalleri'), "
            "       min(m.pipeline_metadata::jsonb ->> 'konsensus_sinyalleri'), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "                        'cozum_dogrulamasi') "
            "                        IS DISTINCT FROM 'yapilmadi_urun_karari') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE b.id = ANY(:ids)"
        ),
        {"ids": temiz},
    )
    sinyalsiz, cesit, liste, cozum_iddiasi = sonuc.one()
    assert sinyalsiz == 0, f"{sinyalsiz} satirda konsensus_sinyalleri yok"
    assert cesit == 1, f"{cesit} farkli sinyal listesi -- karisik parti"
    for beklenen in _SINYALLER:
        assert beklenen in (liste or ""), f"sinyal listesinde {beklenen} yok: {liste}"
    assert "cozum" not in (
        liste or ""
    ), f"sinyal listesi cozum dogrulamasi iddia ediyor ama yapilmadi: {liste}"
    assert (
        cozum_iddiasi == 0
    ), f"{cozum_iddiasi} satirda cozum_dogrulamasi izi degistirilmis"


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
            "       count(*) FILTER (WHERE (m.pipeline_metadata->>'cozum_dogrulamasi') "
            "                        IS DISTINCT FROM 'yapilmadi_urun_karari'), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata->>'cevap_kaynagi') "
            "                        IS DISTINCT FROM 'kitap_anahtari') "
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
    kaynak isaretinin dusmesini yakalar.
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
            "SELECT count(*) FILTER (WHERE m.exam_type IS DISTINCT FROM 'TYT'), "
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
