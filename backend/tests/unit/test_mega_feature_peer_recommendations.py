"""`_build_peer_recommendations` #485 split gocu bekcisi (S255).

NEDEN VAR
---------
`tasks/mega_feature_tasks.py:371/393` `QuestionBankItem.subject_area`i SINIF
duzeyinde okuyordu. O alan #485'te `question_metadata`ya tasindi ve uyumluluk
katmani sinif duzeyinde BILEREK yol gosteren bir `AttributeError` atiyor --
yani sorgu KURULAMIYOR, calisma anina bile gelmiyor.

CANLILIK OLCULDU (27 Agu 2026), ve bu kalem digerlerinden AYRILDI:

    repositories/question_repository.py     16 erisim -> OLU (0 importer)
    analytics/exam_results_reporting.py      4 erisim -> OLU (0 importer)
    core/irt_daemon.py                       8 kalem  -> OLU (start() yorum satiri)
    services/irt_analysis_service.py         5 kalem  -> OLU (0 cagiran)
    services/difficulty_classification.py    2 erisim -> KASITLI 503 shim
    application/commands/learning_path.py    5 erisim -> ULASILAMIYOR (ustte GF10)
    tasks/mega_feature_tasks.py              2 erisim -> **GIZLI CANLI**

Sonuncusu `run_weekly_error_clustering` icinden cagriliyor; task
`core/celery_app.py:188`de beat'e **Pazar 23:00**e zamanli ve
`kiro2-celery-worker` ayakta. Yani kusur bir uc probunda GORUNMEZ, ama
duzeltilmeseydi sonraki haftalik kosumda SESSIZCE patlayacakti (celery task
hatasi kimsenin bakmadigi bir gunluk satiri olarak kalirdi).

NEDEN SAHTE DB
--------------
Kusur sorgunun KURULMASINDA. Gercek bir oturum gerekmez; gereken tek sey
akisin ucuncu sorguya ULASMASI. Fikstur bunu saglar ve `alet dogrulamasi`
assert'i ulasildigini olcer -- yoksa test bos kumede sessizce gecerdi
(ilk sorgu bos donerse fonksiyon `continue` ile o sorguyu hic kurmaz).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from tasks.mega_feature_tasks import _build_peer_recommendations

pytestmark = [pytest.mark.unit]


class _SahteSonuc:
    def __init__(self, satirlar: list[Any]) -> None:
        self._satirlar = satirlar

    def scalars(self) -> _SahteSonuc:
        return self

    def all(self) -> list[Any]:
        return self._satirlar


class _SahteDB:
    """`execute` cagrilarini SIRAYLA yanitlar ve IFADELERI saklar."""

    def __init__(self, sonuclar: list[_SahteSonuc]) -> None:
        self._sonuclar = list(sonuclar)
        self.ifadeler: list[Any] = []

    async def execute(self, stmt: Any, *_a: Any, **_k: Any) -> _SahteSonuc:
        self.ifadeler.append(stmt)
        return self._sonuclar.pop(0) if self._sonuclar else _SahteSonuc([])

    # Yazma yolu bu testin konusu DEGIL; fonksiyonun akmasi icin no-op.
    def add(self, _obj: Any) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None


def _db_kur() -> _SahteDB:
    kume = SimpleNamespace(error_pattern="careless:MATEMATIK", student_count=3)
    return _SahteDB(
        [
            _SahteSonuc([kume]),  # 1) kumeler
            _SahteSonuc([("s1",), ("s2",), ("s3",)]),  # 2) ogrenciler (>=3 SART)
            _SahteSonuc([]),  # 3) iyilesme sorgusu -- KUSUR BURADA
        ]
    )


async def test_iyilesme_sorgusu_kurulabiliyor() -> None:
    """SINIF duzeyi erisim kalsaydi burada `AttributeError` atardi.

    MUTASYON: `QuestionMetadata.subject_area` tekrar
    `QuestionBankItem.subject_area` yapilirsa bu test DUSER.
    """
    db = _db_kur()

    sonuc = await _build_peer_recommendations(db=db, subject="matematik")

    assert sonuc == 0, f"bos iyilesme kumesinde 0 beklenir: {sonuc}"
    # ALET DOGRULAMASI: ucuncu sorguya GERCEKTEN ulasildi mi? Ilk iki fikstur
    # zayif olsaydi fonksiyon `continue` eder, kusurlu sorgu HIC kurulmaz ve
    # test yanlis sebeple yesil kalirdi.
    assert len(db.ifadeler) >= 3, (
        "iyilesme sorgusuna ulasilmadi -- fikstur akisi kisa devre yaptirdi, "
        f"kurulan sorgu sayisi: {len(db.ifadeler)}"
    )


async def test_iyilesme_sorgusu_yavru_tabloyu_okuyor() -> None:
    """`subject_area` question_metadata'dan gelmeli, question_bank'tan degil."""
    db = _db_kur()
    await _build_peer_recommendations(db=db, subject="matematik")

    sql = str(
        db.ifadeler[2].compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert (
        "question_metadata.subject_area" in sql
    ), f"`subject_area` yavru tablodan okunmuyor. Kurulan SQL: {sql[:400]}"
    assert (
        "question_bank.subject_area" not in sql
    ), "question_bank uzerinden subject_area okunuyor -- o kolon orada YOK"


async def test_eklenen_join_kartezyen_uretmiyor() -> None:
    """Yavru tabloya JOIN eklemek FROM sayisini artirmamali.

    audit-methodology: kartezyeni metinsel virgulle degil
    `stmt.get_final_froms()` ile say.
    """
    db = _db_kur()
    await _build_peer_recommendations(db=db, subject="matematik")

    fromlar = db.ifadeler[2].get_final_froms()
    assert (
        len(fromlar) == 1
    ), f"kartezyen: {len(fromlar)} ayri FROM var -> {[str(f)[:60] for f in fromlar]}"
