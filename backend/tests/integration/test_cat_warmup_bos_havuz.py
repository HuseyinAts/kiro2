"""Y4 / Adim 1 — CAT warm-up havuzu BOS oldugunda sessiz kalmamali.

OLCULEN DURUM (19 Agu 2026, canli DB, uretim fonksiyonu dogrudan cagrilarak)

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

DERSLER = ("MATEMATIK", "TURKCE", "FIZIK")


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


@pytest.mark.parametrize("ders", DERSLER)
async def test_warmup_havuzu_bugun_bos_olcum(live_db, ders):
    """Olculen durumu kayda geciren karakterizasyon testi.

    Bu test warm-up havuzunun bos olmasini ONAYLAMIYOR; kusuru KAYDA
    geciriyor. Y4 Adim 3 prior'lari yazdiginda bu test DUSECEK ve o an
    guncellenmesi gerekecek -- kasitli: sessiz duzelme de istemiyoruz.
    """
    aday = await _servis(live_db)._get_candidate_questions(
        ders, theta=0.0, warm_up=True
    )
    assert aday == [], (
        f"{ders} warm-up havuzu artik BOS DEGIL ({len(aday)} aday). Eger "
        "bootstrap prior'lari yazildiysa (Y4 Adim 3) bu BEKLENEN bir "
        "iyilesmedir: bu testi ve start_session'daki uyariyi guncelle."
    )


async def test_start_session_fallback_uyarisi_birakiyor(live_db, caplog):
    """`start_session` gercekten cagrilir ve uyari uretilir.

    redis gerekiyor -> minimal sahte redis. DB GERCEK kalir (kusur sinifi
    sema+veri kaynakli, mock DB onu goremez).
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

    with caplog.at_level(logging.WARNING):
        try:
            await svc.start_session(
                user_id="y4-olcum-kullanicisi",
                subject_id="MATEMATIK",
                is_guest=True,
            )
        except TypeError as exc:  # imza bu turda degismis olabilir
            pytest.skip(f"start_session imzasi uyusmadi: {exc}")

    metinler = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    warmup_uyarisi = [m for m in metinler if "warm-up" in m.lower()]
    assert warmup_uyarisi, (
        "Warm-up havuzu BOS oldugu halde HIC uyari uretilmedi -> sessiz "
        f"fallback. Gorulen WARNING kayitlari: {metinler}"
    )
    assert "MATEMATIK" in warmup_uyarisi[0], (
        "Uyari hangi DERS icin bos oldugunu soylemiyor -> operasyonel olarak "
        f"kullanilamaz: {warmup_uyarisi[0]}"
    )
