"""GF-K1: dusen 7 tablonun sema sozlesmesi.

NEDEN VAR (1 Agu 2026 olcumu)
------------------------------
Canli Golden Flow kosumu 12 kirik akis gosterdi; baskin sebep `UndefinedTable`
(logda 74 kez). `c555a10f4b93_sync_db_changes.py` `upgrade()` icindeki 145
`op.execute('DROP TABLE IF EXISTS ... CASCADE')` bu tablolari dusurmustu.

GECISLI KAPANIS: hedef 6 tabloydu, ama `appointments` -> `teacher_availability`
FK'si var ve O DA yok. Yani olusturulmasi gereken **7** tablo:

    reasoning_cache        (FK yok)
    video_watch_sessions   -> users
    emotional_states       -> users
    teacher_availability   -> teacher_pool_profiles
    video_notes            -> users, video_watch_sessions
    live_sessions          -> users, teacher_profiles
    appointments           -> users, teacher_pool_profiles, teacher_availability

VARLIK YETMEZ, SEMA DA TUTMALI
-------------------------------
Tablo var ama kolon eksikse uc yine 500 verir — "tablo geldi, is bitti" yanilgisi
bu depoda yasandi (`GF106 StudentReview`, ~18 eksik kolon). Bu yuzden asagida
her tablonun ORM modelindeki HER kolonu canli semada aranir.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

pytestmark = [pytest.mark.integration]

DSN = "postgresql+psycopg://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

MODEL_MODULLERI = [
    "models.video_analytics",
    "models.diary",
    "models.teacher_pool",
    "models.live_session",
    "models.reasoning_models",
]

# Bagimlilik sirasi (migration'lar da bu sirayi kullanir)
# GF-K1 dalgasi — gfk1_restore_20260801
BEKLENEN_TABLOLAR = [
    "reasoning_cache",
    "video_watch_sessions",
    "emotional_states",
    "teacher_availability",
    "video_notes",
    "live_sessions",
    "appointments",
    # GF-K2 dalgasi — gfk2_diary_20260801. KACAN KARDES: ayni sinif, ilk turda
    # gorunmedi cunku istek once `emotional_states` yoklugunda patliyordu.
    "diary_entries",
    "diary_exports",
    "goals",
    "learning_entries",
    "peer_comparisons",
    "insights",
    "reflections",
]


def _model_tablolari() -> dict[str, sa.Table]:
    for m in MODEL_MODULLERI:
        importlib.import_module(m)
    bulunan: dict[str, sa.Table] = {}
    for mod in list(sys.modules.values()):
        if not hasattr(mod, "__dict__"):
            continue
        for ad in dir(mod):
            # Tum yuklu modullerde geziniyoruz; bazilari `__getattr__` icinde
            # lazy import yapip patlar (opsiyonel bagimlilik yok). Bu tarama
            # icin ilgisiz; loglamak yuzlerce satir gurultu uretir.
            try:
                nesne = getattr(mod, ad)
                tablo = getattr(nesne, "__table__", None)
            except Exception:  # noqa: S112
                continue
            if isinstance(tablo, sa.Table):
                bulunan.setdefault(tablo.name, tablo)
    return bulunan


@pytest.fixture(scope="module")
def canli_sema() -> dict[str, set[str]]:
    """Canli public semadaki tablo -> kolon adlari."""
    motor = sa.create_engine(DSN)
    try:
        with motor.connect() as baglanti:
            satirlar = baglanti.execute(
                sa.text(
                    "SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public'"
                )
            ).fetchall()
    except Exception as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    finally:
        motor.dispose()

    sema: dict[str, set[str]] = {}
    for tablo, kolon in satirlar:
        sema.setdefault(tablo, set()).add(kolon)
    return sema


def test_alet_dogrulamasi_bilinen_tablo_gorunuyor(
    canli_sema: dict[str, set[str]],
) -> None:
    """KONTROL KOLU: sorgu gercekten semayi okuyor mu."""
    assert "users" in canli_sema, (
        "Bilinen-VAR tablo `users` gorunmuyor -> olcum aleti arizali, "
        "asagidaki 'tablo yok' sonuclari ANLAMSIZ"
    )
    assert (
        "zzz_olmayan_tablo" not in canli_sema
    ), "Bilinen-YOK tablo gorunuyor -> sorgu yanlis kumeyi donduruyor"


def test_dusen_tablolar_canliya_geri_geldi(canli_sema: dict[str, set[str]]) -> None:
    """GF-K1: 7 tablonun tamami canli semada olmali."""
    eksik = [t for t in BEKLENEN_TABLOLAR if t not in canli_sema]
    assert not eksik, (
        f"{len(eksik)}/7 tablo hala YOK: {eksik}. "
        "c555a10f4b93 bunlari DROP etmisti; restore migration'i kosuldu mu?"
    )


@pytest.mark.parametrize("tablo_adi", BEKLENEN_TABLOLAR)
def test_tablo_kolonlari_orm_modeliyle_ortusuyor(
    tablo_adi: str, canli_sema: dict[str, set[str]]
) -> None:
    """Varlik YETMEZ: modelin her kolonu canli tabloda da olmali.

    `GF106 StudentReview` vakasi: tablo vardi, ~18 kolon eksikti ve uc yine
    500 veriyordu.
    """
    if tablo_adi not in canli_sema:
        pytest.fail(f"{tablo_adi} tablosu YOK — once varlik testine bak")
    model = _model_tablolari().get(tablo_adi)
    assert (
        model is not None
    ), f"{tablo_adi} icin ORM modeli bulunamadi (DDL kaynagi yok)"
    eksik = sorted({k.name for k in model.columns} - canli_sema[tablo_adi])
    assert not eksik, (
        f"{tablo_adi}: modelde olup canli tabloda OLMAYAN kolonlar: {eksik} "
        "-> uc 500 vermeye devam eder"
    )
