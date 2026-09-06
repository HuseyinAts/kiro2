"""`.github/scripts/check_new_endpoints.py` yorum satirlarini rota sanmamali.

NEDEN VAR (olcum: PR #181, 6 Eyl 2026)
--------------------------------------
Kaldirilan bir rotayi ACIKLAYAN yorum blogunda `@router.get("/health")`
metni geciyordu. Gate bunu YENI BIR UC sanip HARD C1 ("path missing
/api/v1/ prefix") ile PR'i blokladi -- ustelik iki dosyada, biri bir TEST
dosyasindaki duz aciklama satiriydi. Yani kapi kodu degil METNI okuyordu
ve belgeleme yapmayi cezalandiriyordu.

Bu bekci o davranisi civiliyor: yorum icindeki decorator metni sayilmaz,
gercek decorator sayilir. Ikisi ayni dosyada test edilir ki "hepsini
atliyor" seklinde bir asiri-duzeltme de yakalansin.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_GATE = (
    Path(__file__).resolve().parents[3]
    / ".github"
    / "scripts"
    / "check_new_endpoints.py"
)


def _gate_modulu():
    """Nokta ile baslayan dizin normal import edilemez -- dosyadan yukle."""
    if not _GATE.is_file():
        pytest.skip(f"gate script bulunamadi: {_GATE}")
    spec = importlib.util.spec_from_file_location("kiro2_endpoint_gate", _GATE)
    if spec is None or spec.loader is None:
        pytest.skip("gate script yuklenemedi")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kiro2_endpoint_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


ORNEK = '''
"""Modul docstring'i icinde ornek kod: @router.put("/docstring-uc")"""

# Bu satir bir aciklama: @router.get("/health") rotasi kaldirildi.
    #   ayrica girintili yorum: @router.post("/eski-uc")


@router.get("/api/v1/gercek-uc")
async def gercek_uc():
    return {}
'''


def test_yorumdaki_decorator_rota_sayilmaz(tmp_path, monkeypatch):
    mod = _gate_modulu()
    dosya = tmp_path / "ornek_api.py"
    dosya.write_text(ORNEK, encoding="utf-8")

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    # Dosyadaki TUM satirlar "bu PR'da eklendi" sayilsin.
    eklenen = set(range(1, len(ORNEK.splitlines()) + 2))

    uclar = mod.extract_endpoints("ornek_api.py", eklenen)
    yollar = [u.path for u in uclar]

    assert (
        "/health" not in yollar
    ), f"Yorum icindeki decorator metni rota sayildi: {yollar}"
    assert (
        "/eski-uc" not in yollar
    ), f"Girintili yorum icindeki decorator metni rota sayildi: {yollar}"
    assert (
        "/docstring-uc" not in yollar
    ), f"Docstring icindeki decorator metni rota sayildi: {yollar}"
    assert yollar == [
        "/api/v1/gercek-uc"
    ], f"Gercek rota kaybedildi ya da fazladan rota uretildi: {yollar}"
