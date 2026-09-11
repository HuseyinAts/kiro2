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

3. TOPLU BETA ONAYI VERILDI (0018). Urun sahibi 11 Eyl 2026'da bireysel
   denetimi atlayip toplu onayi beta surumune ertelemeye karar verdi;
   1211 satirin TAMAMI artik is_active=true, review_status='APPROVED',
   quality_review_status='auto_judged_high' -- yani kapidan GECIYORLAR.
   `is_ai_generated` true KALIR.

   Geometrinin konsensus gerekcesi fizik kitaplarininkinden FARKLIDIR:
   0014 (AYT) cozum dogrulamasina dayanmisti, 0016 (TYT) iki sinyale;
   geometride dort sinyal var (cift okuma, anahtar seridinin cift okumasi,
   basili anahtar capraz kontrolu, banner<->anahtar zinciri ortusmesi).
   Bir bekci bu listenin fizigin gerekcesine KAYDIRILMADIGINI dogrular --
   kopyala-yapistir ile yanlis bir kalite beyani olusmasin diye.

Gercek Postgres yoksa ya da veri henuz ithal edilmemisse SKIP olur;
sahte motorla (sqlite) YANLIS pozitif donmez (bkz tests/e2e/pg_dsn.py).
"""

from __future__ import annotations

import json

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
# 0018'in yazdigi gerekce -- fizik kitaplarininkinden FARKLI olmali
_SINYALLER = [
    "cift_bagimsiz_okuma",
    "anahtar_seridi_cift_okuma",
    "basili_anahtar_capraz_kontrolu",
    "banner_anahtar_zinciri_ortusmesi",
]
_SINYALLER_JSON = json.dumps(_SINYALLER)


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
async def test_mikro_geo_onay_sonrasi_sozlesme(db_session: AsyncSession):
    """0018 sonrasi: aktif ve APPROVED, ama KOKEN gizlenmemis.

    Kapiyi acmanin kolay ama yanlis yolu `is_ai_generated=false` yazmakti
    (view'in oteki kolu). O yol DB'ye yanlis bir kaynak beyani birakirdi.
    is_public de acilmaz -- beta kapisi ile herkese aciklik ayri seylerdir.
    """
    n = await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE b.is_active IS NOT TRUE), "
            "       count(*) FILTER (WHERE b.is_public IS TRUE), "
            "       count(*) FILTER (WHERE b.is_ai_generated IS NOT TRUE), "
            "       count(*) FILTER (WHERE b.review_status <> 'APPROVED') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    pasif, acik, ai_isaretsiz, onaysiz = sonuc.one()
    assert pasif == 0, f"{n} satirdan {pasif} tanesi hala is_active=false"
    assert acik == 0, f"{acik} geometri satiri is_public=true"
    assert ai_isaretsiz == 0, (
        f"{ai_isaretsiz} satirda is_ai_generated=true degil -- "
        "OCR kaynakli icerik AI uretimi olarak isaretli KALMALI"
    )
    assert onaysiz == 0, f"{onaysiz} satirin review_status'u APPROVED degil"


@pytest.mark.asyncio
async def test_mikro_geo_temiz_sorular_kapidan_geciyor(db_session: AsyncSession):
    """0018 sonrasi sozlesme: sik_bos TASIMAYAN her satir kapidan gecmeli.

    Bu kitapta sik_bos bayrakli soru YOK (sikler her zaman metin), yani
    hedef 1211 satirin TAMAMI.
    """
    n = await _gerekli(db_session)
    gecmeyen = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_bank b "
                "  JOIN question_metadata m ON m.id = b.id "
                " WHERE m.source_book = :k "
                "   AND NOT ((m.pipeline_metadata::jsonb ? 'bayraklar') "
                "            AND (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos') "
                "   AND NOT EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id)"
            ),
            {"k": _KAYNAK},
        )
    ).scalar()
    assert gecmeyen == 0, (
        f"{n} geometri sorusundan {gecmeyen} tanesi kapidan GECMIYOR "
        "-- 0018 kosmadi mi, yoksa kapi mi degisti?"
    )


@pytest.mark.asyncio
async def test_mikro_geo_sik_bos_kilidi_yerinde(db_session: AsyncSession):
    """D10 kurali: sikki gorsel olan satir TAM onay izi tasisa bile gecemez.

    Bu kitapta sik_bos bayrakli soru YOK; bekci yine de kuralin view'de
    zorunlu tutuldugunu dogrular, cunku ileride boyle bir satir eklenebilir.
    """
    await _gerekli(db_session)
    gecen = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM question_bank b "
                "  JOIN question_metadata m ON m.id = b.id "
                " WHERE (m.pipeline_metadata::jsonb ? 'bayraklar') "
                "   AND (m.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos' "
                "   AND EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id)"
            )
        )
    ).scalar()
    assert gecen == 0, (
        f"{gecen} sik_bos bayrakli satir kapidan geciyor -- "
        "metin tabanli sunumda sikki eksik gorunur"
    )


@pytest.mark.asyncio
async def test_mikro_geo_toplu_onay_izi_kayitli(db_session: AsyncSession):
    """Toplu onay, bireysel denetimden AYIRT EDILEBILIR kalmali.

    IS DISTINCT FROM kullanilir: anahtar HIC YOKSA `->>` NULL doner ve duz
    `<>` karsilastirmasi NULL uretir; FILTER onu saymaz, yani iz hic yokken
    bekci YESIL kalirdi. 0016'da tam olarak bu goruldu ve boyle duzeltildi.
    """
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> 'onay_turu') "
            "                        IS DISTINCT FROM 'toplu_beta_sahibi'), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "                        'bireysel_denetim_yapildi') IS DISTINCT FROM 'false'), "
            "       count(*) FILTER (WHERE s.quality_review_status = 'human_verified'), "
            "       count(*) FILTER (WHERE s.quality_review_status "
            "                        IS DISTINCT FROM 'auto_judged_high') "
            "  FROM question_bank b JOIN question_metadata m ON m.id = b.id "
            "  JOIN question_statistics s ON s.id = b.id "
            " WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK},
    )
    izsiz, denetim_izsiz, insan_dogrulandi, kalite_yanlis = sonuc.one()
    assert izsiz == 0, f"{izsiz} satirda onay_turu='toplu_beta_sahibi' izi yok"
    assert (
        denetim_izsiz == 0
    ), f"{denetim_izsiz} satirda bireysel_denetim_yapildi=false izi yok"
    assert insan_dogrulandi == 0, (
        f"{insan_dogrulandi} satir 'human_verified' isaretli -- hicbir insan "
        "bu sorulari tek tek dogrulamadi, dogru deger 'auto_judged_high'"
    )
    assert (
        kalite_yanlis == 0
    ), f"{kalite_yanlis} satirin quality_review_status'u auto_judged_high degil"


@pytest.mark.asyncio
async def test_mikro_geo_konsensus_gerekcesi_fizige_kaymamis(
    db_session: AsyncSession,
):
    """Geometrinin konsensus gerekcesi fizik kitaplarininkine KAYDIRILMAMIS olmali.

    0014 (AYT fizik) gerekcesi bagimsiz COZUM DOGRULAMASINI iceriyordu;
    geometride sorular tekrar cozulmedi. 0016 (TYT fizik) iki sinyal
    kullanmisti; geometride dort sinyal var (anahtar seridinin cift okumasi
    ve banner<->anahtar zinciri ortusmesi TYT'de YOKTU).

    Kopyala-yapistir ile yanlis bir kalite beyani olusmasin diye bu bekci
    listenin BIREBIR geometrinin dort sinyali oldugunu dogrular ve cozum
    dogrulamasi izinin 'yapilmadi' kalmasini korur.
    """
    await _gerekli(db_session)
    sonuc = await db_session.execute(
        text(
            "SELECT count(*) FILTER (WHERE (m.pipeline_metadata::jsonb -> "
            "         'konsensus_sinyalleri') IS DISTINCT FROM CAST(:beklenen AS jsonb)), "
            "       count(*) FILTER (WHERE (m.pipeline_metadata::jsonb ->> "
            "         'cozum_dogrulamasi') IS DISTINCT FROM 'yapilmadi_urun_karari') "
            "  FROM question_metadata m WHERE m.source_book = :k"
        ),
        {"k": _KAYNAK, "beklenen": _SINYALLER_JSON},
    )
    farkli, cozum_izi_yok = sonuc.one()
    assert farkli == 0, (
        f"{farkli} satirin konsensus_sinyalleri listesi geometrinin dort "
        "sinyalinden farkli -- baska bir kitabin gerekcesi kopyalanmis olabilir"
    )
    assert cozum_izi_yok == 0, (
        f"{cozum_izi_yok} satirda cozum_dogrulamasi='yapilmadi_urun_karari' izi "
        "yok -- uretilmemis bir cozum varmis gibi gorunebilir"
    )


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
