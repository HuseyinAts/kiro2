"""TDD RED kaniti + regresyon bekcisi — Y2 / TRACK A-cat_session (P0).

`app/services/cat_session.py` icindeki UC ham SQL blogu ve `app/api/cat.py`
icindeki bir dorduncusu, `question_bank`'in 69-alan split'inden (S210,
`0fd9b8413`) ONCEKI semayi varsayiyor. Split sonrasi `question_bank`ta
yalnizca 12 kolon var; sorgularin okudugu alanlar cocuk tablolara tasindi:

    question_content     : question_text, option_a..e, correct_answer,
                           question_image_url, image_width/height, image_ocr_text
    question_metadata    : subject_area, exam_type, ...
    question_statistics  : irt_discrimination, irt_difficulty, irt_guessing,
                           is_calibrated, is_calib_pool, quality_review_status

Bu ham SQL oldugu icin ORM devredicisi (models/question_bank.py:545-587)
DEVREYE GIRMEZ; PostgreSQL dogrudan `UndefinedColumnError` atar. Ayni sebeple
AST tabanli `scripts/scan_split_accesses.py` bu dosyayi YAPISAL OLARAK
goremedi (string literal icinde `Attribute` dugumu yoktur).

OLCULEN ETKI (bu turda, canli DB):
  * `_get_candidate_questions` (warm_up ve ZPD dallari) -> UndefinedColumn
  * `_fetch_question_detail`                            -> UndefinedColumn
  * POST /api/v1/cat/next                               -> HTTP 500
    (uc `get_optional_user` kullanir, auth GEREKTIRMEZ -> misafir dahil herkes)
  * `app/api/cat.py::_check_answer`                     -> SESSIZ False
    (`except Exception` yutuyor; her CAT yaniti YANLIS sayiliyor)

NEDEN GERCEK POSTGRES (mock DB DEGIL): S228'de olculdu ki `AsyncMock`'lu 50
test bu kusur sinifini yapisal olarak goremiyordu — mock her kolon adini
kabul eder. Sema kaymasi yalnizca gercek semaya karsi olculebilir.

NEDEN HEM VERI HEM YAPISAL ASSERT: filtrelerin ayirt edici gucu bu turda
tek tek olculdu (MATEMATIK, ZPD dali):

    tam filtre                       2798 satir
    sekil-regex silinirse            4439 satir  <- 1641 sekil-bagimli sizar
    mv_safe_for_beta kapisi silinirse 2798 satir  <- veri duzeyinde AYIRT EDILEMEZ
    quality_review_status silinirse   2798 satir  <- ayni
    is_active silinirse               2798 satir  <- ayni

Yani kapi/durum/aktiflik filtreleri bu veri setinde birbirini kapsiyor;
"donen id'ler kapinin icinde" demek onlari CIVILEMEZ (vakum assert). Bu
yuzden onlar KOSULAN HAM SQL uzerinde iddia ediliyor (ham SQL bu kodun
gercek artefakti), sekil-regex ise veri duzeyinde — orada ayirt edici.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

# `live_db` fixture'i tests/integration/conftest.py'de — DSN kaynak koda
# GOMULMEZ, ortam degiskeninden veya backend/.env'den cozulur ve postgres
# olmayan DSN reddedilir (sessizce sqlite'a dusmeyi onler).
pytestmark = pytest.mark.asyncio

# --- BOS KAPI ANKRAJI (20 Agu 2026) ----------------------------------------
# Bu dosyanin olctugu sey SEMA/SORGU DOGRULUGU (split sonrasi ham SQL dogru
# tablolara mi vuruyor). Dolu bir aday havuzu ONKOSULDUR, test edilen sey
# degildir. 20 Agu'da 36.967 kitapsiz (sentetik) satir silindi ve
# `mv_safe_for_beta` 27.073 -> 0'a dustu; veri donmesini bekleyen 9 test
# kirmizi verdi. Bu kirmizi SEMA hakkinda YANLIS bir ifadedir -- sema saglam,
# olculecek satir yok.
#
# NEDEN skip DEGIL xfail(strict): skip sessizdir ve aliskanliga doner
# (`test_icerik_gecerliligi.py` ayni gerekceyle xfail sectti). strict=True,
# gercek icerik gelip testler gecmeye basladiginda XPASS ile KIRAR --
# yani "isareti kaldir" sinyali otomatik gelir. SQL METNI uzerinde iddia eden
# kardes testler (warm_up, kalite_kapisi, aday_sorgusu_join) isaretlenmedi:
# onlar bos havuzda da olcuyor ve GECIYOR.
_BOS_KAPI = (
    "mv_safe_for_beta BOS (0 satir) — 36.967 kitapsiz sentetik satir 20 Agu "
    "2026'da silindi (S238; 180/180 adversarial cop, ozgulluk %100). Bu test "
    "dolu aday havuzu ONKOSULU ister; sema kusuru DEGIL. Y11/MAT gocu havuzu "
    "doldurunca XPASS verip KIRACAK — o an bu isaret KALDIRILACAK."
)
_bos_kapi_xfail = pytest.mark.xfail(strict=True, reason=_BOS_KAPI)

# Yerlestirme dersi: app/api/cat.py::PLACEMENT_SUBJECT ile ayni.
DERS = "MATEMATIK"

# Sekil/gorsel bagimli sorulari eleyen suzgec (Bug #11, 18 May 2026).
# Sozlesme olarak burada TEKRAR taniminir: fix suzgeci silerse veri
# duzeyindeki assert dusmeli. Olculdu — suzgecsiz havuzun %37'si eslesiyor,
# 100'luk ornekte kacirma olasiligi pratikte sifir.
SEKIL_REGEX = (
    r"[şŞ]ekil|[yY]ukarıda|[aA]şağıda|verilen graf|verilen tablo|[tT]abloda"
    r"|[gG]rafikte|[şŞ]emada|[hH]aritada|[vV]erilenler|aşağıdaki şek|[gG]örsel"
    r"|[kK]avram harita|[dD]eney düzene|numaraland.* özelli|şekildeki kap"
    r"|[cC]am boru|[pP]aralelkenar|şek\.|şek |[dD]ik üçgen|[eE]şkenar üçgen"
    r"|[iI]kizkenar üçgen"
)

COCUK_TABLOLAR = ("question_content", "question_metadata", "question_statistics")
KABUL_EDILEN_DURUMLAR = ("human_verified", "auto_judged_high")


# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------


class _SqlKaydeden:
    """live_db'yi SARAN gecirgen vekil — sorgular GERCEK Postgres'e gider.

    Amaci mock'lamak DEGIL, kosulan ham SQL metnini yakalamak. Servis
    `self.db` uzerinde yalnizca `execute`/`commit` kullanir (olculdu:
    cat_session.py'de 15 cagri, hepsi bu ikisi).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.sorgular: list[str] = []

    async def execute(self, stmt: Any, *args: Any, **kwargs: Any) -> Any:
        self.sorgular.append(str(stmt))
        return await self._session.execute(stmt, *args, **kwargs)

    def __getattr__(self, ad: str) -> Any:
        return getattr(self._session, ad)

    def son_sorgu(self) -> str:
        assert self.sorgular, "Hic SQL kosulmadi — olcum aleti arizali"
        return self.sorgular[-1]


def _sadelestir(sql: str) -> str:
    """Bosluklari tekillestirip kucuk harfe cevir — bicimden bagimsiz eslesme."""
    return re.sub(r"\s+", " ", sql).lower()


def _join_kosulu(sql: str, tablo: str) -> tuple[str, str] | None:
    """`JOIN <tablo> [alias] ON <sol> = <sag>` kosulunun iki tarafini dondur."""
    kalip = (
        rf"join\s+{tablo}\b(?:\s+as)?(?:\s+(?!on\b)\w+)?\s+on\s+([\w.]+)\s*=\s*([\w.]+)"
    )
    eslesme = re.search(kalip, _sadelestir(sql))
    return (eslesme.group(1), eslesme.group(2)) if eslesme else None


async def _ornek_soru(db: AsyncSession) -> tuple[str, str]:
    """Aktif + kapi-ici bir sorunun (id, correct_answer) ciftini dondur."""
    sonuc = await db.execute(
        text(
            "SELECT qb.id::text, qc.correct_answer "
            "FROM question_bank qb JOIN question_content qc ON qc.id = qb.id "
            "WHERE qb.is_active = TRUE AND qc.correct_answer IS NOT NULL "
            "AND qb.id IN (SELECT id FROM mv_safe_for_beta) LIMIT 1"
        )
    )
    satir = sonuc.fetchone()
    assert satir is not None, "Kapi-ici aktif soru yok — test verisi on kosulu"
    return satir[0], satir[1]


async def _canli_redis():
    """Yanit VEREN ilk Redis'i dondur; hicbiri yoksa None.

    NEDEN ADAY LISTESI (bu turda olculdu): `backend/conftest.py:25` test
    kosumunda `REDIS_URL`i `redis://localhost:6380/1` yapiyor ve bu makinede
    6380'de HICBIR SEY DINLEMIYOR (`[Errno 10061] Connect call failed`).
    Gercek Redis 6379'da ayakta ve CAT oturumlari orada tutuluyor. Tek adaya
    bakan bir kontrol, ayakta olan bir altyapiyi "yok" diye raporlayip testi
    sessizce atlatirdi — yani skip bir OLCUM DEGIL, alet arizasi olurdu.

    Adaylarin hicbiri yanit vermezse None doner (cagiran skip eder); sahte
    bir istemciye DUSULMEZ.
    """
    import redis.asyncio as aioredis

    adaylar = [
        os.getenv("KIRO2_TEST_REDIS_URL"),
        os.getenv("REDIS_URL"),
        "redis://localhost:6379/1",
    ]
    for url in dict.fromkeys(a for a in adaylar if a):
        istemci = aioredis.from_url(url, decode_responses=False)
        try:
            await istemci.ping()
            return istemci
        except Exception:
            await istemci.aclose()
    return None


@pytest_asyncio.fixture
async def cat_servis(live_db: AsyncSession):
    """SQL kaydedici vekile bagli CATSessionService (Redis'siz — DB yollari)."""
    from app.services.cat_session import CATSessionService

    kaydeden = _SqlKaydeden(live_db)
    servis = CATSessionService(redis=None, db=kaydeden)
    servis.kaydeden = kaydeden  # testlerin ham SQL'e erisimi
    return servis


@pytest_asyncio.fixture
async def cat_client(live_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """POST /api/v1/cat/next icin in-process istemci.

    `raise_app_exceptions=False`: uretimdeki davranisi (HTTP 500) taklit eder,
    istisnayi teste sizdirmaz — boylece assert HTTP durumu uzerinden yapilir,
    tipki canli `curl` olcumundeki gibi.
    """

    from app.api.cat import router as cat_router
    from app.core.deps import get_db, get_redis
    from core.ddos_protection import limiter

    redis_client = await _canli_redis()

    if redis_client is None:
        pytest.skip(
            "Hicbir Redis adayi yanit vermedi — CAT oturumu Redis'siz kurulamaz"
        )

    app = FastAPI()
    app.state.limiter = limiter

    # Hiz siniri DEPOSU `settings.redis_url`e IMPORT ANINDA baglanir
    # (core/ddos_protection.py:70) ve `backend/conftest.py:25` test kosumunda
    # bunu `redis://localhost:6380/1` yapiyor — o portta hicbir sey dinlemiyor.
    # `_canli_redis()` yalniz SERVIS istemcisini kurtariyor; limiter deposu
    # ayri bir yol ve oradan ham `redis.exceptions.ConnectionError` geliyor.
    # `RateLimitExceeded` icin de islenici kayitli olmadigindan istisna 500'e
    # donusuyor ve SPLIT GOCUYLE ILGISIZ bir 500 uretiyor.
    #
    # OLCULDU (18 Agu): ayni uc, limiter devre disiyken 200 + gercek soru
    # metni + 5 sik donduruyor; limiter aciksa 500. Yani bu testlerin gordugu
    # 500 URUN KUSURU DEGIL, olcum aletinin arizasiydi.
    #
    # Bu iki test SPLIT GOCUNU olcer, hiz siniri politikasini DEGIL — onun
    # kendi bekcisi var: tests/fast/test_rate_limit_tutarliligi.py
    _limiter_onceki = limiter.enabled
    limiter.enabled = False

    app.include_router(cat_router)

    async def _override_db():
        yield live_db

    async def _override_redis():
        return redis_client

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    # Kuresel durum sizmasin: limiter modul duzeyinde tekil bir nesne.
    limiter.enabled = _limiter_onceki
    await redis_client.aclose()


# ---------------------------------------------------------------------------
# 1) Aday soru sorgulari — cat_session.py:258-297 (warm_up) ve :301-328 (ZPD)
# ---------------------------------------------------------------------------


async def test_warm_up_aday_sorgusu_undefined_column_atmiyor(cat_servis):
    """warm_up dali kurulabilmeli.

    Havuzun BOS olmasi kabul edilir (canli veride is_calib_pool=0 ve
    irt_difficulty tek degerli 0.0 -> b<-0.5 kosulu bos kume verir; bu ayri
    bir icerik sorunu, Y4). Olculen sey sorgunun KOSABILMESI.
    """
    adaylar = await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=True)
    assert isinstance(adaylar, list)


@_bos_kapi_xfail
async def test_zpd_aday_sorgusu_dolu_havuz_donduruyor(cat_servis):
    """ZPD dali gercek IRT parametreleriyle dolu bir havuz dondurmeli."""
    from app.services.irt_engine import ItemParams

    adaylar = await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=False)

    assert adaylar, f"{DERS} icin ZPD havuzu bos — start_session ValueError atardi"
    for aday in adaylar:
        assert isinstance(aday, ItemParams)
        assert isinstance(aday.question_id, str) and aday.question_id
        for ad, deger in (("a", aday.a), ("b", aday.b), ("c", aday.c)):
            assert isinstance(deger, float), f"{ad} float degil: {deger!r}"


@_bos_kapi_xfail
async def test_aday_irt_parametreleri_question_statistics_ten_geliyor(
    cat_servis, live_db: AsyncSession
):
    """Donen a/b/c, o id'nin `question_statistics` satiriyla BIREBIR ayni olmali.

    Bu, "IRT parametreleri dogru cocuk tablodan ve `id` uzerinden okundu"
    iddiasini veriye baglar; sabit/uydurma deger donduren bir fix dusurur.
    """
    adaylar = await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=False)
    assert adaylar, "Havuz bos — parametre karsilastirmasi yapilamaz"

    ornek = adaylar[:20]
    sonuc = await live_db.execute(
        text(
            "SELECT id::text, irt_discrimination, irt_difficulty, irt_guessing "
            "FROM question_statistics WHERE id::text = ANY(:idler)"
        ),
        {"idler": [a.question_id for a in ornek]},
    )
    beklenen = {r[0]: (float(r[1]), float(r[2]), float(r[3])) for r in sonuc.fetchall()}

    assert len(beklenen) == len(
        ornek
    ), "Bazi adaylarin question_statistics satiri yok — JOIN anahtari yanlis olabilir"
    for aday in ornek:
        assert (aday.a, aday.b, aday.c) == beklenen[aday.question_id], (
            f"{aday.question_id}: servis {(aday.a, aday.b, aday.c)} != "
            f"DB {beklenen[aday.question_id]}"
        )


@_bos_kapi_xfail
async def test_aday_sorgusu_sekil_bagimli_sorulari_disliyor(
    cat_servis, live_db: AsyncSession
):
    """Sekil/gorsel bagimli sorular havuza SIZMAMALI.

    "Gocurdun mu" degil "korudun mu" olcumu (S219 dersi): suzgeci silip
    sorguyu calisir hale getiren bir fix bu testi dusurur. Olculdu: suzgec
    kalkarsa MATEMATIK havuzunun 1641/4439'u (%37) eslesiyor.
    """
    adaylar = await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=False)
    assert adaylar, "Havuz bos — suzgec olcumu yapilamaz"

    sonuc = await live_db.execute(
        text(
            "SELECT id::text FROM question_content "
            "WHERE id::text = ANY(:idler) AND question_text ~* :rx"
        ),
        {"idler": [a.question_id for a in adaylar], "rx": SEKIL_REGEX},
    )
    sizanlar = [r[0] for r in sonuc.fetchall()]
    assert not sizanlar, (
        f"{len(sizanlar)}/{len(adaylar)} sekil-bagimli soru havuza sizdi: "
        f"{sizanlar[:5]}"
    )


async def test_aday_sorgusu_split_tablolara_id_uzerinden_join_ediyor(cat_servis):
    """Ham SQL, tasinan alanlari cocuk tablolardan ve `id = id` ile okumali.

    Canli FK tanimlarindan olculdu: question_content/metadata/statistics'in
    PK'si `id`dir ve `question_bank.id`ye bagliDIR — `question_id` diye bir
    kolon YOKTUR. En olasi yanlis fix budur, o yuzden ayrica yasaklanir.
    """
    await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=False)
    sql = cat_servis.kaydeden.son_sorgu()
    sade = _sadelestir(sql)

    assert (
        "question_id" not in sade
    ), "Split cocuk tablolarinda `question_id` kolonu YOK; JOIN `id` uzerinden olmali"
    for tablo in COCUK_TABLOLAR:
        assert tablo in sade, f"{tablo} sorguda yok — tasinan alanlar okunamaz"

    for tablo in ("question_content", "question_statistics"):
        kosul = _join_kosulu(sql, tablo)
        assert kosul is not None, f"{tablo} icin JOIN ... ON kosulu bulunamadi"
        sol, sag = kosul
        assert (
            sol.split(".")[-1] == "id" and sag.split(".")[-1] == "id"
        ), f"{tablo} JOIN kosulu `id = id` degil: {sol} = {sag}"


async def test_aday_sorgusu_kalite_kapisini_koruyor(cat_servis):
    """Kalite kapisi + is_active + durum suzgeci ham SQL'de DURMALI.

    Bunlar veri duzeyinde birbirini kapsadigi icin (olculdu: uc filtreyi de
    tek tek silmek satir sayisini 2798'de birakiyor) donen id kumesiyle
    civilenemez. Ham SQL bu kodun gercek artefakti oldugundan iddia orada.
    """
    await cat_servis._get_candidate_questions(DERS, 0.0, warm_up=False)
    sade = _sadelestir(cat_servis.kaydeden.son_sorgu())

    from core.quality_gate import SAFE_POOL_RELATION

    assert SAFE_POOL_RELATION in sade, "Kalite kapisi (mv_safe_for_beta) kaldirilmis"
    assert (
        "is_active" in sade
    ), "is_active suzgeci kaldirilmis (kapi onun YERINE gecmez)"
    assert "quality_review_status" in sade, "quality_review_status suzgeci kaldirilmis"
    for durum in KABUL_EDILEN_DURUMLAR:
        assert durum in sade, f"Kabul edilen durum '{durum}' sorgudan dusmus"


# ---------------------------------------------------------------------------
# 2) Soru detayi — cat_session.py:357-381
# ---------------------------------------------------------------------------


@_bos_kapi_xfail
async def test_soru_detayi_undefined_column_atmiyor_ve_dolu_donuyor(
    cat_servis, live_db: AsyncSession
):
    """Aday sorgusu duzelse bile `_fetch_question_detail` ayrica patliyordu."""
    qid, _ = await _ornek_soru(live_db)
    detay = await cat_servis._fetch_question_detail(qid)

    assert detay is not None, f"{qid} aktif ve kapi-ici oldugu halde detay None"
    assert detay["question_id"] == qid
    assert isinstance(detay["stem"], str) and detay["stem"].strip()


@_bos_kapi_xfail
async def test_soru_detayi_tuketici_sozlesmesini_koruyor(
    cat_servis, live_db: AsyncSession
):
    """SELECT takma adlari degismemeli — cat_session.py:386-403 ve cat.py:_madde
    bu adlara gore govde kuruyor. Kaynak tablo nitelenir, ALIAS korunur.
    """
    qid, dogru_sik = await _ornek_soru(live_db)
    detay = await cat_servis._fetch_question_detail(qid)
    assert detay is not None, "Detay None — sozlesme dogrulanamaz"

    for anahtar in (
        "question_id",
        "stem",
        "options",
        "correct_option",
        "topic_id",
        "konu",
        "subject_id",
        "irt",
        "question_image_url",
        "image_alt_text",
        "image_width",
        "image_height",
    ):
        assert anahtar in detay, f"Tuketici sozlesmesindeki '{anahtar}' anahtari yok"

    secenekler = detay["options"]
    assert isinstance(secenekler, dict), f"options dict degil: {type(secenekler)}"
    for harf in ("A", "B", "C", "D"):
        assert harf in secenekler, f"'{harf}' sikki options'ta yok"

    assert detay["correct_option"] == dogru_sik
    assert set(detay["irt"]) == {"difficulty", "discrimination", "guessing"}
    for ad, deger in detay["irt"].items():
        assert isinstance(deger, float), f"irt.{ad} float degil: {deger!r}"


@_bos_kapi_xfail
async def test_soru_detayi_split_tablolara_id_uzerinden_join_ediyor(
    cat_servis, live_db: AsyncSession
):
    """Detay sorgusu da `id = id` ile JOIN etmeli — aday sorgusu bekcisinin ikizi.

    NEDEN AYRI BIR YAPISAL ASSERT (bu turda mutasyonla OLCULDU): detay
    blogunun IRT degerleri veri duzeyinde AYIRT EDILEMEZ. Canli veride
    `question_statistics` tek degerli (a=1.0, b=0.0, c=0.25 — 36967/36967
    satir) ve `_fetch_question_detail`'daki COALESCE varsayilanlari
    (1.0/0.0/0.25) TAM ayni sayilar. Yani JOIN anahtari bozulup satir NULL
    donse bile donen sozluk birebir ayni kalir. Olculdu: `ON qs.id =
    qb.primary_topic_id` mutasyonu diger 11 testin HEPSINI yesil birakti
    (11 passed). Kusur ancak kosulan ham SQL uzerinde gorulebilir.
    """
    qid, _ = await _ornek_soru(live_db)
    await cat_servis._fetch_question_detail(qid)
    sql = cat_servis.kaydeden.son_sorgu()

    assert "question_id" not in _sadelestir(
        sql
    ), "Split cocuk tablolarinda `question_id` kolonu YOK; JOIN `id` uzerinden olmali"

    for tablo in COCUK_TABLOLAR:
        kosul = _join_kosulu(sql, tablo)
        assert kosul is not None, f"{tablo} icin JOIN ... ON kosulu bulunamadi"
        sol, sag = kosul
        assert (
            sol.split(".")[-1] == "id" and sag.split(".")[-1] == "id"
        ), f"{tablo} JOIN kosulu `id = id` degil: {sol} = {sag}"


# ---------------------------------------------------------------------------
# 3) SESSIZ kusur — app/api/cat.py:485-503 (_check_answer)
# ---------------------------------------------------------------------------


@_bos_kapi_xfail
async def test_check_answer_dogru_sikki_dogru_biliyor(live_db: AsyncSession):
    """`_check_answer` DOGRU siki dogru bilmeli.

    Bu kusur SESSIZ: `except Exception` UndefinedColumn'u yutuyor ve False
    donuyor -> her CAT yaniti YANLIS sayiliyor, hicbir 500 gorunmuyor. Bu
    yuzden burada HTTP durumu degil, fonksiyonun DONDURDUGU DEGER olculur;
    "200 dondu" assert'i fix'ten once de gecerdi (vakum test).

    Ikinci assert (yanlis sik -> False) tek basina vakumdur; birinciyle ayni
    testte durmasi kasitli — testin RED'ligini birinci assert tasir.
    """
    from app.api.cat import _check_answer

    qid, dogru_sik = await _ornek_soru(live_db)

    assert await _check_answer(live_db, qid, dogru_sik) is True, (
        f"{qid} icin dogru sik {dogru_sik!r} verildi ama _check_answer False dondu "
        "(sessiz yutulan UndefinedColumn)"
    )

    yanlis_sik = next(h for h in "ABCDE" if h != dogru_sik.upper())
    assert await _check_answer(live_db, qid, yanlis_sik) is False


# ---------------------------------------------------------------------------
# 4) Uc nokta — POST /api/v1/cat/next (auth GEREKTIRMEZ)
# ---------------------------------------------------------------------------


@_bos_kapi_xfail
async def test_cat_next_ucu_500_donmuyor(cat_client: AsyncClient):
    """Canli repro: `curl -X POST .../api/v1/cat/next` -> HTTP 500."""
    yanit = await cat_client.post("/api/v1/cat/next", json={})
    assert yanit.status_code == 200, f"HTTP {yanit.status_code}: {yanit.text[:400]}"


@_bos_kapi_xfail
async def test_cat_next_gercek_madde_ve_sik_donduruyor(cat_client: AsyncClient):
    """200 yetmez — sozlesmedeki madde gercek soru metni ve siklarla dolmali."""
    yanit = await cat_client.post("/api/v1/cat/next", json={})
    assert yanit.status_code == 200, f"HTTP {yanit.status_code}: {yanit.text[:400]}"

    govde = yanit.json()
    madde = govde["item"]
    assert isinstance(madde["soru"], str) and madde["soru"].strip()
    assert (
        len(madde["secenekler"]) >= 4
    ), f"Sik sayisi {len(madde['secenekler'])} — en az 4 (A-D) beklenir"
    assert all(str(s).strip() for s in madde["secenekler"]), "Bos sik sunuldu"
    assert govde["done"] is False
    assert govde["madde"] == 0
    for alan in ("theta", "se"):
        assert isinstance(govde[alan], int | float), f"{alan} sayi degil"
