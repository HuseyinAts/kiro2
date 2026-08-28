"""TDD RED kaniti + regresyon bekcisi — #485 Track C-sinav.

`application/commands/sinav.py` icindeki `SaveAnswerCommandHandler`, 69-alan
split'inden (S210, 0fd9b8413) ONCEKI semayi varsayan **sinif duzeyi** erisimler
kullaniyor::

    select(Question.correct_answer, Question.subject_area,
           Question.irt_discrimination, Question.irt_difficulty,
           Question.irt_guessing)

Bu alanlar artik `question_content` / `question_metadata` /
`question_statistics` tablolarinda. `models/question_bank.py:545-587`'deki
strangler devredicisi sinif duzeyi erisimde KASITLI `AttributeError` firlatiyor
(olculdu) -> sorgu HIC KURULAMIYOR.

### BU KUSUR SESSIZDIR — bu yuzden HTTP durum testi VAKUM olurdu ###

Dort sorgu yerinin dordu de `except Exception` ile sarili (`:421` ve `:564`).
AttributeError yutuluyor, loga "BKT pipeline FAILED ... degraded mode" duruyor
ve uc **200** donuyor. Yani `assert status_code == 200` fix'ten ONCE de gecer.

Bu yuzden buradaki iddialar kusurun FIILEN tezahur ettigi katmanda:
  * `BKTService.record_answer` CAGRILDI MI (bugun cagrilmiyor),
  * cagrildiysa `topic_id` / `subject_slug` / IRT parametreleri GERCEK
    Postgres'ten, dogru cocuk tablodan mi geldi (varsayilana dusmedi mi),
  * tek bir SQL ifadesi `question_bank`'i uc cocuk tabloya JOIN'liyor mu.

### Ayirt edicilik (S223 dersi: mutasyonun kacmadigini ONCEDEN garanti et) ###

Uretimdeki varsayilanlar `or 1.0 / 0.0 / 0.2` ve `or "matematik"` degerleri
"JOIN calismasa da makul gorunen" sonuc uretebilir. O yuzden fixture, canli
DB'den yalnizca **varsayilandan FARKLI** degerlere sahip bir soru secer
(`irt_guessing <> 0.2`, `subject_area <> 'matematik'`) ve bunu assert eder.
Aksi halde iddialar sessizce ayirt edici olmaktan cikardi.

### Neden gercek Postgres (mock DB DEGIL) ###

`core/database.py:279-288` — `TESTING=true` iken `db_manager` oturum yapicisi
yoksa **AsyncMock** doner. Mock'lu bir oturumda `select(...)` zaten hic
kurulmadigi icin bu kusur yapisal olarak GORULEMEZ (S228'in olctugu tuzagin
birebir ayni sinifi). Bu dosya `live_db` fixture'ini kullanir; DSN kaynak koda
GOMULMEZ, `tests/integration/conftest.py::canli_dsn_cozumle` ile ortamdan
cozulur ve postgres olmayan DSN reddedilir.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

pytestmark = pytest.mark.asyncio

# Uretim kodundaki varsayilanlar (application/commands/sinav.py:399-405, 546-548).
# Fixture bu degerlerden FARKLI veri secmek zorunda, yoksa iddia ayirt edici olmaz.
VARSAYILAN_IRT_A = 1.0
VARSAYILAN_IRT_B = 0.0
VARSAYILAN_IRT_C = 0.2
VARSAYILAN_SUBJECT_SLUG = "matematik"


# ---------------------------------------------------------------------------
# Yardimci veri yapilari
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SoruKaydi:
    """Canli DB'den okunan gercek bir soru — beklenen degerlerin kaynagi."""

    id: str
    correct_answer: str
    subject_area: str
    primary_topic_id: str
    irt_discrimination: float
    irt_difficulty: float
    irt_guessing: float


class _SahteSinavMotoru:
    """Sinav OTURUM deposunun (Redis/bellek) yerine gecer — VERITABANI DEGIL.

    `osym_exam_engine` sinav oturumunu DB'de degil oturum deposunda tutar; bu
    testin olctugu sey oturum depolamasi degil, `question_bank` split'i sonrasi
    SORGU katmanidir. DB yolu sonuna kadar gercek Postgres'e baglidir.
    """

    def __init__(self, student_id: str) -> None:
        self._student_id = student_id
        self.save_answer_cagrildi = False

    async def get_session_data(self, session_id: str) -> Any:
        class _Oturum:
            student_id = self._student_id

        return _Oturum()

    async def save_answer(self, **_kwargs: Any) -> bool:
        self.save_answer_cagrildi = True
        return True


class _CommitsizOturum:
    """`live_db`'yi uretim koduna verir, `commit()`'i `flush()`'a cevirir.

    Gercek Postgres baglantisi/gercek SQL — yalnizca islem siniri bastirilir.
    Aksi halde uretimin `await db.commit()` cagrisi (sinav.py:420, 563)
    fixture'in ROLLBACK'ini gecersiz kilar ve test verisi canli DB'de kalir.
    """

    def __init__(self, oturum: AsyncSession) -> None:
        self._oturum = oturum

    def __getattr__(self, ad: str) -> Any:
        return getattr(self._oturum, ad)

    async def commit(self) -> None:
        await self._oturum.flush()


class BktKancasi:
    """Test kosumunun gozlem yuzeyi: BKT cagrilari + calisan ham SQL."""

    def __init__(self) -> None:
        self.cagrilar: list[dict[str, Any]] = []
        self.ifadeler: list[str] = []
        self._imlec = 0

    @property
    def uretim_ifadeleri(self) -> list[str]:
        """YALNIZ handler cagrisi sirasinda calisan SQL.

        OLCUM ALETI ARIZASI (yakalandi): tum `ifadeler`e bakan ilk surum
        fix'ten ONCE de geciyordu — cunku `ornek_soru` fixture'inin KENDI
        sorgusu da dort tabloyu JOIN'liyor ve iddiayi karsiliyordu. Imlec
        `calistir()` icinde sifirlanir, boylece yalniz uretimin urettigi
        ifadeler olculur.
        """
        return self.ifadeler[self._imlec :]

    @property
    def son_cagri(self) -> dict[str, Any]:
        assert self.cagrilar, (
            "BKTService.record_answer HIC CAGRILMADI. Bugunku sebep: "
            "select(Question.correct_answer, ...) sinif duzeyi erisimi "
            "AttributeError firlatiyor (models/question_bank.py:545-587), "
            "hata sinav.py:421/:564'teki `except Exception` tarafindan "
            "yutuluyor ve uc sessizce 200 donuyor."
        )
        return self.cagrilar[-1]

    async def calistir(self, komut: Any) -> dict[str, Any]:
        """Handler'i cagirir ve fire-and-forget arka plan gorevini BEKLER."""
        from application.commands.sinav import SaveAnswerCommandHandler

        self._imlec = len(self.ifadeler)
        onceki = asyncio.all_tasks()
        sonuc = await SaveAnswerCommandHandler().handle(komut)
        yeni = [
            t
            for t in asyncio.all_tasks()
            if t not in onceki and t is not asyncio.current_task()
        ]
        if yeni:
            await asyncio.wait(yeni, timeout=30)
        return sonuc


# ---------------------------------------------------------------------------
# Fixture'lar
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ornek_soru(live_db: AsyncSession) -> SoruKaydi:
    """Canli DB'den, uretim varsayilanlarindan AYIRT EDILEBILIR bir soru sec."""
    satir = (
        await live_db.execute(
            text(
                """
                SELECT qb.id, qc.correct_answer, qm.subject_area,
                       qb.primary_topic_id, qs.irt_discrimination,
                       qs.irt_difficulty, qs.irt_guessing
                FROM question_bank qb
                JOIN question_content qc     ON qc.id = qb.id
                JOIN question_metadata qm    ON qm.id = qb.id
                JOIN question_statistics qs  ON qs.id = qb.id
                WHERE qb.is_active = TRUE
                  AND qb.primary_topic_id IS NOT NULL
                  AND qc.correct_answer IN ('A','B','C','D','E')
                  AND qm.subject_area IS NOT NULL
                  AND lower(qm.subject_area) <> :varsayilan_slug
                  AND qs.irt_guessing IS NOT NULL
                  AND qs.irt_guessing <> :varsayilan_c
                ORDER BY qb.id
                LIMIT 1
                """
            ),
            {
                "varsayilan_slug": VARSAYILAN_SUBJECT_SLUG,
                "varsayilan_c": VARSAYILAN_IRT_C,
            },
        )
    ).first()

    if satir is None:
        pytest.skip(
            "Ayirt edici soru bulunamadi (irt_guessing<>0.2 ve "
            "subject_area<>'matematik' olan aktif soru yok) — iddialar "
            "uretim varsayilanlarindan ayirt edilemezdi"
        )

    soru = SoruKaydi(
        id=str(satir.id),
        correct_answer=str(satir.correct_answer),
        subject_area=str(satir.subject_area),
        primary_topic_id=str(satir.primary_topic_id),
        irt_discrimination=float(satir.irt_discrimination),
        irt_difficulty=float(satir.irt_difficulty),
        irt_guessing=float(satir.irt_guessing),
    )
    # AYIRT EDICILIK GARANTISI — bu assert dusuyorsa testler degersizlesir.
    assert soru.irt_guessing != VARSAYILAN_IRT_C
    assert soru.subject_area.lower() != VARSAYILAN_SUBJECT_SLUG
    return soru


@pytest_asyncio.fixture
async def bkt_kancasi(
    live_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[BktKancasi, None]:
    """Uretimin DB yolunu `live_db`'ye baglar, BKT cagrilarini ve SQL'i yakalar."""
    from services.bkt_service import BKTService

    kanca = BktKancasi()

    async def _yakala(**kwargs: Any) -> dict[str, Any]:
        kanca.cagrilar.append(kwargs)
        return {"new_p_L": 0.5, "theta_after": 0.0}

    monkeypatch.setattr(BKTService, "record_answer", staticmethod(_yakala))

    @asynccontextmanager
    async def _canli_oturum() -> AsyncGenerator[Any, None]:
        yield _CommitsizOturum(live_db)

    monkeypatch.setattr("core.database.get_db_session_context", _canli_oturum)
    monkeypatch.setattr(
        "application.commands.sinav._get_engine",
        lambda: _SahteSinavMotoru(student_id="ogrenci-s229"),
    )

    def _sql_kaydet(_conn, _cursor, statement, _params, _ctx, _many):
        kanca.ifadeler.append(statement)

    event.listen(Engine, "before_cursor_execute", _sql_kaydet)
    try:
        yield kanca
    finally:
        event.remove(Engine, "before_cursor_execute", _sql_kaydet)


@pytest_asyncio.fixture
async def onceki_cevaplar(
    live_db: AsyncSession, ornek_soru: SoruKaydi
) -> tuple[str, list[str]]:
    """Ayni oturumda 2 onceki cevap yaratir (IRT gecmis sorgusunu tetiklemek icin).

    `student_answers` ve `exam_sessions` canli DB'de BOS oldugu icin
    (olculdu: 0/0) bu satirlar yaratilmadan IRT gecmis sorgusu HIC kurulmaz.
    Butun yazmalar `live_db` islemi icinde, test sonunda ROLLBACK edilir.
    """
    onceki_ids = [
        str(r[0])
        for r in await live_db.execute(
            text(
                """
                SELECT qb.id FROM question_bank qb
                JOIN question_statistics qs ON qs.id = qb.id
                WHERE qb.id <> :hedef AND qs.irt_guessing = :beklenen
                ORDER BY qb.id LIMIT 2
                """
            ),
            {"hedef": ornek_soru.id, "beklenen": ornek_soru.irt_guessing},
        )
    ]
    assert len(onceki_ids) == 2, "IRT gecmisi icin 2 ek soru gerekiyor"

    ogrenci_id = (
        await live_db.execute(text("SELECT id FROM student_profiles LIMIT 1"))
    ).scalar()
    if ogrenci_id is None:
        pytest.skip("student_profiles bos — exam_sessions FK'si karsilanamiyor")

    oturum_id = f"test-s229-{uuid.uuid4().hex[:12]}"
    await live_db.execute(
        text(
            """
            INSERT INTO exam_sessions (
                id, organization_id, student_id, exam_type, exam_name,
                total_questions, duration_minutes, status, current_question_index,
                time_spent_seconds, total_correct, total_wrong, total_empty,
                raw_score, estimated_ability, ability_confidence)
            VALUES (:id, 'org_legacy_default', :ogrenci, CAST('TYT' AS examtype),
                    'S229 split gocu testi', 3, 120, 'in_progress', 0, 0, 0, 0, 0,
                    0.0, 0.0, 0.0)
            """
        ),
        {"id": oturum_id, "ogrenci": ogrenci_id},
    )
    for sira, (soru_id, dogru_mu) in enumerate(
        zip(onceki_ids, [True, False], strict=False)
    ):
        await live_db.execute(
            text(
                """
                INSERT INTO student_answers (
                    id, exam_session_id, question_id, selected_answer, is_correct,
                    response_time_seconds, answer_changes, time_to_first_answer)
                VALUES (:id, :oturum, :soru, 'A', :dogru, 12.0, 0, 4.0)
                """
            ),
            {
                "id": f"{oturum_id}-a{sira}",
                "oturum": oturum_id,
                "soru": soru_id,
                "dogru": dogru_mu,
            },
        )
    await live_db.flush()
    return oturum_id, onceki_ids


def _komut(soru: SoruKaydi, oturum_id: str) -> Any:
    from application.commands.sinav import SaveAnswerCommand

    return SaveAnswerCommand(
        student_id="ogrenci-s229",
        session_id=oturum_id,
        question_id=soru.id,
        selected_answer=soru.correct_answer,
        response_time=12.0,
    )


def _irt_dogrula(kayit: dict[str, Any], soru: SoruKaydi) -> None:
    """IRT ucluleri `question_statistics`'ten mi geldi, varsayilandan mi?"""
    assert kayit["irt_c"] == pytest.approx(soru.irt_guessing), (
        f"irt_c={kayit['irt_c']} — DB'deki question_statistics.irt_guessing "
        f"({soru.irt_guessing}) yerine uretim varsayilanina "
        f"({VARSAYILAN_IRT_C}) dusulmus: JOIN question_statistics'e ulasmiyor"
    )
    assert kayit["irt_a"] == pytest.approx(soru.irt_discrimination)
    assert kayit["irt_b"] == pytest.approx(soru.irt_difficulty)


# ---------------------------------------------------------------------------
# 1) Fire-and-forget dali (VARSAYILAN akis) — ana sorgu, sinav.py:312-321
# ---------------------------------------------------------------------------


async def test_fire_and_forget_ana_sorgu_split_tablolardan_okumali(
    bkt_kancasi: BktKancasi,
    ornek_soru: SoruKaydi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALGO_FIRE_AND_FORGET", "yes")

    sonuc = await bkt_kancasi.calistir(_komut(ornek_soru, "oturum-ff-1"))
    assert (
        sonuc["success"] is True
    )  # uc sessizce basarili doner — kusur burada GORUNMEZ

    kayit = bkt_kancasi.son_cagri
    assert kayit["topic_id"] == ornek_soru.primary_topic_id
    assert kayit["subject_slug"] == ornek_soru.subject_area.lower(), (
        "subject_slug question_metadata.subject_area'dan gelmeli; "
        f"'{VARSAYILAN_SUBJECT_SLUG}' varsayilani JOIN'in calismadigini gosterir"
    )
    assert kayit["correct"] is True, (
        "correct question_content.correct_answer ile karsilastirilmali; "
        "False, correct_answer'in None geldigini gosterir"
    )
    assert kayit["rating"] == 3
    _irt_dogrula(kayit["answered_questions"][-1], ornek_soru)


# ---------------------------------------------------------------------------
# 2) Senkron dal — ana sorgu, sinav.py:473-482
# ---------------------------------------------------------------------------


async def test_senkron_dal_ana_sorgu_split_tablolardan_okumali(
    bkt_kancasi: BktKancasi,
    ornek_soru: SoruKaydi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALGO_FIRE_AND_FORGET", "no")

    sonuc = await bkt_kancasi.calistir(_komut(ornek_soru, "oturum-senk-1"))

    assert sonuc["algorithm"] is not None, (
        "senkron dalda BKT sonucu None — sorgu kurulamadi ve "
        "sinav.py:564'teki `except Exception` hatayi yuttu"
    )
    assert sonuc["algorithm_degraded"] is False

    kayit = bkt_kancasi.son_cagri
    assert kayit["topic_id"] == ornek_soru.primary_topic_id
    assert kayit["subject_slug"] == ornek_soru.subject_area.lower()
    assert kayit["correct"] is True
    _irt_dogrula(kayit["answered_questions"][-1], ornek_soru)


# ---------------------------------------------------------------------------
# 3) Yapisal: TEK ifade, question_bank + uc cocuk tablo
# ---------------------------------------------------------------------------


async def test_ana_sorgu_tek_ifadede_uc_cocuk_tabloyu_joinlemeli(
    bkt_kancasi: BktKancasi,
    ornek_soru: SoruKaydi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """N+1 yerine tek JOIN'li ifade (onerilen kalip: outerjoin x3, FK `id` uzerinden)."""
    monkeypatch.setenv("ALGO_FIRE_AND_FORGET", "no")

    await bkt_kancasi.calistir(_komut(ornek_soru, "oturum-sql-1"))

    uretim = bkt_kancasi.uretim_ifadeleri
    joinli = [
        s
        for s in uretim
        if "question_bank" in s
        and "question_content" in s
        and "question_metadata" in s
        and "question_statistics" in s
    ]
    assert joinli, (
        "Handler question_bank'i uc cocuk tabloya JOIN'leyen TEK bir SELECT "
        f"calistirmadi. Uretimin calistirdigi ifadeler: {[s[:110] for s in uretim]}"
    )


# ---------------------------------------------------------------------------
# 4) IRT gecmis sorgusu — senkron dal, sinav.py:513-520
# ---------------------------------------------------------------------------


async def test_senkron_dal_irt_gecmisi_onceki_cevaplari_getirmeli(
    bkt_kancasi: BktKancasi,
    ornek_soru: SoruKaydi,
    onceki_cevaplar: tuple[str, list[str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALGO_FIRE_AND_FORGET", "no")
    oturum_id, _ = onceki_cevaplar

    await bkt_kancasi.calistir(_komut(ornek_soru, oturum_id))

    kayit = bkt_kancasi.son_cagri
    assert len(kayit["answered_questions"]) == 3, (
        "2 onceki cevap + 1 guncel = 3 bekleniyor; "
        f"{len(kayit['answered_questions'])} geldi — IRT gecmis sorgusu "
        "(sinav.py:513-520) `except Exception as irt_err` tarafindan yutuldu"
    )
    assert len(kayit["responses"]) == 3
    assert kayit["responses"][-1] is True
    assert sorted(kayit["responses"][:2]) == [False, True]
    for giris in kayit["answered_questions"]:
        _irt_dogrula(giris, ornek_soru)


# ---------------------------------------------------------------------------
# 5) IRT gecmis sorgusu — fire-and-forget dal, sinav.py:360-367
# ---------------------------------------------------------------------------


async def test_fire_and_forget_irt_gecmisi_onceki_cevaplari_getirmeli(
    bkt_kancasi: BktKancasi,
    ornek_soru: SoruKaydi,
    onceki_cevaplar: tuple[str, list[str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALGO_FIRE_AND_FORGET", "yes")
    oturum_id, _ = onceki_cevaplar

    await bkt_kancasi.calistir(_komut(ornek_soru, oturum_id))

    kayit = bkt_kancasi.son_cagri
    assert len(kayit["answered_questions"]) == 3, (
        "2 onceki cevap + 1 guncel = 3 bekleniyor; "
        f"{len(kayit['answered_questions'])} geldi — IRT gecmis sorgusu "
        "(sinav.py:360-367) `except Exception as irt_err` tarafindan yutuldu"
    )
    assert len(kayit["responses"]) == 3
    assert kayit["responses"][-1] is True
    assert sorted(kayit["responses"][:2]) == [False, True]
    for giris in kayit["answered_questions"]:
        _irt_dogrula(giris, ornek_soru)
