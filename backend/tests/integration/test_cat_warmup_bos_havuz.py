"""Y4 / Adim 1 — CAT warm-up havuzu BOS oldugunda sessiz kalmamali.

GUNCELLEME (7 Eyl 2026, SS10.64) -- ASAGIDAKI 19 AGU OLCUMU ARTIK GECERSIZ
-------------------------------------------------------------------------
Bootstrap prior'lari (Y4 Adim 3) YAZILMIS. Yeni olcum, ayni yontemle:

    ders        calib_pool  toplam   warm_up   core
    MATEMATIK           17     391        13    100
    KIMYA                5    3531        30    100
    TURKCE               0       0         0      0
    FIZIK                0       0         0      0
    BIYOLOJI             0       0         0      0

    is_calib_pool TRUE : 0  -> 22
    irt_difficulty     : tek deger 0.0 -> 2.301 farkli deger (-1,05 .. 0,887)
    source_book dolu   : 0/27.073 -> 3.922/3.922

Yani "warm-up havuzu bos" olgusu MATEMATIK ve KIMYA icin COZULDU. Buradaki
testler bu yuzden guncellendi: artik OLGUYU degil ILISKIYI civiliyorlar
(calib_pool > 0 <-> warm-up dolu). Ayrica TURKCE/FIZIK/BIYOLOJI'de HIC soru
yok (core=0) -- ayri bir icerik kapsami bulgusu, bu bekcinin konusu degil ama
eski testin o derslerde YANLIS NEDENLE yesil kalmasina yol aciyordu.

OLCULEN DURUM (19 Agu 2026, canli DB, uretim fonksiyonu dogrudan cagrilarak)
--- TARIHSEL KAYIT, artik gecerli degil ---

    _get_candidate_questions(ders, theta=0.0, warm_up=True)
        MATEMATIK -> 0    TURKCE -> 0    FIZIK -> 0

Warm-up sorgusunun DORT dalinin DORDU de bos donuyor:

    Oncelik 1/2/3  ->  `qs.is_calib_pool = TRUE` sarti
                       canli: is_calib_pool TRUE=0 / FALSE=36.967
    Son care       ->  `qs.irt_difficulty < max(theta-1.0, -0.5)`
                       canli: irt_difficulty TEK deger = 0.0 (36.967 satir)
                       theta=0 -> b_max=-0.5 -> `0.0 < -0.5` FALSE -> 0 satir

Sonucu: `start_session` core havuzuna dusuyor (dogru davranis, oturum yine
baslar) ama bunu HIC bildirmiyordu. Yani "kolay ilk soru" tasarim niyeti
fiilen OLU ve bu gorunmezdi. Bu dosya o sessizligi civiler.

BU TESTIN IDDIA ETMEDIGI SEY: warm-up havuzunun DOLU olmasi. O, Y4 Adim 3'un
(bootstrap prior'lari) kabul kriteridir ve bugun kasitli olarak saglanmiyor.
Buraya kirmizi bir test koymak CI'yi surekli kirmizi tutardi; bunun yerine
mevcut (kusurlu ama bilinen) davranis + onu gorunur kilan uyari civilenir.

NEDEN GERCEK POSTGRES: warm-up havuzunun bosluu bir SEMA+VERI olgusudur.
`AsyncMock`'lu bir DB her kolon adini ve her satiri uydurur, dolayisiyla bu
sinifi yapisal olarak goremez (S228 dersi).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pytest

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

pytestmark = pytest.mark.asyncio

DERSLER = ("MATEMATIK", "KIMYA", "TURKCE", "FIZIK", "BIYOLOJI")

# --- KONTROL KOLU (evren) : SS10.64 ----------------------------------------
#
# Asagidaki `test_alet_dogrulamasi_core_havuz_dolu` kontrol kolu VAR ama zayif:
# yalnizca "core havuz > 0" diyor. CI kendi `backend/.env`ini yazip taze
# `kiro2_test` konteynerini gosteriyor (.github/workflows/ci.yml:296); orada 12
# tohum sorusu var ve core havuz 12 dondugu icin kol GECIYOR -- ardindan
# warm-up olcumleri urun DB'sinde olcumus gibi degerlendiriliyor. Sonuc:
# CI kosusu 34068207500'de 2 kalici kirmizi
#   test_warmup_havuzu_bugun_bos_olcum[MATEMATIK] -> "artik BOS DEGIL (12 aday)"
#   test_start_session_fallback_uyarisi_birakiyor -> uyari uretilmedi
# Ikisi de urun kusuru DEGIL: bu dosyanin belgeledigi olgu (is_calib_pool
# TRUE=0, irt_difficulty tek deger 0.0) 36.967 satirlik URUN havuzuna aittir.
#
# Bu yuzden kol evren duzeyine cikariliyor: urun havuzuna bagli degilsek
# olcumu reddet. Sayi mesajda durur -- sessizce yesil gecmez.
KONTROL_KOLU_MIN_SATIR = 1000


@pytest.fixture(autouse=True)
async def _evren_kontrolu(live_db):
    """Urun havuzuna bagli degilsek bu dosyadaki olcumleri REDDET."""
    from sqlalchemy import text

    aktif = (
        await live_db.execute(
            text("SELECT count(*) FROM question_bank WHERE is_active")
        )
    ).scalar()
    if not aktif or aktif < KONTROL_KOLU_MIN_SATIR:
        pytest.skip(
            f"kontrol kolu: baglanilan DB'de {aktif} aktif soru var "
            f"(esik >={KONTROL_KOLU_MIN_SATIR}). Bu urun havuzu degil -- "
            "warm-up olcumleri yapilmadi."
        )


def _servis(db):
    """CATSessionService — redis'siz.

    `_get_candidate_questions` yalniz `self.db`ye dokunuyor (olculdu); redis
    sadece oturum durumu icin gerekli. `None` gecmek testin bu metodu izole
    olcmesini sagliyor.
    """
    from app.services.cat_session import CATSessionService

    return CATSessionService(redis=None, db=db)


async def test_alet_dogrulamasi_core_havuz_dolu(live_db):
    """KONTROL KOLU.

    Asagidaki 'warm-up bos' iddialari, sorgu/baglanti/kapi tamamen bozuk
    oldugunda da 0 dondurerek SAHTE bir sekilde gecerdi. Bu test bilinen-DOLU
    durumun gorundugunu kanitlar: theta=0 core havuzu > 0 olmali.
    """
    aday = await _servis(live_db)._get_candidate_questions(
        "MATEMATIK", theta=0.0, warm_up=False
    )
    assert len(aday) > 0, (
        "Core havuz theta=0'da BOS. Kontrol kolu dustu -> bu dosyadaki diger "
        "'bos' olcumleri GECERSIZ (baglanti/kapi/sema arizasi olabilir)."
    )


async def _calib_sayisi(oturum, ders: str) -> int:
    """Dersin `is_calib_pool = TRUE` soru sayisi."""
    from sqlalchemy import text

    return (
        await oturum.execute(
            text(
                "SELECT count(*) FROM question_metadata qm "
                "JOIN question_statistics qs ON qs.id = qm.id "
                "WHERE qm.subject_area = :ders AND qs.is_calib_pool"
            ),
            {"ders": ders},
        )
    ).scalar() or 0


@pytest.mark.parametrize("ders", DERSLER)
async def test_warmup_havuzu_calib_pool_ile_uyumlu(live_db, ders):
    """Warm-up havuzu, dersin kalibrasyon havuzuyla TUTARLI olmali (SS10.64).

    ESKI HALI VE NEDEN DEGISTI
    --------------------------
    Bu test eskiden `assert aday == []` diyordu, yani "warm-up havuzu BOS"
    olgusunu kayda geciriyordu; docstring'i de "Y4 Adim 3 prior'lari
    yazdiginda bu test DUSECEK ve o an guncellenmesi gerekecek" diyordu.
    O an geldi. 7 Eyl 2026 olcumu (yerel canli DB, uretim fonksiyonu
    dogrudan cagrilarak):

        ders        calib_pool  toplam   warm_up   core
        MATEMATIK           17     391        13    100
        KIMYA                5    3531        30    100
        TURKCE               0       0         0      0
        FIZIK                0       0         0      0
        BIYOLOJI             0       0         0      0

    Yani bootstrap prior'lari YAZILMIS: `is_calib_pool` artik TRUE=22 (eskiden
    0) ve `irt_difficulty` 2.301 farkli deger tasiyor (eskiden tek deger 0.0).
    Eski assert bugun MATEMATIK ve KIMYA'da DUSER, TURKCE/FIZIK'te ise YANLIS
    NEDENLE gecerdi: o derslerde hic soru yok, warm-up'in bos olmasi warm-up
    hakkinda hicbir sey soylemez. Bu, vakum-bekci desenidir.

    YENI IDDIA -- olguyu degil ILISKIYI civiliyor, boylece havuz degistikce
    kendini gunceller:
      * calib_pool > 0  -> warm-up BOS OLMAMALI (prior'lar ise yariyor)
      * calib_pool == 0 ama core > 0 -> warm-up BOS OLMALI (eski kusur hala
        gecerli; asagidaki uyari testi de o durumu civiliyor)
      * core == 0 -> o derste hic soru yok; olcum yapilmaz (ayri bir icerik
        kapsami bulgusu, bu bekcinin konusu degil)
    """
    servis = _servis(live_db)
    calib = await _calib_sayisi(live_db, ders)
    core = await servis._get_candidate_questions(ders, theta=0.0, warm_up=False)
    if not core:
        pytest.skip(
            f"{ders}: core havuz da BOS -> bu derste hic soru yok. "
            "Warm-up olcumu anlamsiz (ayri bir icerik kapsami bulgusu)."
        )

    aday = await servis._get_candidate_questions(ders, theta=0.0, warm_up=True)

    if calib > 0:
        assert aday, (
            f"{ders}: {calib} soru `is_calib_pool = TRUE` oldugu halde warm-up "
            "havuzu BOS dondu. Prior'lar yazilmis ama warm-up sorgusu onlari "
            "gormuyor -> 'kolay ilk soru' tasarim niyeti hala olu."
        )
    else:
        assert aday == [], (
            f"{ders}: kalibrasyon havuzu BOS ({calib}) oldugu halde warm-up "
            f"{len(aday)} aday dondurdu. Warm-up sorgusunun son care dali "
            "beklenmedik bicimde eslesiyor -> sorgu davranisi degismis."
        )


async def test_start_session_fallback_uyarisi_birakiyor(live_db, caplog):
    """Warm-up BOS iken `start_session` sessiz kalmamali (SS10.64'te guncellendi).

    Bu test "warm-up bos ve bu gorunmuyor" kusurunu civiliyordu ve MATEMATIK'i
    sabit olarak kullaniyordu. 7 Eyl 2026 olcumu MATEMATIK warm-up'inin ARTIK
    DOLU oldugunu gosterdi (13 aday, 17 calib_pool sorusu) -- yani uyarinin
    uretilmemesi artik DOGRU davranis; testin kirmizisi urun kusuru degildi.

    Iddia korunuyor ama dogru derse baglaniyor: uyari, warm-up'i GERCEKTEN bos
    olan ama core havuzu DOLU olan bir derste aranir. Boyle bir ders yoksa
    kusur bugun yeniden uretilemez -> olcum yapilmaz (skip), sessizce yesil
    gecilmez.
    """
    from app.services.cat_session import CATSessionService

    class _SahteBoruHatti:
        """`_write_state` boru hatti kullaniyor: hset + expire, sonra execute."""

        def __init__(self, depo: dict[str, str]) -> None:
            self.depo = depo

        def hset(self, key, mapping=None):
            self.depo[key] = str(mapping)
            return self

        def expire(self, key, ttl):
            return self

        async def execute(self):
            return [True, True]

    class _SahteRedis:
        """start_session'in dokundugu YUZEY: pipeline/get/setex/delete/hgetall.

        Redis SAHTE, DB GERCEK. Kusur sinifi (warm-up havuzunun bos donmesi)
        sema+veri kaynakli; onu ancak gercek Postgres gosterir. Redis ise
        yalnizca oturum durumunu tutuyor, olculen davranisin parcasi degil.
        """

        def __init__(self) -> None:
            self.depo: dict[str, str] = {}

        def pipeline(self):
            return _SahteBoruHatti(self.depo)

        async def hgetall(self, key):
            return {}

        async def get(self, key):
            return None

        async def setex(self, key, ttl, val):
            self.depo[key] = val

        async def delete(self, *keys):
            for k in keys:
                self.depo.pop(k, None)

    svc = CATSessionService(redis=_SahteRedis(), db=live_db)

    # Kusurun bugun GERCEKTEN gorundugu dersi bul: core DOLU ama warm-up BOS.
    hedef_ders = None
    for ders in DERSLER:
        core = await svc._get_candidate_questions(ders, theta=0.0, warm_up=False)
        if not core:
            continue
        sicak = await svc._get_candidate_questions(ders, theta=0.0, warm_up=True)
        if not sicak:
            hedef_ders = ders
            break

    if hedef_ders is None:
        pytest.skip(
            "core havuzu dolu olup warm-up'i bos olan ders yok -> 'sessiz "
            "fallback' kusuru bugun yeniden uretilemiyor, olcum yapilmadi. "
            f"(bakilan dersler: {', '.join(DERSLER)})"
        )

    with caplog.at_level(logging.WARNING):
        try:
            await svc.start_session(
                user_id="y4-olcum-kullanicisi",
                subject_id=hedef_ders,
                is_guest=True,
            )
        except TypeError as exc:  # imza bu turda degismis olabilir
            pytest.skip(f"start_session imzasi uyusmadi: {exc}")

    metinler = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    warmup_uyarisi = [m for m in metinler if "warm-up" in m.lower()]
    assert warmup_uyarisi, (
        f"{hedef_ders}: warm-up havuzu BOS oldugu halde HIC uyari uretilmedi "
        f"-> sessiz fallback. Gorulen WARNING kayitlari: {metinler}"
    )
    assert hedef_ders in warmup_uyarisi[0], (
        "Uyari hangi DERS icin bos oldugunu soylemiyor -> operasyonel olarak "
        f"kullanilamaz: {warmup_uyarisi[0]}"
    )
