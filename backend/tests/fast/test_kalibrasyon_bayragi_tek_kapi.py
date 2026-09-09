"""is_calibrated=true yalnizca orneklem bekcili tek kapidan yazilir (0008, madde 3).

Olculen kusur (9 Eyl 2026): canli DB'de 20 question_statistics satiri
is_calibrated=true iken calibration_sample_size=0 ve irt_n_responses=0'di.
Uretim kodunda bayragi yanit orneklemi OLMADAN true yapan iki uyuyan yol
vardi: core/irt_daemon.py (baslatilmasi yorum satirinda) ve
services/irt_analysis_service.py::calibrate_soru_difficulty (uretimde
cagiran yok). Her ikisinden bayrak yazimi kaldirildi.

Sozlesme
--------
1. git'in izledigi uretim .py dosyalarinda `is_calibrated=True` (keyword)
   veya `x.is_calibrated = True` (atama) YALNIZCA
   services/question_bank_service.py::calibrate_question_irt icinde gecer.
2. calibrate_question_irt, sample_size < 1 ile cagrilinca DB'ye dokunmadan
   IRTValidationError firlatir.

Mutasyon: irt_daemon'daki `is_calibrated=True` geri konunca test 1 duser;
servisteki `sample_size < 1` bekcisi silinince test 2 duser.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.irt_validators import IRTValidationError
from services.question_bank_service import QuestionBankService

_KOK = Path(__file__).resolve().parents[2]
_TEK_KAPI = ("services/question_bank_service.py", "calibrate_question_irt")


def _izlenen_uretim_py() -> list[Path]:
    cikti = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=_KOK,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [
        _KOK / s
        for s in cikti
        if not s.startswith(("tests/", "_pilots/", "scripts/", "_scripts/"))
        and "versions_archive" not in s
        and "/tests/" not in s
    ]


def _true_yazimi(n: ast.AST) -> bool:
    if isinstance(n, ast.Call):
        return any(
            kw.arg == "is_calibrated"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
            for kw in n.keywords
        )
    if isinstance(n, ast.Assign):
        return any(
            isinstance(t, ast.Attribute)
            and t.attr == "is_calibrated"
            and isinstance(n.value, ast.Constant)
            and n.value.value is True
            for t in n.targets
        )
    return False


def _bayrak_yazan_yerler() -> list[tuple[str, str]]:
    """(dosya, kapsayan fonksiyon adi) listesi."""
    yerler: list[tuple[str, str]] = []
    for p in _izlenen_uretim_py():
        try:
            agac = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        goreli = p.relative_to(_KOK).as_posix()
        for fn in ast.walk(agac):
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if any(_true_yazimi(n) for n in ast.walk(fn)):
                yerler.append((goreli, fn.name))
    return yerler


def test_bayragi_yalnizca_orneklem_bekcili_kapi_yazar() -> None:
    yerler = _bayrak_yazan_yerler()
    assert _TEK_KAPI in yerler, "tek kapi bulunamadi -- servis mi tasindi?"
    fazla = [y for y in yerler if y != _TEK_KAPI]
    assert not fazla, f"is_calibrated=True baska yerde yaziliyor: {fazla}"


@pytest.mark.asyncio
async def test_orneklemsiz_kalibrasyon_reddedilir() -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    servis = QuestionBankService(db)
    # Bekci yoksa akis DB'ye iner: get_question None -> ValueError (IRT hatasi
    # degil) ve test "bekci yok" diye acikca duser (mutasyonla olculdu).
    servis.get_question = AsyncMock(return_value=None)

    with pytest.raises(IRTValidationError) as hata:
        await servis.calibrate_question_irt(
            question_id="q",
            new_discrimination=1.0,
            new_difficulty=0.0,
            new_guessing=0.2,
            new_upper_asymptote=1.0,
            calibration_method="EM",
            sample_size=0,
        )
    assert "sample_size" in str(hata.value)
    servis.get_question.assert_not_awaited()
    db.add.assert_not_called()
