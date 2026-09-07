"""`soru_getir` / `sorular_listele` OKUMA yolunu canli PG'ye karsi civiler.

OLCULEN KUSUR (17 Agu 2026, canli PG 18.1:5434, 36.967 aktif soru)
-------------------------------------------------------------------
Iki metot da `cache_manager.get_or_compute(...)` cagiriyor ama `CacheManager`
sinifinda O METOT YOK — `get_or_set` var. Gercek traceback:

    AttributeError: 'CacheManager' object has no attribute 'get_or_compute'
      services/soru_bankasi_service.py:625  soru_getir
      services/soru_bankasi_service.py:754  sorular_listele

Ikisi de ciplak `except Exception` ile sariliyor, yani hata KULLANICIYA
ULASMIYOR; bunun yerine:

    soru_getir(gercek_id)  -> None  -> uc HTTP 404 "Soru bulunamadi"
    sorular_listele()      -> []    -> uc HTTP 200 + BOS liste (36.967 soru varken)

`get_or_set(key, factory_func, ttl)` imzasi `get_or_compute(key, fetch, ttl)` ile
konumsal olarak uyumlu (olculdu, `inspect.signature`), yani duzeltme ad degisimi.

NEDEN HIC YAKALANMADI (asil kusur bu)
--------------------------------------
Uretim kodu `unittest.mock.AsyncMock` IMPORT EDIP ona gore dallaniyordu:

    if isinstance(cache_manager.get, AsyncMock):   # :575 ve :657
        ... ayni sorgunun IKINCI, KOPYA hali ...

`tests/unit/test_soru_bankasi_service.py:124` tum `cache_manager`i mock'ladigi
icin 50 testin hepsi MOCK dalini kosuyordu; uretim dali hic kosmuyordu. Yani
kusur "test edilmemis" degil, **test edilemez** hale getirilmisti — ve iki dal
ayni sorguyu tasidigi icin sorgu degisiklikleri de iki kez yapilmak zorundaydi.

Bu dosyadaki testler GERCEK `cache_manager` ile kosar (mock yok), bu yuzden
dal silinse de silinmese de URETIM yolunu olcerler.

CIVILENEMEYEN INVARYANT (olculdu, kapatilmadi)
-----------------------------------------------
`soru_getir`in `Question.is_active == True` filtresi bu dosyadaki hicbir testle
CIVILENMIYOR: mutasyonla olculdu (filtre silindi -> 3 passed, mutasyon HAYATTA).
Sebep yapisal — canli DB'de `is_active` dagilimi **36.967 / 36.967 TRUE**, yani
filtreyi ayirt edecek pasif satir YOK. Civilemek icin testin gecici bir pasif
soru YAZMASI gerekirdi; bu dosya bilincli olarak salt-okunur tutuldu.

Filtre bu turda DEGISTIRILMEDI (onceden var olan kod), yani bu bir regresyon
riski degil bir KAPSAM bosluğu. `.claude/rules/testing.md` #24/#31 bu invaryanti
repo genelinde zorunlu kiliyor — kapatilmasi ayri bir isin konusu.

KAPSAM DISI (bilincli): `get_or_set`te cache-stampede kilidi ve penetrasyon
(None'i cache'leme) korumasi YOK; `MultiLayerCache.get_or_compute`ta VAR
(olculdu). Servisin 12 `cache_manager.*` cagrisindan yalniz 2'sini baska bir
cache nesnesine cevirmek SPLIT-BRAIN yaratirdi (yazma bir store'a, okuma
digerine -> invalidation kirilir); 12'sini birden cevirmek bu turun kapsami
disi. Kusur (%100 kirik okuma yolu) bu korumalarin yoklugundan cok daha agir.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import services.soru_bankasi_service as sbs
from services.soru_bankasi_service import SoruBankasiServisi


class _RealDbManager:
    def __init__(self, maker):
        self._maker = maker

    @asynccontextmanager
    async def get_session(self):
        async with self._maker() as session:
            yield session


def _canli_dsn() -> str | None:
    """DSN'i `.env`ten DOGRUDAN oku — `conftest.py` `DATABASE_URL`i SQLite yapiyor.

    Sir sizintisi: DSN parola icerir, hicbir assert/skip mesajina KONULMAZ.
    """
    if override := os.getenv("KIRO2_LIVE_DSN"):
        return override
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None
    for ham in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ham.strip().startswith("DATABASE_URL="):
            continue
        dsn = ham.strip().split("=", 1)[1].strip().strip('"').strip("'")
        for eski, yeni in (
            ("postgresql+psycopg2://", "postgresql+asyncpg://"),
            ("postgresql://", "postgresql+asyncpg://"),
        ):
            if dsn.startswith(eski):
                return dsn.replace(eski, yeni, 1)
        return dsn
    return None


@pytest.fixture
async def canli_okuma(monkeypatch):
    """Servisi GERCEK PG'ye baglar; `cache_manager` MOCK'LANMAZ.

    KONTROL KOLU: >1000 aktif satir gormeyen baglanti "canli" sayilmaz —
    aksi halde bos SQLite uzerinde olculur ve fix sonrasi bile kirmizi kalir
    (bulgu degil, alet arizasi).

    Ayrica ornek bir soru id'si dondurur; "gercek bir soru 404 donuyor"
    iddiasi ancak GERCEK bir id ile olculebilir.
    """
    dsn = _canli_dsn()
    if not dsn or "postgresql" not in dsn:
        pytest.skip("canli PostgreSQL DSN'i bulunamadi (.env / KIRO2_LIVE_DSN)")

    engine = create_async_engine(dsn, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            aktif = (
                await session.execute(
                    text("SELECT count(*) FROM question_bank WHERE is_active")
                )
            ).scalar()
            ornek_id = (
                await session.execute(
                    text(
                        "SELECT id FROM question_bank WHERE is_active "
                        "ORDER BY id LIMIT 1"
                    )
                )
            ).scalar()
    except (
        OSError,
        SQLAlchemyError,
    ) as exc:  # pragma: no cover  # ortam kosullu: canli PG erisilebilirken bu dal hic kosmaz
        await engine.dispose()
        pytest.skip(f"canli PostgreSQL'e baglanilamadi: {type(exc).__name__}")

    # KONTROL KOLU: yanlis evren -> SKIP, FAIL degil (SS10.64).
    #
    # Bu kolun amaci "olcumu reddetmek"tir; docstring'i de zaten oyle diyor
    # ("bulgu degil, alet arizasi"). Ama `assert` kullanildigi icin reddetme
    # KIRMIZI olarak raporlaniyordu. Komsu iki dal (DSN yok / baglanilamadi)
    # zaten `pytest.skip` kullaniyor; bu dal onlarla tutarsizdi.
    #
    # Olculdu: CI `backend/.env`i kendisi yaziyor (.github/workflows/ci.yml:296)
    # ve `kiro2_test` veritabanini gosteriyor -- taze bir konteyner, 12 tohum
    # sorusu. Yani CI'da bu kol HER ZAMAN dusuyordu: 3 test kalici olarak
    # kirmizi, hicbiri urun kusuru degil.
    #
    # Skip mesaji sayiyi ve esigi YAZIYOR: "sessizce yesil" olmuyor, kosum
    # ozetinde neden olculmedigi okunabiliyor.
    if not aktif or aktif <= 1000:
        await engine.dispose()
        pytest.skip(
            f"kontrol kolu: baglanilan DB'de {aktif} aktif soru var (esik >1000). "
            "Bu, urun havuzu degil -- olcum yapilmadi (alet arizasi olurdu)."
        )
    if not ornek_id:
        await engine.dispose()
        pytest.skip("kontrol kolu: ornek soru id'si alinamadi -- olcum yapilmadi")

    monkeypatch.setattr(sbs, "db_manager", _RealDbManager(maker))
    yield ornek_id
    await engine.dispose()


async def test_soru_getir_gercek_soruyu_donduruyor(canli_okuma):
    """Var olan, aktif bir soru `None` DONMEMELI (uc bunu 404'e ceviriyor).

    Bugun RED: `AttributeError: ... has no attribute 'get_or_compute'` ciplak
    `except` tarafindan yutuluyor ve `None` doniyor.
    """
    soru = await SoruBankasiServisi().soru_getir(canli_okuma)

    assert (
        soru is not None
    ), f"aktif soru {canli_okuma!r} icin None dondu -> uc HTTP 404 verir"
    assert soru.id == canli_okuma
    # Yanit kurulurken okunan split alanlar da erisilebilir olmali (joinedload).
    assert soru.content.question_text
    assert soru.metadata_info.subject_area


async def test_sorular_listele_bos_donmuyor(canli_okuma):
    """`sorular_listele` 36.967 aktif soru varken BOS liste DONMEMELI.

    Bugun RED: ayni `AttributeError`, ayni ciplak `except` -> `[]`.
    Uc bunu HTTP 200 + bos liste yapiyor, yani kullanici "soru yok" goruyor.
    """
    sonuc = await SoruBankasiServisi().sorular_listele(limit=5)

    assert len(sonuc) > 0, "36.967 aktif soru varken bos liste dondu"
    assert len(sonuc) <= 5, f"limit=5 asildi: {len(sonuc)}"


async def test_soru_getir_olmayan_id_icin_none_donuyor(canli_okuma):
    """Olmayan id GERCEKTEN `None` donmeli — yani `None` bir HATA SINYALI DEGIL.

    Bu test yukaridakilerin AYIRT EDICILIGINI saglar: `get_or_set`i
    "her zaman bir sey dondur" gibi naif bir seye cevirmek yukaridaki iki
    testi yesil yapar ama BURAYI dusurur.
    """
    sonuc = await SoruBankasiServisi().soru_getir("olmayan-id-00000000-0000-0000")

    assert sonuc is None, f"olmayan id icin {sonuc!r} dondu"
