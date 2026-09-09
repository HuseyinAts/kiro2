"""cop_yedek_arsivle.py DROP kapisi (rapor madde 1, 9 Eyl 2026).

Sozlesme: DROP yalnizca (1) --onay SIL, (2) manifest dogrulandi=true,
(3) dump dosyasi yerinde ise ve (4) canli satir sayilari manifestle ayni ise
calisir. Ilk uc kapi DB'siz olculur; dorduncusu icin DB gerekir (burada
_satir_sayilari yamalanir). Kapilardan herhangi biri kalkarsa test duser.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from scripts.quality import cop_yedek_arsivle as m


def _manifest(tmp_path: Path, **ek) -> Path:
    dump = tmp_path / "x.dump"
    dump.write_bytes(b"PGDMP")
    veri = {
        "tablolar": ["t1"],
        "satir_sayilari": {"t1": 3},
        "dump": dump.name,
        "onkosul": "x.prereq.sql",
        "dogrulandi": True,
    }
    veri.update(ek)
    p = tmp_path / "x.manifest.json"
    p.write_text(json.dumps(veri), encoding="utf-8")
    return p


def _args(manifest: Path, onay: str = "SIL") -> argparse.Namespace:
    return argparse.Namespace(manifest=str(manifest), onay=onay)


def test_onay_yoksa_drop_reddedilir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        m, "_satir_sayilari", lambda *a, **k: pytest.fail("DB'ye gidildi")
    )
    with pytest.raises(SystemExit, match="onay SIL"):
        m.drop(_args(_manifest(tmp_path), onay=""))


def test_dogrulanmamis_manifest_reddedilir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        m, "_satir_sayilari", lambda *a, **k: pytest.fail("DB'ye gidildi")
    )
    with pytest.raises(SystemExit, match="dogrulanmamis"):
        m.drop(_args(_manifest(tmp_path, dogrulandi=False)))


def test_dump_dosyasi_yoksa_reddedilir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        m, "_satir_sayilari", lambda *a, **k: pytest.fail("DB'ye gidildi")
    )
    p = _manifest(tmp_path)
    (tmp_path / "x.dump").unlink()
    with pytest.raises(SystemExit, match="Dump dosyasi"):
        m.drop(_args(p))


def test_satir_sayisi_degismisse_reddedilir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(m, "_satir_sayilari", lambda *a, **k: {"t1": 4})
    monkeypatch.setattr(
        m.psycopg, "connect", lambda *a, **k: pytest.fail("DROP baglantisi acildi")
    )
    with pytest.raises(SystemExit, match="degismis"):
        m.drop(_args(_manifest(tmp_path)))


def test_bakim_dsn_yalnizca_veritabani_adini_degistirir() -> None:
    assert (
        m._bakim_dsn(
            "postgresql://u:p@localhost:5434/kiro2", "postgres"
        )  # pragma: allowlist secret
        == "postgresql://u:p@localhost:5434/postgres"  # pragma: allowlist secret
    )
