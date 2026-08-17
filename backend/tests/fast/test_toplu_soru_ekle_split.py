"""`toplu_soru_ekle` + `soru_ekle` yazma yolunun #485 split sonrasi kusurlarini civiler.

Bu dosya BILINCLI olarak GERCEK PostgreSQL'e yazar. Sebebi olculdu: mevcut
`tests/unit/test_soru_bankasi_service.py::TestTopluSoruEkle` (4 test) `mock_session`
kullandigi icin uretim %100 kirikken **4/4 PASS** veriyordu. Mock'lu oturum
`commit()`'i no-op yapar, dolayisiyla NOT NULL kisiti, FK ve PG enum'u HIC
zorlanmaz — yani o testler "yaziliyor mu" sorusunu hic sormuyordu.

OLCULEN KUSURLAR (17 Agu 2026, canli PG 18.1:5434, 36.967 soru)
---------------------------------------------------------------
`toplu_soru_ekle`in 4 kusuru **SERI** baglidir: her biri giderilene kadar bir
sonraki gorunmez. Kumulatif asama olcumuyle sira birebir dogrulandi:

    ASAMA 0 -> NotNullViolationError: "soru_hash"          (yazilan 0)
    ASAMA 1 -> NotNullViolationError: "primary_topic_id"   (yazilan 0)
    ASAMA 2 -> NotNullViolationError: "grade_level"        (yazilan 0)
    ASAMA 3 -> InvalidTextRepresentationError:
               invalid input value for enum questiondifficultylevel: "medium"
    ASAMA 4 -> basarili=3 basarisiz=0                      (yazilan 3)  <- kontrol kolu

Kusur 4'un mekanizmasi sanildigi gibi `LookupError` DEGIL (olculdu):
`enums_db.QuestionDifficulty` bir `str` ALT SINIFI ve kolonun `validate_strings`
degeri `False` -> SQLAlchemy uyeyi "ham dize" sanip aynen geciriyor; PG'ye
`'medium'` gidiyor, oysa etiketler BUYUK harf. Yani hata Python'da degil
**PG'de** olusuyor:

    bind(DOGRU sinif)  -> 'MEDIUM'
    bind(YANLIS sinif) -> <QuestionDifficulty.MEDIUM: 'medium'>
    'medium' in _valid_lookup -> False   (ama LookupError ATILMIYOR)

5. KUSUR — BUGUN ULASILAMAZ, YARIN AKTIF
----------------------------------------
`_enum_donusturucu` kucuk-harf `enums_db` uyeleri dondurur ve bunlar String
kolonlara DUZ gecirilir -> `exam_type='tyt'`, `subject_area='matematik'`.
Canli kanon BUYUK harf (olculdu: TYT 28.204 / AYT 8.763, kucuk-harf **0**).

Bu kusur BUGUN canli veriye zarar VERMIYOR — cunku batch zaten `soru_hash`te
oluyor, yani kod ULASILAMAZ. Yukaridaki 4 kusur duzeltilir duzeltilmez
AKTIFLESIR. Bu yuzden ayni turda civilenmistir: aksi halde S219 deseni tekrar
ederdi (olu kod canlanir, suc SONRAKI task'a yazilir).

Kucuk-harf satirin somut zarari olculdu: `question_crud_service` gibi
case-convention'a uyan (`exam_type='TYT'`) gercek sorgulardan DUSER, yani soru
sessizce gorunmez olur.

API TUKETICISI (`api/soru_bankasi.py:776-788`)
----------------------------------------------
Yanit blogu 9 split alani PARENT uzerinden okuyor. Split sonrasi bu
`AttributeError` vermiyor (strangler devredicisi ornek duzeyini karsiliyor) —
bunun yerine:

    oturum KAPALI  -> DetachedInstanceError
    oturum ACIK    -> MissingGreenlet

Kok neden `soru_bankasi_service.py:355` `await session.refresh(yeni_soru)`:
refresh uc iliskiyi de `__dict__`'ten SILIYOR, sonraki erisim async baglamda
senkron lazy-load denemesine donusuyor. Uctaki `except Exception` bunu yutuyor
-> kullanici **HTTP 500** goruyor AMA soru DB'ye YAZILMIS oluyor (commit yanit
kurulmadan once). Bu yuzden asagidaki test dogrudan "oturum kapandiktan sonra
okunabiliyor mu" diye soruyor.

NOT: bu dosyadaki hicbir test AST sayacinin (`scan_split_accesses.py`) gordugu
bir kusuru olcmuyor — sayac yalniz SINIF duzeyi erisimi sayar ve
`api/soru_bankasi.py` onun ciktisinda HIC GORUNMUYOR (SINIF=0/ENTITY=0).
Buradaki kusurlarin tamami ORNEK duzeyi, yani sayaca yapisal olarak gorunmez
(S219: "sayacin ciktisi bir ALT SINIRDIR").
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import services.soru_bankasi_service as sbs
from models.question_bank import (
    QuestionBankItem,
    QuestionContent,
    QuestionDifficultyLevel,
    QuestionMetadata,
    QuestionStatistics,
)
from services.soru_bankasi_service import SoruBankasiServisi

# Bu turda yazilan her satir bu on ek ile isaretlenir; temizlik buna dayanir.
MARKER = "S224E2E"


# ---------------------------------------------------------------------------
# Canli PG harness'i (test_soru_bankasi_service_split.py'deki kalibin esi)
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

    `tests/conftest.py:100` `DATABASE_URL`i `sqlite+aiosqlite:///:memory:`
    yapiyor ve pydantic ortam degiskenini `.env`in ONUNE koyuyor (olculdu).
    Bu yuzden DSN `.env`ten DOGRUDAN okunur.

    Sir sizintisi: DSN parola ICERIR -> hicbir assert/skip mesajina KONULMAZ
    (`.claude/rules/security.md`).
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


async def _marker_satirlarini_sil(maker) -> None:
    """Bu turda yazilan satirlari sil. `question_bank` silmesi CASCADE eder."""
    async with maker() as session:
        await session.execute(
            text(
                "DELETE FROM question_bank WHERE id IN ("
                "  SELECT id FROM question_content WHERE question_text LIKE :on_ek"
                ")"
            ),
            {"on_ek": f"{MARKER}-%"},
        )
        await session.commit()


@pytest.fixture
async def canli_pg(monkeypatch):
    """Servisi GERCEK PostgreSQL'e baglar + aletin dogru evreni olctugunu KANITLAR.

    KONTROL KOLU (S219 dersi): bilinen sonucu (>1000 aktif satir) uretmeyen bir
    baglanti "canli DB" sayilmaz. Bu guard olmadan testler bos SQLite uzerinde
    kirmizi kalir ve fix yapilsa BILE yesile donmez — yani bulgu degil, ALET
    ARIZASI olculurdu.

    Fixture ayrica temizligi GARANTI eder: test dusse de yazilan satirlar
    silinir, yoksa bir sonraki kosum `uq_qb_soru_hash_active` ile catisir.
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
    ) as exc:  # pragma: no cover  # ortam kosullu: canli PG erisilebilirken bu dal hic kosmaz
        await engine.dispose()
        pytest.skip(f"canli PostgreSQL'e baglanilamadi: {type(exc).__name__}")

    assert aktif and aktif > 1000, (
        f"kontrol kolu DUSTU: baglanilan DB'de yalnizca {aktif} aktif soru var. "
        "Alet yanlis evreni olcuyor — bulgu degil, alet arizasi."
    )

    monkeypatch.setattr(sbs, "db_manager", _RealDbManager(maker))
    await _marker_satirlarini_sil(maker)
    try:
        yield maker
    finally:
        await _marker_satirlarini_sil(maker)
        await engine.dispose()


def _soru_verisi(etiket: str, konu: str = "Matematik") -> dict:
    """Uc noktanin urettigi sozlugun ayni sekli (api/soru_bankasi.py:753-764)."""
    benzersiz = uuid.uuid4().hex[:12]
    return {
        "soru_metni": f"{MARKER}-{etiket}-{benzersiz} Asagidakilerden hangisi dogrudur?",
        "secenekler": ["A) bir", "B) iki", "C) uc", "D) dort", "E) bes"],
        "dogru_cevap": "A",
        "cozum_aciklamasi": "olcum",
        "sinav_tipi": "TYT",
        "konu": konu,
        "zorluk_seviyesi": "orta",
        "created_by": None,
    }


async def _yazilan_satirlar(maker, etiket: str) -> list[tuple]:
    """Marker'li satirlari DORT tablodan JOIN'leyerek geri oku."""
    async with maker() as session:
        rows = await session.execute(
            select(
                QuestionBankItem.soru_hash,
                QuestionBankItem.primary_topic_id,
                QuestionMetadata.exam_type,
                QuestionMetadata.subject_area,
                QuestionMetadata.grade_level,
                QuestionStatistics.difficulty_level,
            )
            .join(QuestionContent, QuestionContent.id == QuestionBankItem.id)
            .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
            .join(QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id)
            .where(QuestionContent.question_text.like(f"{MARKER}-{etiket}-%"))
        )
        return list(rows.all())


# ---------------------------------------------------------------------------
# KUSUR 1-4 — toplu_soru_ekle hic yazmiyor (SERI bagli)
# ---------------------------------------------------------------------------


async def test_toplu_soru_ekle_gercekten_yaziyor(canli_pg):
    """Uctan uca: 3 soru verilir, 3 soru YAZILMIS olmali.

    Bugun RED: `basarili=0 / basarisiz=3`, DB'ye 0 satir
    (`NotNullViolationError: "soru_hash"`).

    Bu assert ayni anda 4 kusurun HEPSINI kapsar (seri bagli olduklari icin
    biri bile acikken sonuc 0'dir); tekil kusurlari asagidaki testler ayirir.
    """
    sorular = [_soru_verisi("yaz") for _ in range(3)]

    sonuc = await SoruBankasiServisi().toplu_soru_ekle(sorular)

    satirlar = await _yazilan_satirlar(canli_pg, "yaz")
    assert sonuc["basarisiz"] == 0, f"hatalar: {sonuc.get('hatalar')}"
    assert sonuc["basarili"] == 3, sonuc
    assert len(satirlar) == 3, f"DB'ye yazilan satir: {len(satirlar)} (beklenen 3)"


async def test_toplu_soru_ekle_not_null_alanlarini_dolduruyor(canli_pg):
    """`soru_hash` + `primary_topic_id` + `grade_level` DB'de DOLU olmali.

    Ucu de NOT NULL ve DB-default'suz (olculdu, `information_schema`).
    `toplu_soru_ekle` ucunu de hic set etmiyordu.

    `soru_hash`in yalniz "dolu" degil AYIRT EDICI oldugu da iddia edilir:
    sabit bir dize donduren naif bir fix `uq_qb_soru_hash_active` ile
    catisirdi ama ilk satirda fark edilmezdi.
    """
    sorular = [_soru_verisi("notnull") for _ in range(2)]

    await SoruBankasiServisi().toplu_soru_ekle(sorular)

    satirlar = await _yazilan_satirlar(canli_pg, "notnull")
    assert len(satirlar) == 2, f"yazilan satir {len(satirlar)}"
    for soru_hash, topic_id, _, _, grade_level, _ in satirlar:
        assert soru_hash, "soru_hash NULL/bos"
        assert topic_id, "primary_topic_id NULL/bos"
        assert grade_level is not None, "grade_level NULL"
        assert 9 <= grade_level <= 12, f"check_grade_level ihlali: {grade_level}"
    hashler = {satir[0] for satir in satirlar}
    assert len(hashler) == 2, f"soru_hash ayirt edici degil: {hashler}"


async def test_toplu_soru_ekle_difficulty_level_pg_enumuna_uyuyor(canli_pg):
    """`difficulty_level` 5-seviyeli `QuestionDifficultyLevel` uyesi olmali.

    Bugun 3-seviyeli `enums_db.QuestionDifficulty` geciriliyor; `str` alt sinifi
    oldugu icin SQLAlchemy onu ham dize sanip PG'ye `'medium'` yolluyor ve PG
    `invalid input value for enum questiondifficultylevel: "medium"` diyor.

    `is` DEGIL `==` kullanilmasi kasitli: onemli olan uyenin KIMLIGI degil, PG'ye
    dogru etiketin (`MEDIUM`) yazilmasi.
    """
    await SoruBankasiServisi().toplu_soru_ekle([_soru_verisi("zorluk")])

    satirlar = await _yazilan_satirlar(canli_pg, "zorluk")
    assert len(satirlar) == 1, f"yazilan satir {len(satirlar)}"
    zorluk = satirlar[0][5]
    assert isinstance(
        zorluk, QuestionDifficultyLevel
    ), f"difficulty_level yanlis enum sinifi: {type(zorluk)!r} ({zorluk!r})"
    assert zorluk == QuestionDifficultyLevel.MEDIUM, zorluk


# ---------------------------------------------------------------------------
# KUSUR 5 — casing (bugun ULASILAMAZ, 1-4 duzelince AKTIF)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("konu", "beklenen_subject"),
    [("Matematik", "MATEMATIK"), ("Türkçe", "TURKCE")],
    ids=["matematik", "turkce"],
)
async def test_toplu_soru_ekle_kanonik_buyuk_harf_yaziyor(
    canli_pg, konu, beklenen_subject
):
    """`exam_type`/`subject_area` canli kanona (BUYUK harf) uymali.

    Olculdu: canli dagilim TYT 28.204 / AYT 8.763, kucuk-harf satir **0**.
    `_enum_donusturucu` `<ExamType.TYT: 'tyt'>` dondurur ve String kolona duz
    gecerse DB'ye `'tyt'` yazilir -> `exam_type='TYT'` filtreleyen gercek
    servis sorgularindan DUSER (soru sessizce gorunmez olur).

    Iki parametre gerekli: tek `Matematik` dali Turkce karakterli girdinin
    `subject_db()` ile normalize edildigini olcmez (I/i tuzagi,
    `.claude/rules/case-convention.md`).

    `str(ExamType.TYT)` ile "duzeltmek" UCUNCU bir bozulma sinifidir — Python
    3.13'te `'ExamType.TYT'` yazar (olculdu) — bu yuzden esitlik iddia edilir,
    "buyuk harf mi" degil.
    """
    await SoruBankasiServisi().toplu_soru_ekle([_soru_verisi(konu, konu=konu)])

    satirlar = await _yazilan_satirlar(canli_pg, konu)
    assert len(satirlar) == 1, f"yazilan satir {len(satirlar)}"
    _, _, exam_type, subject_area, _, _ = satirlar[0]
    assert exam_type == "TYT", f"exam_type kanonik degil: {exam_type!r}"
    assert (
        subject_area == beklenen_subject
    ), f"subject_area kanonik degil: {subject_area!r}"


# ---------------------------------------------------------------------------
# soru_ekle (tekil) — kosulsuz ValueError + tuketilemeyen donus
# ---------------------------------------------------------------------------


async def test_soru_ekle_topic_cozumleyip_yaziyor(canli_pg):
    """`soru_ekle` bu DB'de KOSULSUZ `ValueError` atmamali.

    Olculdu: `topic_hierarchy`in 12 satirinin 12'sinde `subject_area` NULL, bu
    yuzden servisteki iki lookup da 0 satir doner ve fonksiyon
    `ValueError("topic_hierarchy'de '<X>' icin kayit yok")` atar -> uc HTTP 500.
    Yani `POST /soru-ekle` bu makinede HIC calismiyor.
    """
    soru = await SoruBankasiServisi().soru_ekle(_soru_verisi("tekil"))

    assert soru is not None
    satirlar = await _yazilan_satirlar(canli_pg, "tekil")
    assert len(satirlar) == 1, f"soru_ekle DB'ye yazmadi: {len(satirlar)} satir"
    assert satirlar[0][1], "primary_topic_id doldurulmadi"


async def test_soru_ekle_donusu_oturum_kapaninca_okunabiliyor(canli_pg):
    """Donen nesnenin 9 yanit alani oturum KAPANDIKTAN sonra okunabilmeli.

    Bu, `api/soru_bankasi.py:776-788`in yaptigi seyin birebir ayni sekli.
    Bugun RED: `DetachedInstanceError` (oturum kapali) / `MissingGreenlet`
    (oturum acik), cunku servis :355 `session.refresh()` uc iliskiyi de
    `__dict__`ten siliyor. Uctaki `except Exception` bunu yutup HTTP 500
    veriyor — ama satir ZATEN yazilmis oluyor.

    Alanlar PARENT uzerinden DEGIL yavru tablolardan okunur: strangler
    devredicisi bugun calisiyor olsa bile lazy-load'a dustugu icin
    guvenilmez, ve devredici gecici (silinecek).
    """
    soru = await SoruBankasiServisi().soru_ekle(_soru_verisi("detach"))

    # Oturum burada KAPANMIS durumda (servis `async with` blogundan cikti).
    assert soru.content.question_text.startswith(f"{MARKER}-detach-")
    assert soru.content.correct_answer == "A"
    assert soru.metadata_info.exam_type == "TYT"
    assert soru.metadata_info.subject_area == "MATEMATIK"
    assert soru.metadata_info.grade_level is not None
    assert soru.metadata_info.morphology_complexity is not None
    assert soru.metadata_info.readability_score is not None
    assert soru.statistics.difficulty_level == QuestionDifficultyLevel.MEDIUM
    assert soru.statistics.irt_difficulty is not None


async def test_soru_ekle_mukerrer_soruda_mevcut_kaydi_donuyor(canli_pg):
    """Ayni soru iki kez eklenirse ikincisi MEVCUT kaydi donmeli, patlamamali.

    `uq_qb_soru_hash_active` kismi benzersizlik indeksi ikinci INSERT'i
    `IntegrityError` ile reddediyor; servis bunu yakalayip `soru_hash` ile
    mevcut kaydi geri okuyor ve `zaten_mevcuttu = True` isaretliyor.

    NEDEN VAR: bu dal KANITLANMIS sekilde testsizdi. Ortak yardimciya gecerken
    yerel `soru_hash` degiskeni kalkti ama bu dal ona atifta bulunmaya devam
    etti; hicbir test dusmedi (hepsi benzersiz metin kullaniyor) ve kusuru
    KAPI yakaladi (ruff F821 x2). `reference_formatter-import-stripping` ile
    ayni sinif: alan tasindiginda GERIYE KALAN atiflar taranmali.

    Mutasyonla civili: `alanlar["soru_hash"]` -> `soru_hash` yapilirsa
    `NameError`, sabit bir dize yapilirsa mevcut kayit bulunamaz.
    """
    veri = _soru_verisi("mukerrer")
    servis = SoruBankasiServisi()

    birinci = await servis.soru_ekle(veri)
    ikinci = await servis.soru_ekle(dict(veri))

    assert birinci.id == ikinci.id, "mukerrer ekleme YENI satir yaratti"
    assert getattr(birinci, "zaten_mevcuttu", None) is False
    assert getattr(ikinci, "zaten_mevcuttu", None) is True
    assert len(await _yazilan_satirlar(canli_pg, "mukerrer")) == 1


# ---------------------------------------------------------------------------
# HTTP KATMANI — uc noktalar (api/soru_bankasi.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def uc_ortami(monkeypatch):
    """Uc fonksiyonlarini DOGRUDAN cagirabilmek icin Redis'i devre disi birak.

    Yalnizca `invalidate_question_cache` no-op'lanir — servis, ORM ve DB
    GERCEKTIR. Uc fonksiyonlari `Depends(...)` cozumlemesi olmadan cagrilir,
    bu yuzden `current_user`/`db` elle verilir.
    """
    import api.soru_bankasi as api_sb

    async def _no_op():
        return None

    monkeypatch.setattr(api_sb, "invalidate_question_cache", _no_op)
    return api_sb


def _sahte_kullanici():
    return SimpleNamespace(id=None, role="ADMIN")


async def test_uc_soru_ekle_201_ve_yavru_alanlari_donuyor(canli_pg, uc_ortami):
    """`POST /soru-ekle` 500 DEGIL 201 donmeli ve yanit alanlari DOLU olmali.

    Bugun RED (iki ayri sebep, seri): once servis `ValueError` atiyor
    (topic gate), o asilsa bile yanit blogu `DetachedInstanceError` aliyor.
    Ikisini de `except Exception` yutup HTTP 500 yapiyor.

    `difficulty` icin `.name` (BUYUK harf) iddia edilir: kolon `Enum`'unun DB
    temsili ADdir ve ayni ifadedeki fallback zaten `"MEDIUM"` — `.value`
    (`'medium'`) ayni alani kendi icinde tutarsiz birakiyordu.
    """
    istek = uc_ortami.SoruEkleRequest(
        soru_metni=f"{MARKER}-uc1-{uuid.uuid4().hex[:12]} Bu bir olcum sorusudur?",
        secenekler=["A) bir", "B) iki", "C) uc", "D) dort", "E) bes"],
        dogru_cevap="A",
        cozum_aciklamasi="olcum",
        sinav_tipi="TYT",
        konu="Matematik",
        zorluk_seviyesi="orta",
    )

    yanit = await uc_ortami.soru_ekle(
        request=istek, current_user=_sahte_kullanici(), db=None
    )

    govde = json.loads(bytes(yanit.body))
    assert yanit.status_code == 201, govde
    veri = govde["data"]
    assert veri["question_text"].startswith(f"{MARKER}-uc1-")
    assert veri["exam_type"] == "TYT"
    assert veri["subject_area"] == "MATEMATIK"
    assert veri["difficulty"] == "MEDIUM", veri["difficulty"]
    assert veri["irt_parameters"]["difficulty"] is not None
    assert veri["morphology_complexity"] is not None
    assert veri["readability_score"] is not None


async def test_uc_toplu_soru_ekle_201_ve_ekliyor(canli_pg, uc_ortami):
    """`POST /toplu-soru-ekle` gercekten eklemeli ve 201 donmeli."""
    sorular = [_soru_verisi("uc2") for _ in range(2)]
    istek = uc_ortami.TopluSoruEkleRequest(sorular=sorular)

    yanit = await uc_ortami.toplu_soru_ekle(
        request=istek, current_user=_sahte_kullanici(), db=None
    )

    govde = json.loads(bytes(yanit.body))
    assert yanit.status_code == 201, govde
    assert govde["success"] is True
    assert govde["data"]["basarili"] == 2, govde
    assert len(await _yazilan_satirlar(canli_pg, "uc2")) == 2


async def test_uc_hicbir_soru_eklenmezse_201_donmuyor_ve_sql_sizdirmiyor(
    canli_pg, uc_ortami, monkeypatch
):
    """SIFIR ekleme -> 201 DEGIL; ve `hatalar` ham SQL/parametre SIZDIRMAMALI.

    Bugun RED: uc **201 CREATED + "success": true + "0/2 soru basariyla
    eklendi"** donuyor ve govdede tam SQLAlchemy istisnasi var — INSERT
    deyiminin kendisi, bind parametreleri ve `created_by` kullanici kimligi
    dahil (olculdu).

    Basarisizlik GERCEK bir kusurla degil, servis duzeyinde enjekte edilerek
    uretilir: boylece test HTTP SOZLESMESINI olcer, dogrulugu tekrar dogrulanan
    yazma yolunu degil. Aksi halde 1-4 kusurlari duzeldigi an bu test
    anlamsizlasirdi.
    """
    hassas = (
        "Batch insert hatası: (asyncpg.NotNullViolationError) ... "
        "[SQL: INSERT INTO question_bank (id, soru_hash, ...) VALUES ($1::VARCHAR, ...)] "
        "[parameters: ('01a0-gizli-id', None, None, False, 'gizli-kullanici-kimligi')]"
    )

    async def _hep_dusen(_sorular):
        return {"basarili": 0, "basarisiz": 2, "toplam": 2, "hatalar": [hassas]}

    monkeypatch.setattr(uc_ortami.soru_bankasi_servisi, "toplu_soru_ekle", _hep_dusen)
    istek = uc_ortami.TopluSoruEkleRequest(
        sorular=[_soru_verisi("uc3") for _ in range(2)]
    )

    yanit = await uc_ortami.toplu_soru_ekle(
        request=istek, current_user=_sahte_kullanici(), db=None
    )

    ham_govde = bytes(yanit.body).decode("utf-8")
    govde = json.loads(ham_govde)
    assert yanit.status_code != 201, f"sifir ekleme 201 dondu: {govde}"
    assert govde["success"] is False, govde
    for sizinti in ("INSERT INTO", "parameters:", "gizli-kullanici-kimligi", "[SQL:"):
        assert sizinti not in ham_govde, f"istemciye sizdi: {sizinti!r}"
    assert govde["data"]["hata_sayisi"] == 1, govde["data"]
