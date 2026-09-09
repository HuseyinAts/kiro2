"""osym_inspired_generator ham SQL'i gercek semaya uyuyor mu (9 Eyl 2026).

NEDEN VAR
---------
Golden Flows kapisi genisletilince (#224) `test_osym_examples_still_works_for_staff`
500 verdi. Sebep: `services/osym_inspired_generator.py` bes ham asyncpg
sorgusunda `question_bank`'tan `question_text`, `subject_area`, `exam_type`,
`osym_format_compliant`, `correct_answer`, `osym_year` okuyordu. S210 split'i
bu kolonlari `question_content` / `question_metadata`'ya tasidi; CI postgres
log'unda `column "question_text" does not exist` goruldu.

Bunu hicbir mevcut bekci yakalamadi: `scripts/scan_split_accesses.py` ORM
attribute erisimini sayar, `scripts/audit_dual_table_trap.py` eski `questions`
modeli import'unu arar. Ham SQL string'i ikisinin de gorus alani disinda.

NE YAPAR
--------
Uc generator metodunu GERCEK Postgres'e karsi calistirir. Satir sayisi
onemsiz -- bos tabloda bile calisir; kanit, sorgunun `UndefinedColumnError`
atmadan donmesi. Eski kodda (tek-tablo sorgu) uc test de asyncpg
`UndefinedColumnError` ile duser (mutasyonla dogrulandi: sorgudan JOIN'ler
silinince 3/3 FAILED).

DB yoksa skip (tests/e2e/pg_dsn.py sozlesmesi).
"""

from __future__ import annotations

import re

import asyncpg
import pytest

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [pytest.mark.db_invariant, pytest.mark.asyncio]


def _asyncpg_dsn() -> str:
    # Acik tip: CI mypy repo kokunden kosuyor, `tests.e2e.pg_dsn` orada
    # cozulmeyince donus Any oluyor ve no-any-return dusuyordu.
    dsn: str | None = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)
    # asyncpg surucu eki kabul etmez. CI'da DATABASE_URL_SYNC
    # `postgresql+psycopg://` (olculdu: job 102472156026, "invalid DSN: scheme");
    # yalnizca `+asyncpg`i soymak yetmiyordu -- her `+surucu` eki soyulur.
    return re.sub(r"^postgresql\+\w+://", "postgresql://", dsn)


@pytest.fixture
def uretici():
    """Generator; DB baglantisi test DSN'ine yonlendirilmis (alt sinif, monkeypatch degil)."""
    from services.osym_inspired_generator import OSYMInspiredGenerator

    dsn = _asyncpg_dsn()

    class _TestUretici(OSYMInspiredGenerator):
        async def get_db_connection(self):
            return await asyncpg.connect(dsn)

    return _TestUretici()


async def test_ornek_sorgusu_bolunmus_semada_calisir(uretici) -> None:
    sorular = await uretici.get_similar_osym_questions(
        "MATEMATIK", "TYT", count=2, use_reranking=False
    )
    assert isinstance(sorular, list)
    for s in sorular:
        assert {
            "question_id",
            "subject",
            "stem",
            "options",
            "correct_answer",
            "year",
        } <= set(s)
        assert s["subject"] == "MATEMATIK"


async def test_stil_analizi_bolunmus_semada_calisir(uretici) -> None:
    stil = await uretici.analyze_osym_style("MATEMATIK", "TYT")
    assert stil["data_source"] in {"database", "research_fallback"}
    assert stil["total_analyzed"] >= 0


async def test_istatistik_bolunmus_semada_calisir(uretici) -> None:
    ist = await uretici.get_osym_statistics()
    assert ist["total_osym_questions"] >= ist["usable_for_training"] >= 0
    assert isinstance(ist["by_subject"], dict)
