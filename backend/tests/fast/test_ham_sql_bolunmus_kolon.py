"""Uretim yolundaki ham SQL, bolunmus question_bank kolonlarini sahibinden okuyor mu.

NEDEN VAR (rapor 7.7 / madde 15, 9 Eyl 2026)
--------------------------------------------
S210 split'i question_bank'i dort tabloya ayirdi. ORM erisimini
scripts/scan_split_accesses.py sayar; eski `questions` modelini
scripts/audit_dual_table_trap.py arar. HAM SQL STRING'I ikisinin de gorus
alani disinda kaldi -- AST sayimi: backend/ altinda `FROM question_bank`
gecen 325 sabit, 137'si JOIN'suz bolunmus kolon okuyor; uretim yolunda uc
dosya (osym_inspired_generator #226, ve buradaki iki dosya).

Bu bekci, listedeki uretim modullerinde `FROM question_bank` gecen her string
sabiti / f-string'i tarar: icerik kolonu -> question_content JOIN'i,
metaveri kolonu -> question_metadata JOIN'i, istatistik kolonu ->
question_statistics JOIN'i; kolon `q.`/`b.` gibi yanlis alias'la degil
sahibinin alias'iyla nitelenmis.

Kolon sahipleri information_schema'dan olculdu (9 Eyl 2026).
Mutasyon: eski tek-tablo sorgular geri konunca FAILED.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[2]

# Kanonik alias sozlesmesi: b=question_bank, c=content, m=metadata, s=statistics
_SAHIP = {
    "c": (
        "question_content",
        (
            "question_text",
            "question_image_url",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "option_e",
            "correct_answer",
            "explanation",
        ),
    ),
    "m": (
        "question_metadata",
        (
            "subject_area",
            "exam_type",
            "osym_format_compliant",
            "osym_year",
            "source_book",
        ),
    ),
    "s": ("question_statistics", ("difficulty_level", "embedding")),
}

# (modul, beklenen `FROM question_bank` sorgu sayisi) -- sayi, aletin kor
# olmadigini kanitlar: 0 bulup "temiz" demesin.
_MODULLER = [
    ("services/photo_ask_service.py", 1),
    ("api/wave2b_quality_routes.py", 1),
    # #226'nin ozel bekcisi (test_osym_inspired_ham_sql.py) buraya katildi;
    # DB'li kardesi tests/db/test_osym_inspired_sql_sema_uyumu.py duruyor.
    ("services/osym_inspired_generator.py", 5),
]


def _metin(n: ast.AST) -> str | None:
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.JoinedStr):
        return "".join(
            v.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
            else " {} "
            for v in n.values
        )
    return None


def _docstring_idleri(agac: ast.AST) -> set[int]:
    """Docstring sabitleri SQL degil (eski sorguyu ornek diye alintilayabilir)."""
    ids: set[int] = set()
    for n in ast.walk(agac):
        govde = getattr(n, "body", None)
        if (
            isinstance(govde, list)
            and govde
            and isinstance(govde[0], ast.Expr)
            and isinstance(govde[0].value, ast.Constant)
            and isinstance(govde[0].value.value, str)
        ):
            ids.add(id(govde[0].value))
        if isinstance(n, ast.JoinedStr):
            # f-string parcalari ayrica Constant olarak gezilir; butunu _metin
            # ile bir kez sayiyoruz, parcalari atla (cift sayim = yanlis olcum).
            ids.update(id(v) for v in n.values)
    return ids


def _sorgular(modul: str) -> list[str]:
    agac = ast.parse((_KOK / modul).read_text(encoding="utf-8"))
    atla = _docstring_idleri(agac)
    out = []
    for n in ast.walk(agac):
        if id(n) in atla:
            continue
        m = _metin(n)
        if m and re.search(r"\bFROM\s+question_bank\b", m):
            out.append(m)
    return out


@pytest.mark.parametrize(("modul", "beklenen"), _MODULLER)
def test_sorgular_bulundu(modul: str, beklenen: int) -> None:
    assert len(_sorgular(modul)) == beklenen, [s[:60] for s in _sorgular(modul)]


@pytest.mark.parametrize("modul", [m for m, _ in _MODULLER])
def test_bolunmus_kolon_sahibine_join_edilmis(modul: str) -> None:
    for sql in _sorgular(modul):
        for alias, (tablo, kolonlar) in _SAHIP.items():
            if any(re.search(rf"\b{k}\b", sql) for k in kolonlar):
                assert re.search(
                    rf"\bJOIN\s+{tablo}\s+{alias}\b", sql
                ), f"{modul}: {tablo} kolonu okunuyor ama JOIN yok:\n{sql}"


@pytest.mark.parametrize("modul", [m for m, _ in _MODULLER])
def test_bolunmus_kolon_sahibinin_aliasiyla_nitelenmis(modul: str) -> None:
    """JOIN var ama `b.question_text` / `q.subject_area` yazilmissa yine UndefinedColumn."""
    for sql in _sorgular(modul):
        for alias, (_tablo, kolonlar) in _SAHIP.items():
            for k in kolonlar:
                for m in re.finditer(rf"(\b\w+\.)?\b{k}\b", sql):
                    onek = m.group(1)
                    assert (
                        onek == f"{alias}."
                    ), f"{modul}: {k!r} beklenen alias {alias}., bulunan {onek!r}:\n{sql}"
