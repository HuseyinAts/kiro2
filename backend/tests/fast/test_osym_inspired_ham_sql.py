"""osym_inspired_generator ham SQL'i bolunmus kolonlari dogru tablodan okuyor mu.

DB'siz, statik kardes: tests/db/test_osym_inspired_sql_sema_uyumu.py gercek
Postgres ister ve CI'da DB olmayan adimlarda skip olur. Bu bekci kaynak
dosyayi AST ile okur, `question_bank` gecen her string sabitinde S210 split'i
ile tasinan kolonlarin sahibi tabloya JOIN oldugunu dogrular.

Kolon sahipleri 9 Eyl 2026'da information_schema'dan olculdu:
  question_content : question_text, option_a..e, correct_answer, explanation
  question_metadata: subject_area, exam_type, osym_format_compliant, osym_year
  question_bank    : is_active (parent'ta kaldi)

Mutasyon: eski tek-tablo sorgu geri konunca FAILED (5 sorgu / 3 metod).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_KAYNAK = (
    Path(__file__).resolve().parents[2] / "services" / "osym_inspired_generator.py"
)

_ICERIK_KOLONLARI = (
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "correct_answer",
    "explanation",
)
_GECERLI_ONEKLER = ("c.", "m.")
_METAVERI_KOLONLARI = (
    "subject_area",
    "exam_type",
    "osym_format_compliant",
    "osym_year",
)


def _sql_sabitleri() -> list[str]:
    agac = ast.parse(_KAYNAK.read_text(encoding="utf-8"))
    return [
        n.value
        for n in ast.walk(agac)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and re.search(r"\bFROM\s+question_bank\b", n.value)
    ]


def _kolon_gecer(sql: str, kolon: str) -> bool:
    return re.search(rf"\b{kolon}\b", sql) is not None


def test_question_bank_sorgulari_bulundu() -> None:
    """Olcum aleti kor olmasin: dosyada beklenen sayida ham sorgu var."""
    assert len(_sql_sabitleri()) == 5, [s[:60] for s in _sql_sabitleri()]


def test_icerik_kolonu_okuyan_sorgu_question_content_join_eder() -> None:
    for sql in _sql_sabitleri():
        if any(_kolon_gecer(sql, k) for k in _ICERIK_KOLONLARI):
            assert re.search(r"\bJOIN\s+question_content\b", sql), sql


def test_metaveri_kolonu_okuyan_sorgu_question_metadata_join_eder() -> None:
    for sql in _sql_sabitleri():
        if any(_kolon_gecer(sql, k) for k in _METAVERI_KOLONLARI):
            assert re.search(r"\bJOIN\s+question_metadata\b", sql), sql


def test_bolunmus_kolonlar_alias_ile_nitelenmis() -> None:
    """JOIN var ama kolon `question_bank` alias'iyla okunuyorsa yine 500 olur.

    `b.question_text` gibi bir yazim yakalanir; `c.`/`m.` gecerli.
    """
    for sql in _sql_sabitleri():
        for k in (*_ICERIK_KOLONLARI, *_METAVERI_KOLONLARI):
            for m in re.finditer(rf"(\b\w+\.)?\b{k}\b", sql):
                onek = m.group(1)
                mesaj = f"{k!r} niteliksiz/yanlis alias ({onek}): {sql}"
                assert onek in _GECERLI_ONEKLER, mesaj
