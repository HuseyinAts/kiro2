"""services/soru_bankasi_service.py'nin #485 split sonrasi UC kusurunu civileyen testler.

Calisan agacta SINIF-duzeyi erisim sayaci 41 -> 0 (goc DOGRU yapilmis), ama goc
UC ayri kusur birakti ve ucu de SESSIZ: her biri ciplak `except Exception` ile
yutulup "veri yok" gibi gorunuyor.

1. **`select_from` EKSIK** (S214 kosullu kurali). SQLAlchemy sorgunun sol
   tarafini SELECT listesinden cikarir. SELECT listesi YALNIZ split-tablo
   kolonu/agregasi iceriyorsa sol taraf split tablo sanilir:

       select(QuestionMetadata.subject_area).join(QuestionMetadata, ...)
       -> InvalidRequestError: Don't know how to join to <Mapper QuestionMetadata>

   Olculdu (17 Agu) — hata KURULUM'da DEGIL **DERLEME**'de:
   `BUILD: OK` / `COMPILE: InvalidRequestError` / `FROMS: InvalidRequestError`.
   Yani `select(...)` nesnesi sorunsuz yaratilir, patlama `session.execute()`
   icinde (derleme aninda) olur. Bu ayrim testlerin ne iddia edebilecegini
   belirler: "statement yakalandi" bir sey KANITLAMAZ, derleme/`get_final_froms`
   iddiasi kanitlar

   Bagimsiz olculdu (17 Agu): `.select_from(QuestionBankItem)` eklenince
   `get_final_froms() == 1` ve sorgu kuruluyor. Iki yer: `konu_listesi_getir`
   (her iki dal) ve `istatistikler_getir`'in `irt_stmt`'i.

   KARDES sorgulara EKLENMEZ: `select(QuestionMetadata.exam_type,
   func.count(Question.id))` SELECT listesinde `question_bank` kolonu
   tasidigi icin ZATEN kuruluyor (olculdu). Oraya `select_from` eklemek
   S214'un "sus" vakasidir — hicbir mutasyonla civilenemez.

2. **String kolonda `.value`**. Split sonrasi bu kolonlar Enum DEGIL String
   (olculdu):

       QuestionMetadata.exam_type      -> String
       QuestionMetadata.subject_area   -> String
       QuestionStatistics.difficulty_level -> Enum(QuestionDifficultyLevel)

   Yani `subject.value` / `exam_type.value` bir `str` uzerinde cagriliyor ->
   `AttributeError`. AMA `difficulty.value` (:1432) DOGRU — o kolon gercekten
   Enum ve DB enum uyesi dondurur. Asagidaki testler bunu ACIKCA civiliyor
   (`zorluk_dagilimi` anahtarlari `str` olmali), boylece "tum `.value`'lari
   sil" seklindeki ASIRI-FIX de kirmizi verir. `QuestionDifficultyLevel` bir
   `str` karisimi DEGIL (olculdu: `isinstance(uye, str) is False`), bu yuzden
   `isinstance(k, str)` iki durumu gercekten ayirir.

3. **`soru_guncelle` EAGER-LOAD'SUZ**. `select(Question)` ile ENTITY seciliyor,
   sonra `hasattr(soru, alan)` split alanlarina dokunuyor. Uc split iliskisi de
   `lazy='select'` -> async oturumda `MissingGreenlet` -> ciplak `except` ->
   `return None` -> cagiran HTTP 404 "Soru bulunamadi" goruyor. Dosyadaki
   diger 9 sorgu ZATEN `joinedload` kullaniyor; ayni kalip izlenmeli.

Testler GERCEK `models.question_bank` modeline karsi kosar (S212 D maddesi:
`sys.modules`'e stub koyan test KIRIK kodda da yesil kalir). `tests/fast/`
altinda `conftest.py` yok.

KAPSAM DISI (bilincli olarak test EDILMEDI — Adim 2/3'un konusu):
  * `_enum_donusturucu` KUCUK-HARF uretiyor (`ExamType.TYT` -> `'tyt'`) ama DB
    `TYT` tutuyor (olculdu: 28204 TYT / 8763 AYT). Yani `konu_listesi_getir`in
    `sinav_tipi` DALI, `select_from` fix'inden SONRA bile bos donecek. Bu P2
    casing kusuru bu turun kapsaminda DEGIL, o yuzden asagidaki `sinav_tipi`
    testi yalnizca sorgunun DERLENDIGINI iddia eder, satir dondurdugunu DEGIL.
  * `toplu_soru_ekle` (:1664 `difficulty.value`) — o `.value` bir Python
    enum'i uzerinde ve dogru; ayrica fonksiyon Adim 2'nin konusu.
  * :231 `difficulty_level.value` — `QuestionDifficultyLevel` enum uyesi
    uzerinde (String kolon DEGIL), dogru; hedef fonksiyonlarin disinda.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import services.soru_bankasi_service as sbs
from models.question_bank import QuestionDifficultyLevel
from services.soru_bankasi_service import SoruBankasiServisi

# ---------------------------------------------------------------------------
# S212 / S214 yardimcilari
# ---------------------------------------------------------------------------


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _assert_single_from(stmt) -> None:
    """Kartezyen kontrolu — METIN degil YAPI uzerinden (S212 B maddesi).

    Metinsel "FROM'da virgul var mi" kontrolu alt-sorgunun SELECT listesindeki
    virgule takilir; `get_final_froms()` semantiktir.
    """
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen carpim: {len(froms)} ayri FROM"


def _eager_loaded(stmt) -> dict[str, str | None]:
    """Yuklenen iliski adi -> yukleme stratejisi. Metin degil YAPI okur.

    Olculdu (SQLAlchemy 2.0.45): `joinedload(X.rel)` bir `Load` uretir;
    `opt.path[1].key` iliski adini, `dict(opt.context[0].strategy)["lazy"]`
    stratejiyi verir.

    GUARD (S221'den devralindi): iliski-YOLU OLMAYAN secenekler yardimciyi
    opak bicimde carpitir — `raiseload("*")` -> `.context` yok;
    `load_only(Q.id)` -> path uzunlugu 1. Bunlar atlanir; zaten bir iliskiye
    eager-load ATAMADIKLARI icin iddia kaybi yok.
    """
    loaded: dict[str, str | None] = {}
    for opt in stmt._with_options:
        if len(getattr(opt, "path", ())) < 2 or not hasattr(opt, "context"):
            continue
        strategy = dict(opt.context[0].strategy or {}) if opt.context else {}
        loaded[opt.path[1].key] = strategy.get("lazy")
    return loaded


class _CaptureSession:
    """Kurulan her `stmt`'i yakalar; gercek DB'ye gitmez.

    Servisin sonucu TUKETME sekilleri kodda tek tek okundu:
      * `konu_listesi_getir`  -> `result.scalars().all()`
      * `istatistikler_getir` -> `.scalar()`, `.all()` x3, `.first()`
      * `soru_guncelle`       -> `result.scalar_one_or_none()`
    """

    def __init__(self, results=None):
        self.statements: list = []
        self._results = list(results or [])
        self.committed = False
        self.rolled_back = False

    async def execute(self, stmt, params=None):
        idx = len(self.statements)
        self.statements.append(stmt)
        spec = self._results[idx] if idx < len(self._results) else {}
        result = MagicMock()
        result.all.return_value = spec.get("all", [])
        result.scalars.return_value.all.return_value = spec.get("scalars", [])
        result.scalar.return_value = spec.get("scalar", 0)
        result.first.return_value = spec.get("first")
        result.scalar_one_or_none.return_value = spec.get("one")
        return result

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, obj):
        return obj


class _FakeDbManager:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def get_session(self):
        yield self._session


@pytest.fixture
def wired(monkeypatch):
    """Servisi sahte oturuma bagla; kurulan sorgulari yakala."""

    def _wire(results=None):
        session = _CaptureSession(results)
        monkeypatch.setattr(sbs, "db_manager", _FakeDbManager(session))
        return SoruBankasiServisi(), session

    return _wire


# ---------------------------------------------------------------------------
# KUSUR 1 — select_from eksik (sorgu KURULUM aninda patliyor)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sinav_tipi", [None, "TYT"], ids=["dalsiz", "sinav_tipi"])
async def test_konu_listesi_sorgusu_kuruluyor(wired, sinav_tipi):
    """`konu_listesi_getir` sorgusu HER IKI DALDA DERLENEBILMELI.

    Olculdu (17 Agu) — hata KURULUM'da degil DERLEME'de:

        BUILD  : OK -> nesne olusuyor
        COMPILE: InvalidRequestError
        FROMS  : InvalidRequestError

    Yani `select(...)` nesnesi sorunsuz yaratiliyor; SQLAlchemi sol tarafi
    ancak derlerken cozmeye calisiyor ve SELECT listesinde yalnizca
    `QuestionMetadata.subject_area` oldugu icin sol tarafi QuestionMetadata
    saniyor. Uretimde bu `session.execute()` icinde patlar
    (`soru_bankasi_service.py:1372`), ciplak `except` yutar, `[]` doner.

    Bu yuzden asagidaki `statements == 1` YUK TASIMAZ (bugun de geciyor) —
    sadece `execute`e ulasildigini gosteren on kosuldur. Kusuru yakalayan
    assert'ler `_assert_single_from` + `_compiled_sql`.
    """
    servis, session = wired([{"scalars": ["MATEMATIK"]}])

    await servis.konu_listesi_getir(sinav_tipi)

    assert (
        len(session.statements) == 1
    ), f"on kosul: execute'a ulasilamadi, {len(session.statements)} statement"
    stmt = session.statements[0]
    _assert_single_from(stmt)
    sql = _compiled_sql(stmt)
    # JOIN yonunu de civile: `select_from(QuestionMetadata)` ile "duzeltmek"
    # sorguyu kurar ama FROM'u ters cevirir ve `is_active` filtresini anlamsiz
    # kilar.
    assert "FROM question_bank JOIN question_metadata" in sql, sql


async def test_istatistikler_irt_sorgusu_kuruluyor(wired):
    """`istatistikler_getir`'in `irt_stmt`'i (5. sorgu) DERLENEBILMELI.

    SELECT listesi YALNIZ QuestionStatistics/QuestionMetadata agregasi ->
    sol taraf cikarilamiyor -> derlemede `InvalidRequestError`.

    ZINCIRLEME RED (olculdu): bugun bu test 5. sorguya HIC ULASAMIYOR, cunku
    2. sorgunun SONUCU tuketilirken `exam_type.value` bir `str` uzerinde
    `AttributeError` atiyor ve ciplak `except` metodu erken bitiriyor ->
    yalnizca 2 statement yakalaniyor. Yani bu test ONCE kusur (2)'yi, o
    duzelince kusur (1)'i yakalar; yesile donmesi icin IKISININ DE
    duzeltilmesi gerekir.
    """
    servis, session = wired(_ISTATISTIK_RESULTS)

    await servis.istatistikler_getir()

    assert len(session.statements) >= 5, (
        f"5. sorguya ulasilamadi ({len(session.statements)} statement). "
        "Once `.value` kusuru (2) metodu erken bitiriyor olabilir."
    )
    irt_stmt = session.statements[4]
    _assert_single_from(irt_stmt)
    assert "FROM question_bank JOIN" in _compiled_sql(irt_stmt)


# NOT — SILINEN VAKUM TEST (17 Agu, olculdu):
# Buraya once `test_kardes_sorgulara_select_from_eklenmemeli` yazilmisti; fix'ten
# ONCE de GECIYORDU (1 passed). Sebep: testi kendi kurdugu sorgu uzerinde
# calisiyordu, yani `soru_bankasi_service.py`'yi HIC OKUMUYORDU — o dosyada ne
# degisirse degissin asla kirmizi veremezdi. Siki'lastirilamaz da: kardes bir
# sorguya `.select_from(QuestionBankItem)` eklemek derlenmis SQL'i BIREBIR AYNI
# birakir (S214 "sus" vakasi), dolayisiyla hicbir mutasyonla civilenemez.
# Kapsam siniri bu yuzden testle degil, modul docstring'iyle korunuyor.


# ---------------------------------------------------------------------------
# KUSUR 2 — String kolonda .value
# ---------------------------------------------------------------------------

_ISTATISTIK_RESULTS = [
    {"scalar": 36967},  # toplam_stmt
    {"all": [("TYT", 28204), ("AYT", 8763)]},  # sinav_tipi_stmt (String kolon)
    {"all": [("MATEMATIK", 7816), ("GEOMETRI", 2589)]},  # konu_stmt (String kolon)
    {"all": [(QuestionDifficultyLevel.MEDIUM, 5)]},  # zorluk_stmt (GERCEK Enum)
    {
        "first": SimpleNamespace(
            avg_difficulty=0.1,
            min_difficulty=-2.0,
            max_difficulty=2.0,
            avg_discrimination=1.2,
            avg_morphology=0.5,
            avg_readability=0.6,
        )
    },
]


async def test_konu_listesi_duz_string_donduruyor(wired):
    """`subject_area` String kolon -> `.value` `AttributeError` atar.

    Donen liste `str` uyeleri icermeli (bugun `.value` yuzunden `[]`).
    """
    servis, _ = wired([{"scalars": ["MATEMATIK", "GEOMETRI"]}])

    sonuc = await servis.konu_listesi_getir()

    assert sonuc == ["GEOMETRI", "MATEMATIK"], f"beklenmeyen sonuc: {sonuc!r}"
    assert all(type(k) is str for k in sonuc)


async def test_istatistikler_string_kolonlarda_value_kullanmiyor(wired):
    """String kolonlarda `.value` kaldirilmali, GERCEK Enum'da KORUNMALI.

    Bu test iki yonlu: `.value`'yu birakmak kirmizi verir (AttributeError ->
    sifirlanmis sozluk), ama `difficulty_level`'dan `.value`'yu SILMEK de
    kirmizi verir (anahtar `str` olmaz). ASIRI-FIX korumasi.
    """
    servis, _ = wired(_ISTATISTIK_RESULTS)

    stats = await servis.istatistikler_getir()

    assert stats["sinav_tipi_dagilimi"] == {"TYT": 28204, "AYT": 8763}
    assert stats["konu_dagilimi"] == {"MATEMATIK": 7816, "GEOMETRI": 2589}
    # GERCEK Enum kolon: `.value` KORUNMALI -> anahtar duz `str` olmali.
    # `QuestionDifficultyLevel` bir `str` karisimi DEGIL (olculdu), bu yuzden
    # `.value` silinirse asagidaki iddia duser.
    assert stats["zorluk_dagilimi"] == {"medium": 5}
    assert all(
        isinstance(k, str) for k in stats["zorluk_dagilimi"]
    ), "difficulty_level GERCEK Enum — `.value` KALDIRILMAMALI"


# ---------------------------------------------------------------------------
# KUSUR 3 — soru_guncelle eager-load'suz
# ---------------------------------------------------------------------------


async def test_soru_guncelle_uc_iliskiyi_de_eager_load_ediyor(wired):
    """`soru_guncelle` donen ORNEK'ten split alan okuyor -> eager-load SART.

    KUME esitligi kullaniliyor (S221): eksik anahtari da FAZLA anahtari da
    reddeder, `in` kontrolunden siki.
    """
    servis, session = wired([{"one": None}])

    await servis.soru_guncelle("q-1", {"question_text": "yeni metin"})

    assert len(session.statements) == 1
    stmt = session.statements[0]
    assert set(_eager_loaded(stmt)) == {"content", "metadata_info", "statistics"}, (
        "eager-load eksik -> async'te MissingGreenlet -> ciplak except -> "
        f"HTTP 404: {_eager_loaded(stmt)}"
    )


# ---------------------------------------------------------------------------
# UCTAN UCA — canli DB (kullanici gozunden)
# ---------------------------------------------------------------------------


class _RealDbManager:
    """Servisin bekledigi `get_session()` sozlesmesi, GERCEK PostgreSQL uzerinde."""

    def __init__(self, maker):
        self._maker = maker

    @asynccontextmanager
    async def get_session(self):
        async with self._maker() as session:
            yield session


def _canli_dsn() -> str | None:
    """Gercek PostgreSQL DSN'i — KIRLENMIS ortam degiskenini ATLAYARAK.

    OLCUM ALETI TUZAGI (bu turda IKI kez ısırdı, ikisi de olculdu):
    `tests/conftest.py:100` `os.environ["DATABASE_URL"]`i
    `sqlite+aiosqlite:///:memory:` yapiyor. Sonuc:
      1. `db_manager` ONCE ortam degiskenine bakiyor (`core/database.py:126`)
         -> bos SQLite.
      2. `settings.database_url` de kurtarmiyor: pydantic ortam degiskenini
         `.env` dosyasinin ONUNE koyuyor (olculdu) -> yine SQLite.
    Bu yuzden DSN `.env` dosyasindan DOGRUDAN okunuyor. `KIRO2_LIVE_DSN` ile
    ezilebilir (CI/farkli makine).

    Sir sizintisi: DSN parolasi ICERIR, o yuzden hicbir assert/skip mesajina
    KOYULMAZ (`.claude/rules/security.md`).
    """
    override = os.getenv("KIRO2_LIVE_DSN")
    if override:
        return override
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None
    for ham_satir in env_path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        satir = ham_satir.strip()
        if not satir.startswith("DATABASE_URL="):
            continue
        dsn = satir.split("=", 1)[1].strip().strip('"').strip("'")
        for eski, yeni in (
            ("postgresql+psycopg2://", "postgresql+asyncpg://"),
            ("postgresql://", "postgresql+asyncpg://"),
        ):
            if dsn.startswith(eski):
                return dsn.replace(eski, yeni, 1)
        return dsn
    return None


@pytest.fixture
async def canli_pg(monkeypatch):
    """Servisi GERCEK PostgreSQL'e baglar + aletin dogru evreni olctugunu KANITLAR.

    KONTROL KOLU (S219 dersi): bilinen sonucu (>1000 aktif satir) uretmeyen bir
    baglanti "canli DB" sayilmaz. Bu guard olmadan testler bos SQLite uzerinde
    kirmizi kalir ve fix yapilsa BILE yesile donmez — yani bulgu degil, alet
    arizasi olcuulurdu.
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
    except (
        OSError,
        SQLAlchemyError,
    ) as exc:  # pragma: no cover  # ortam kosullu: canli PG erisilebilirken bu dal hic kosmaz, kapsam disi birakilmasi kasitli
        await engine.dispose()
        pytest.skip(f"canli PostgreSQL'e baglanilamadi: {type(exc).__name__}")

    # KONTROL KOLU: yanlis evren -> SKIP, FAIL degil (SS10.64).
    # Bkz. tests/fast/test_soru_bankasi_okuma_yolu.py: ayni kol, ayni gerekce.
    # CI kendi `backend/.env`ini yazip `kiro2_test`i gosteriyor (12 tohum
    # sorusu), dolayisiyla bu kol CI'da her zaman dusuyordu; olcumu reddetmek
    # kirmizi degil skip olmali. Sayi ve esik mesajda duruyor.
    if not aktif or aktif <= 1000:
        await engine.dispose()
        pytest.skip(
            f"kontrol kolu: baglanilan DB'de {aktif} aktif soru var (esik >1000). "
            "Bu, urun havuzu degil -- olcum yapilmadi (alet arizasi olurdu)."
        )

    monkeypatch.setattr(sbs, "db_manager", _RealDbManager(maker))
    yield aktif
    await engine.dispose()


async def test_e2e_konu_listesi_bos_donmuyor(canli_pg):
    """Olculdu (17 Agu): canli DB'de 12 farkli aktif `subject_area` var.

    Bugun bu cagri `[]` donuyor — ciplak `except` iki kusuru birden yutuyor.
    """
    sonuc = await SoruBankasiServisi().konu_listesi_getir()

    assert len(sonuc) >= 2, f"konu listesi bos/eksik dondu: {sonuc!r}"
    assert all(type(k) is str for k in sonuc), sonuc


async def test_e2e_istatistikler_sifir_donmuyor(canli_pg):
    """Olculdu (17 Agu): 36.967 aktif soru, exam_type TYT/AYT.

    Bugun `toplam_soru_sayisi` 0 ve tum dagilimlar bos donuyor.
    """
    stats = await SoruBankasiServisi().istatistikler_getir()

    assert stats["toplam_soru_sayisi"] > 0, "istatistikler sifirlanmis sozluk dondu"
    assert set(stats["sinav_tipi_dagilimi"]) == {"TYT", "AYT"}, stats[
        "sinav_tipi_dagilimi"
    ]
    assert all(type(k) is str for k in stats["konu_dagilimi"])
    assert all(isinstance(k, str) for k in stats["zorluk_dagilimi"])
