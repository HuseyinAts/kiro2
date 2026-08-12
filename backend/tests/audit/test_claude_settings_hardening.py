"""Claude Code arac-zinciri sertlestirmesi bekcisi (X01/X03).

NEDEN VAR
---------
12 Agu 2026 dogrulama turu iki eksik/bayat ayari olctu:
  X01: .claude/settings.json model alani bayat ID (claude-sonnet-4-6) tasiyordu.
  X03: permissions.deny'de agir dizinler (node_modules, __pycache__, vb.) icin
       Read() kurali yoktu -> CLAUDE.md'nin "ripgrep root taramasi 30dk
       timeout" uyarisi yalnizca tavsiyeydi, zorlanmiyordu.
Fix commit baf59b23e ikisini de duzeltti. Bu test, gerilemeyi (bayat model
ID'ye veya bos deny listesine donusu) yakalar.
"""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parents[3] / ".claude" / "settings.json"

BAYAT_MODEL = "claude-sonnet-4-6"
AGIR_DIZINLER = ("node_modules", "__pycache__", ".venv", "dist", "build")


def _yukle() -> dict:
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def test_model_bayat_id_degil():
    ayar = _yukle()
    assert (
        ayar.get("model") != BAYAT_MODEL
    ), f"model alani bayat ID'ye geri dondu: {BAYAT_MODEL} (X01 regresyonu)"


def test_agir_dizinler_read_deny_ile_korunuyor():
    ayar = _yukle()
    deny = ayar.get("permissions", {}).get("deny", [])
    eksik = [
        d
        for d in AGIR_DIZINLER
        if not any(d in kural for kural in deny if kural.startswith("Read("))
    ]
    assert (
        not eksik
    ), f"agir dizinler icin Read() deny kurali eksik: {eksik} (X03 regresyonu)"
