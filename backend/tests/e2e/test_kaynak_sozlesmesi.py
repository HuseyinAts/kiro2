"""source_book adlandirma sozlesmesinin bekcileri.

NE KORUYOR
----------
`question_metadata.source_book` bu depoda bir etiket degil KIMLIKTIR: toplu
onay/aktiflestirme migration'lari (0011, 0012, 0014, 0016, 0018) hedeflerini
bu kolona gore secer, ithal scriptlerinin "bu satir baska kitaba ait,
dokunma" korumasi da buna bakar. Kolon serbest metin oldugu icin iki ayri
sekilde bozulabilir ve iki bekci bunlari ayri ayri tutar:

1. ADIN IKI FARKLI YAZIMI (test_iki_yazim_ayni_kitaba_cozulmuyor)
   11 Eyl 2026 olcumu: 192 farkli deger icinde TEK bir cakisma vardi --
   "Aromat Tyt ... Model Sorular" iki yazimla bolunmustu (8 + 1 satir).
   Bolunmus ad, source_book ile filtreleyen her korumada sessiz bir delik
   acar. 0019 birlestirdi; bu bekci yenisinin olusmasini engeller.

2. KORUMANIN KOPYALANMAMASI (test_ithal_scriptleri_ortak_korumayi_kullaniyor)
   `soru_hash` metin + 5 sik uzerinden hesaplandigi ve
   `id = uuid5(NAMESPACE_OID, soru_hash)` oldugu icin AYNI SORU baska bir
   kitapta da varsa ID AYNIDIR. PR #254'te bu ayrim mikro_geo_ithal.py'ye
   eklendi ama neofizik_ithal.py ve neofizik_tyt_ithal.py'ye TASINMADI --
   ikisi de "SELECT id FROM question_bank WHERE id = ANY(...)" ile yetinip
   --meta-guncelle'de baska bir kitabin satirini ezebiliyordu. (Ayni acik
   11 Eyl 2026'da 2 resmi OSYM satirinin metadata'sini ezdi ve ikisi de
   servis kapisindan dustu.) Bu bekci, korumanin uc scriptte de ORTAK
   FONKSIYONLA kuruldugunu ve eski desenin geri gelmedigini dogrular.

Kod bekcileri DB'siz kosar. DB bekcileri gercek Postgres yoksa SKIP olur;
sahte motorla (sqlite) YANLIS pozitif donmez (bkz tests/e2e/pg_dsn.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from scripts.kitap.kaynak_sozlesmesi import (
    KAYNAK_KAYITLARI,
    KaynakAdiError,
    cakisan_kaynak,
    kaynak_adi_dogrula,
    normalize_anahtar,
)
from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

# BILEREK golden_flow ISARETSIZ -- ithal scriptleri elle calistirilir,
# hicbir migration ya da seed akisinda degil.

_BACKEND = Path(__file__).resolve().parents[2]
_ITHAL_SCRIPTLERI = (
    "scripts/kitap/mikro_geo_ithal.py",
    "scripts/kitap/neofizik_ithal.py",
    "scripts/kitap/neofizik_tyt_ithal.py",
)
# PR #254 oncesi desen: var olan satirlari kaynak kitaba gore AYIRMADAN toplar.
_ESKI_DESEN = "SELECT id FROM question_bank WHERE id = ANY"


# --------------------------------------------------------------------------
# Kod bekcileri (DB gerekmez)
# --------------------------------------------------------------------------


def test_kayitli_adlar_sozlesmeye_uyuyor():
    """KAYNAK_KAYITLARI'ndaki her ad kendi kuralini gecmeli."""
    assert KAYNAK_KAYITLARI, "kayit sozlugu bos olamaz"
    for ad in KAYNAK_KAYITLARI:
        kaynak_adi_dogrula(ad, kayitli_olmali=True)


def test_kayitli_adlar_birbirine_cozulmuyor():
    """Iki kayitli ad ayni normalize anahtara dusmemeli."""
    adlar = list(KAYNAK_KAYITLARI)
    anahtarlar = [normalize_anahtar(a) for a in adlar]
    assert len(set(anahtarlar)) == len(adlar), (
        "kayitli adlarda cakisma var: "
        f"{[a for a in adlar if anahtarlar.count(normalize_anahtar(a)) > 1]}"
    )


@pytest.mark.parametrize(
    "bozuk",
    [
        "",
        " Bas boslugu",
        "Son boslugu ",
        "Cift  bosluk",
        "Turkce karakterli Bankasi" + chr(0x0131),
    ],
)
def test_bozuk_adlar_reddediliyor(bozuk: str):
    """Dogrulayici gercekten olcuyor mu -- her bozuk sekil ayri ayri red."""
    with pytest.raises(KaynakAdiError):
        kaynak_adi_dogrula(bozuk)


def test_cakisma_bulucu_turkce_katliyor():
    """Aromat ciftinin iki yazimi ayni kitap olarak goruluyor mu."""
    govde = "Aromat Tyt T" + chr(0x00FC) + "rk{0}e Model Sorular"
    duz, cedilla = govde.format("c"), govde.format(chr(0x00E7))
    assert duz != cedilla
    assert cakisan_kaynak(cedilla, [duz]) == duz
    assert cakisan_kaynak(duz, [duz]) is None


def test_ithal_scriptleri_ortak_korumayi_kullaniyor():
    """Uc ithal script'i de yabanci-satir ayrimini ortak fonksiyondan almali."""
    eksik, eski = [], []
    for yol in _ITHAL_SCRIPTLERI:
        kaynak = (_BACKEND / yol).read_text(encoding="utf-8")
        if "kaynak_sozlesmesi import" not in kaynak or "ayristir(" not in kaynak:
            eksik.append(yol)
        if _ESKI_DESEN in kaynak:
            eski.append(yol)
    assert not eksik, f"ortak korumayi kullanmayan ithal script'i: {eksik}"
    assert not eski, f"PR #254 oncesi ayrimsiz desen geri gelmis: {eski}"


def test_ithal_scriptleri_adi_kayittan_okuyor():
    """KAYNAK_ADI ile ONEK ayni yerden gelmeli -- ikinci elle yazim olmasin."""
    for yol in _ITHAL_SCRIPTLERI:
        kaynak = (_BACKEND / yol).read_text(encoding="utf-8")
        assert (
            'ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]' in kaynak
        ), f"{yol}: ONEK hala elle yazilmis"


# --------------------------------------------------------------------------
# DB bekcileri
# --------------------------------------------------------------------------


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


async def _adlar(session: AsyncSession) -> list[str]:
    sonuc = await session.execute(
        text(
            "SELECT DISTINCT source_book FROM question_metadata "
            " WHERE source_book IS NOT NULL AND source_book <> ''"
        )
    )
    adlar = [r[0] for r in sonuc.fetchall()]
    if not adlar:
        pytest.skip("question_metadata bos -- olculecek kaynak yok")
    return adlar


@pytest.mark.asyncio
async def test_iki_yazim_ayni_kitaba_cozulmuyor(db_session: AsyncSession):
    """Hicbir iki source_book degeri ayni normalize anahtara dusmemeli."""
    adlar = await _adlar(db_session)
    kume: dict[str, list[str]] = {}
    for ad in adlar:
        kume.setdefault(normalize_anahtar(ad), []).append(ad)
    cakisan = {a: v for a, v in kume.items() if len(v) > 1}
    assert not cakisan, (
        "ayni kitap birden fazla yazimla duruyor (source_book ile filtreleyen "
        f"her koruma bu satirlari kacirir): {cakisan}"
    )


@pytest.mark.asyncio
async def test_modern_ithaller_kayitli_ve_ascii(db_session: AsyncSession):
    """`ithal_araci` yazan her satirin kaynak adi sozlesmeye uymali.

    Eski hattan kalan 187 deger BILEREK kapsam disi: onlar duzeltilecek borc,
    bu bekcinin konusu yeni yazilan satirlar.
    """
    sonuc = await db_session.execute(
        text(
            "SELECT DISTINCT source_book FROM question_metadata "
            " WHERE (pipeline_metadata::jsonb) ? 'ithal_araci' "
            "   AND source_book IS NOT NULL"
        )
    )
    modern = [r[0] for r in sonuc.fetchall()]
    if not modern:
        pytest.skip("modern ithal satiri yok")
    for ad in modern:
        kaynak_adi_dogrula(ad, kayitli_olmali=True)


@pytest.mark.asyncio
async def test_kayit_sozlugu_db_ile_ortusuyor(db_session: AsyncSession):
    """KAYNAK_KAYITLARI DB'den sapmasin -- sapma sessiz bir yazim hatasidir."""
    sonuc = await db_session.execute(
        text(
            "SELECT DISTINCT source_book FROM question_metadata "
            " WHERE (pipeline_metadata::jsonb) ? 'ithal_araci' "
            "   AND source_book IS NOT NULL"
        )
    )
    modern = {r[0] for r in sonuc.fetchall()}
    if not modern:
        pytest.skip("modern ithal satiri yok")
    assert modern <= set(
        KAYNAK_KAYITLARI
    ), f"DB'de kayitli olmayan modern kaynak: {sorted(modern - set(KAYNAK_KAYITLARI))}"
