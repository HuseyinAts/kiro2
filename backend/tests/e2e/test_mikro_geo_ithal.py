"""Mikro Orijinal AYT Geometri ithalinin (0017) bekcisi.

11 Eyl 2026: 1213 geometri sorusu OCR/VLM hattiyla cikarilip PASIF ithal
edildi. Bu dosya ithalin SONUCUNU dogrular -- migration'in ya da view'in
SQL'ini tekrarlamaz.

BU KITABIN NEOFIZIK'TEN AYRILDIGI UC NOKTA -- BEKCILER BUNU KORUR

1. CEVAP ESLEMESI KONUMSALDIR. Serit girdisi <-> kirpim eslemesi SIRAYA
   dayanir, basili numaraya DEGIL. Bunun onemi s77'de gorulur: sayfada
   basili numaralar 6,7,8,9 iken yayinevinin cevap seridi 7,8,9,10 diyor
   (dizgi hatasi; onceki sayfa 1-5'te bitiyor). Biri sonradan "numaraya
   gore eslendi" diye yazarsa o beyan YANLIS olur. Bir bekci
   `cevap_eslemesi='konumsal_serit_sirasi'` izini ve sapmanin yalnizca
   bilinen 4 satirda isaretli oldugunu dogrular.

2. GORSEL TAM SORU KIRPIMIDIR. Sorularin %88'i sekil iceriyor ve sekil
   olmadan soru eksik. Neofizik'teki gibi varlik duzeyinde ayristirma
   YAPILMADI; bu bilerek boyle ve `gorsel_kaynagi='tam_soru_kirpimi'` ile
   isaretli. Kirpim kutusu kaybolursa gorseller bir daha uretilemez --
   bir bekci her satirda 4 elemanli kutunun durdugunu dogrular.

3. ITHAL HENUZ PASIF. Neofizik'te (0014/0016) urun sahibi toplu beta onayi
   verdi; geometride BOYLE BIR KARAR HENUZ YOK. Bir bekci hicbir satirin
   kapidan gecmedigini ve hicbir satirda toplu-onay izi olmadigini
   dogrular -- Neofizik'in gerekcesi kopyala-yapistir ile buraya
   kaymasin diye.

Gercek Postgres yoksa ya da veri henuz ithal edilmemisse SKIP olur;
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
# mikro_geo_ithal.py elle calistirilan bir ithalat script'i, hicbir
# migration ya da seed akisinda degil.

_KAYNAK = "Mikro Orijinal 2025 AYT Geometri Soru Bankasi"
_ASGARI = 1150  # kitapta olculen 1213; esik altinda kalmasi ithal kaybi demektir
_SAPMA_SAYFASI = 77  # yayinevinin serit numarasi kaydirdigi tek sayfa
_SAPMA_ADEDI = 4


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


async def _sayi(session: AsyncSession) -> int:
    sonuc = await session.execute(
        text(
            "SELECT count(*) FROM question_bank b "
            "JOIN question_metadata m ON m.id = b.id WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    return int(sonuc.scalar() or 0)


async def _gerekli(session: AsyncSession) -> int:
    n = await _sayi(session)
    if n == 0:
        pytest.skip(f"{_KAYNAK} henuz ithal edilmemis")
    return n


@pytest.mark.asyncio
async def test_mikro_geo_ithal_edildi(db_session: AsyncSession):
    """Kitabin sorulari DB'de ve sayi kitaptan olculen buyuklukte."""
    n = await _gerekli(db_session)
    assert n >= _ASGARI, f"beklenen >= {_ASGARI}, bulunan {n}"


@pytest.mark.asyncio
async def test_mikro_geo_pasif_ithal_sozlesmesi(db_session: AsyncSession):
    """PASIF ithal: aktif degil, acik degil, AI isaretli, incelenmemis."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE b.is_active IS TRUE), "
            "       count(*) FILTER (WHERE b.is_public IS TRUE), "
            "       count(*) FILTER (WHERE b.is_ai_generated IS NOT TRUE), "
            "       count(*) FILTER (WHERE b.review_status <> 'PENDING') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    aktif, acik, ai_isaretsiz, onayli = sonuc.one()
    assert aktif == 0, f"{aktif} geometri satiri is_active=true"
    assert acik == 0, f"{acik} geometri satiri is_public=true"
    assert ai_isaretsiz == 0, (
        f"{ai_isaretsiz} satirda is_ai_generated=true degil -- "
        "OCR kaynakli icerik AI uretimi olarak isaretli KALMALI"
    )
    assert onayli == 0, f"{onayli} satirin review_status'u PENDING degil"


@pytest.mark.asyncio
async def test_mikro_geo_hicbiri_kapidan_gecmiyor(db_session: AsyncSession):
    """Toplu beta onayi HENUZ VERILMEDI -- hicbir satir servis kapisindan gecmez."""
    await _gerekli(db_session)
    gecen = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_bank b "
                "  JOIN question_metadata m ON m.id = b.id "
                " WHERE m.source_book = :k "
                "   AND EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id)"
            ),
            {"k": _KAYNAK},
        )
    ).scalar()
    assert gecen == 0, (
        f"{gecen} geometri sorusu v_safe_for_beta'dan geciyor -- "
        "bu kitap icin toplu onay karari verilmedi"
    )


@pytest.mark.asyncio
async def test_mikro_geo_toplu_onay_izi_yok(db_session: AsyncSession):
    """Neofizik'in toplu onay gerekcesi buraya KOPYALANMAMIS olmali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            # IS DISTINCT FROM degil: burada anahtarin HIC OLMAMASINI
            # bekliyoruz, bu yuzden dogrudan varligina bakilir.
            "SELECT count(*) FILTER (WHERE m.pipeline_metadata::jsonb ? 'onay_turu'), "
            "       count(*) FILTER (WHERE m.pipeline_metadata::jsonb ? "
            "                        'konsensus_sinyalleri'), "
            "       count(*) FILTER (WHERE s.quality_review_status <> 'pending') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "  JOIN question_statistics s ON s.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    onay, sinyal, kalite = sonuc.one()
    assert onay == 0, f"{onay} satirda onay_turu izi var -- toplu onay verilmedi"
    assert sinyal == 0, (
        f"{sinyal} satirda konsensus_sinyalleri var -- Neofizik'in gerekcesi "
        "geometriye kaydirilmis olabilir"
    )
    assert kalite == 0, f"{kalite} satirin quality_review_status'u pending degil"


@pytest.mark.asyncio
async def test_mikro_geo_anahtar_dolu_bir_sikka_isaret_ediyor(
    db_session: AsyncSession,
):
    """R5: cevap anahtari BOS OLMAYAN bir sikki gostermeli (sifir tolerans)."""
    await _gerekli(db_session)
    bozuk = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_content c "
                "  JOIN question_metadata m ON m.id = c.id "
                " WHERE m.source_book = :k AND ("
                "   c.correct_answer IS NULL OR btrim(coalesce("
                "     CASE upper(c.correct_answer) "
                "       WHEN 'A' THEN c.option_a WHEN 'B' THEN c.option_b "
                "       WHEN 'C' THEN c.option_c WHEN 'D' THEN c.option_d "
                "       WHEN 'E' THEN c.option_e END, '')) = '')"
            ),
            {"k": _KAYNAK},
        )
    ).scalar()
    assert bozuk == 0, f"{bozuk} geometri sorusunda anahtar bos sikka isaret ediyor"


@pytest.mark.asyncio
async def test_mikro_geo_cevap_eslemesi_konumsal(db_session: AsyncSession):
    """Esleme yontemi DB'de yaziyor ve KONUMSAL -- numaraya gore degil."""
    await _gerekli(db_session)
    yanlis = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_metadata m "
                " WHERE m.source_book = :k AND (m.pipeline_metadata::jsonb ->> "
                "       'cevap_eslemesi') IS DISTINCT FROM 'konumsal_serit_sirasi'"
            ),
            {"k": _KAYNAK},
        )
    ).scalar()
    assert yanlis == 0, (
        f"{yanlis} satirda cevap_eslemesi izi yok ya da farkli -- s77'deki "
        "yayinevi numara kaymasi yuzunden bu ayrim ANLAMLI"
    )


@pytest.mark.asyncio
async def test_mikro_geo_numara_sapmasi_yalnizca_bilinen_sayfada(
    db_session: AsyncSession,
):
    """Serit numarasi <-> basili numara sapmasi SADECE s77'nin 4 sorusunda."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'anahtar_numara_sapmasi') = 'true'), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'anahtar_numara_sapmasi') = 'true' AND m.source_page = :s), "
            "       count(*) FILTER (WHERE NOT (m.pipeline_metadata::jsonb ? "
            "         'anahtar_numara_sapmasi')) "
            "  FROM question_metadata m WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK, "s": _SAPMA_SAYFASI},
    )
    toplam, sayfada, izsiz = sonuc.one()
    assert izsiz == 0, f"{izsiz} satirda anahtar_numara_sapmasi anahtari yok"
    assert toplam == _SAPMA_ADEDI, (
        f"sapma isaretli satir {toplam}, beklenen {_SAPMA_ADEDI} -- "
        "yeni bir kayma olustu ya da bilinen kayma silindi"
    )
    assert (
        sayfada == _SAPMA_ADEDI
    ), f"sapmalarin {sayfada} tanesi s{_SAPMA_SAYFASI}'de; hepsi orada olmali"


@pytest.mark.asyncio
async def test_mikro_geo_cozum_uretilmedi(db_session: AsyncSession):
    """Cozum uretilmedi; uretilmis gibi gorunmemeli."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE btrim(coalesce(c.explanation, '')) <> ''), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'cozum_dogrulamasi') IS DISTINCT FROM 'yapilmadi_urun_karari') "
            "  FROM question_content c JOIN question_metadata m ON m.id = c.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    cozumlu, izsiz = sonuc.one()
    assert cozumlu == 0, f"{cozumlu} satirda explanation dolu -- cozum uretilmedi"
    assert izsiz == 0, f"{izsiz} satirda cozum_dogrulamasi izi yok"


@pytest.mark.asyncio
async def test_mikro_geo_kirpim_kutusu_saklanmis(db_session: AsyncSession):
    """Gorseller PDF'ten yeniden uretilebilir kalmali: kutu 4 elemanli olmali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE jsonb_array_length(coalesce("
            "         m.pipeline_metadata::jsonb -> 'kirpim_kutusu', '[]'::jsonb)) <> 4), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'gorsel_kaynagi') IS DISTINCT FROM 'tam_soru_kirpimi'), "
            "       count(*) FILTER (WHERE coalesce(c.question_image_url, '') "
            "         NOT LIKE '/static/crops/MIKRO_GEO/%') "
            "  FROM question_metadata m JOIN question_content c ON c.id = m.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    kutusuz, izsiz, yolsuz = sonuc.one()
    assert kutusuz == 0, f"{kutusuz} satirda 4 elemanli kirpim kutusu yok"
    assert izsiz == 0, f"{izsiz} satirda gorsel_kaynagi izi yok"
    assert yolsuz == 0, f"{yolsuz} satirda question_image_url beklenen yolda degil"


@pytest.mark.asyncio
async def test_mikro_geo_okunabilirlik_hesaplanmis(db_session: AsyncSession):
    """readability_score sabit degil, metinden hesaplanmis olmali."""
    n = await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(DISTINCT m.readability_score), "
            "       count(*) FILTER (WHERE m.readability_score IS NULL) "
            "  FROM question_metadata m WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    farkli, bos = sonuc.one()
    assert bos == 0, f"{bos} satirda readability_score NULL"
    assert farkli > max(20, n // 50), (
        f"readability_score yalnizca {farkli} farkli deger aliyor -- "
        "hesaplanmamis, sabit yazilmis olabilir"
    )


@pytest.mark.asyncio
async def test_mikro_geo_morfoloji_durustce_isaretli(db_session: AsyncSession):
    """Zemberek yok; deger heuristik ve OLCUM DEGIL -- kaynagi yazili olmali."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'morfoloji_kaynagi') IS DISTINCT FROM "
            "         'heuristik_zemberek_yok_sabit'), "
            "       count(DISTINCT m.morphology_complexity) "
            "  FROM question_metadata m WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    izsiz, farkli = sonuc.one()
    assert izsiz == 0, (
        f"{izsiz} satirda morfoloji_kaynagi izi yok -- heuristik deger olcum "
        "sanilabilir"
    )
    assert farkli <= 3, (
        f"morphology_complexity {farkli} farkli deger aliyor; heuristik yol "
        "{0.0, 0.35} uretir. Zemberek acildiysa bu bekci guncellenmeli."
    )


@pytest.mark.asyncio
async def test_mikro_geo_sinav_turu_ve_yil(db_session: AsyncSession):
    """AYT/GEOMETRI; osym_year YALNIZCA rozetli sorularda dolu."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE m.exam_type <> 'AYT'), "
            "       count(*) FILTER (WHERE m.subject_area <> 'GEOMETRI'), "
            "       count(*) FILTER (WHERE m.osym_year IS NOT NULL AND "
            "         (m.pipeline_metadata::jsonb ->> 'cikmis_soru') <> 'true'), "
            "       count(*) FILTER (WHERE m.osym_year IS NULL AND "
            "         (m.pipeline_metadata::jsonb ->> 'cikmis_soru') = 'true') "
            "  FROM question_metadata m WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    tur, alan, fazla, eksik = sonuc.one()
    assert tur == 0, f"{tur} satirda exam_type AYT degil"
    assert alan == 0, f"{alan} satirda subject_area GEOMETRI degil"
    assert fazla == 0, (
        f"{fazla} satirda rozet yokken osym_year dolu -- yayinevinin kendi "
        "sorusuna OSYM damgasi vurulmus"
    )
    assert eksik == 0, f"{eksik} rozetli satirda osym_year bos"


@pytest.mark.asyncio
async def test_mikro_geo_sorulari_yaprak_konuya_bagli(db_session: AsyncSession):
    """Her soru 0017'nin kurdugu GEO-MIKRO yapragina bagli olmali, koke degil."""
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE t.code IS NULL), "
            "       count(*) FILTER (WHERE t.code NOT LIKE 'GEO-MIKRO-U%-%'), "
            "       count(DISTINCT t.code) "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "  LEFT JOIN topic_hierarchy t ON t.id = b.primary_topic_id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    konusuz, yaprak_disi, farkli = sonuc.one()
    assert konusuz == 0, f"{konusuz} sorunun primary_topic_id'si cozulmuyor"
    assert yaprak_disi == 0, (
        f"{yaprak_disi} soru GEO-MIKRO yapragina degil baska bir dugume bagli "
        "(0017 kosmadiysa GEO kokune dusmus olabilir)"
    )
    assert farkli >= 25, f"sorular yalnizca {farkli} farkli konuya dagilmis"


@pytest.mark.asyncio
async def test_mikro_geo_ayni_hash_li_yabanci_satirlar_bozulmamis(
    db_session: AsyncSession,
):
    """soru_hash carpismasi olan satirlar KENDI kaynaginda kalmali.

    Bu kitaptaki iki soru resmi "OSYM 2025 TYT" kitapciginda da var; metin ve
    besi de sik birebir ayni oldugu icin soru_hash ve dolayisiyla id de ayni.
    O satirlar OSYM ithaliyle yazildi, OSYM kaynagina ait ve AKTIF.

    11 Eyl 2026'da mikro_geo_ithal.py --meta-guncelle kaynak ayrimi yapmadigi
    icin bu iki satirin pipeline_metadata'sini ezdi; osym_resmi_kaynak sinyali
    kayboldu ve ikisi de v_safe_for_beta'dan DUSTU. Bu bekci o regresyonun
    tekrarini yakalar: OSYM kaynakli hicbir satir geometri hattinin izini
    tasimamali.
    """
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FROM question_metadata m "
            " WHERE m.source_book <> :k "
            "   AND (m.pipeline_metadata::jsonb ->> 'ithal_araci') "
            "       = 'scripts/kitap/mikro_geo_ithal.py'"
        ),
        {"k": _KAYNAK},
    )
    sizan = sonuc.scalar()
    assert sizan == 0, (
        f"{sizan} satir baska bir kaynaga ait oldugu halde geometri hattinin "
        "ithal_araci izini tasiyor -- --meta-guncelle yabanci satira dokunmus"
    )
