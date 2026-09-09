"""KVKK tablolarini ORM'de TEK model iddia eder (rapor madde 13, 9 Eyl 2026).

Olculen kusur: core/kvkk_compliance.py kendi `declarative_base()` uzerinde
`kvkk_consents` (+3 tablo) icin Integer anahtarli ikinci bir sema tanimliyordu;
canli tablo models/kvkk_models.py (uuid7) ile uyusuyor, uretim kodu bu
modulden yalnizca `is_minor` kullaniyordu. Modul emekli edildi.

Bekci, git'in izledigi uretim .py dosyalarini (tests/ ve arsiv haric) AST ile
tarar: `__tablename__` degeri `kvkk_` ile baslayan her sinif icin tanim yeri
tek olmali ve models/ altinda olmali. `core.kvkk_compliance` ise yalnizca
`is_minor` ve yas esigini disari vermeli -- Base/Column geri gelirse duser.
Mutasyon: eski 1.213 satirlik modul geri konunca 2/2 FAILED.
"""

from __future__ import annotations

import ast
import subprocess
from collections import defaultdict
from pathlib import Path

_KOK = Path(__file__).resolve().parents[2]


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
        if not s.startswith(("tests/", "_pilots/", "scripts/"))
        and "versions_archive" not in s
        and "/tests/" not in s
    ]


def _kvkk_tablename_tanimlari() -> dict[str, list[str]]:
    tanimlar: dict[str, list[str]] = defaultdict(list)
    for p in _izlenen_uretim_py():
        try:
            agac = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(agac):
            if not isinstance(n, ast.ClassDef):
                continue
            for g in n.body:
                if (
                    isinstance(g, ast.Assign)
                    and any(
                        isinstance(h, ast.Name) and h.id == "__tablename__"
                        for h in g.targets
                    )
                    and isinstance(g.value, ast.Constant)
                    and isinstance(g.value.value, str)
                    and g.value.value.startswith("kvkk_")
                ):
                    tanimlar[g.value.value].append(
                        str(p.relative_to(_KOK)).replace("\\", "/")
                    )
    return tanimlar


def test_her_kvkk_tablosunu_tek_model_iddia_eder() -> None:
    tanimlar = _kvkk_tablename_tanimlari()
    assert (
        "kvkk_consents" in tanimlar
    ), "kanonik model bulunamadi (models/kvkk_models.py?)"
    for tablo, yerler in tanimlar.items():
        assert len(yerler) == 1, f"{tablo} birden fazla ORM modelinde: {yerler}"
        assert yerler[0].startswith(
            "models/"
        ), f"{tablo} models/ disinda tanimli: {yerler}"


def test_kvkk_compliance_yalnizca_yas_esigi_verir() -> None:
    import core.kvkk_compliance as m

    disa = {ad for ad in dir(m) if not ad.startswith("_")}
    assert disa == {
        "date",
        "datetime",
        "ZoneInfo",
        "is_minor",
        "KVKK_RESIT_YASI",
    }, sorted(disa)
