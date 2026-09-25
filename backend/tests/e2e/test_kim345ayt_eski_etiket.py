"""0052: 345 AYT Kimya eski hat -- TYT etiketi, TYT konu dugumu, ikiz pasif.

Canli DB istemez: migration sabitlerini, 0049 agacini ve 0051'i DOSYADAN okur.
"""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
V = KOK / "alembic" / "versions"
MIG_YOLU = V / "0052_kim345ayt_eski_etiket.py"
TYT_SAYISI = 268  # 2025 etiketi 118 + 2024 etiketi 150
KONU_SAYISI = 117


def _modul(ad: str, yol: Path) -> object:
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mig() -> object:
    return _modul("mig0052", MIG_YOLU)


@pytest.fixture(scope="module")
def agac() -> object:
    return _modul("agac0049", V / "0049_kim345ayt_konu_agaci.py")


@pytest.fixture(scope="module")
def cevap() -> object:
    return _modul("mig0051", V / "0051_kim345ayt_eski_hat_cevap.py")


def test_zincir_ve_ascii(mig: object) -> None:
    assert mig.down_revision == "0051_kim345ayt_eski_cevap"  # type: ignore[attr-defined]
    assert len(mig.revision) <= 32  # type: ignore[attr-defined]
    assert all(b < 128 for b in MIG_YOLU.read_bytes())


def test_tyt_listesi(mig: object) -> None:
    t = mig.TYT_SATIRLARI  # type: ignore[attr-defined]
    assert len(t) == len(set(t)) == TYT_SAYISI
    for i in t:
        uuid.UUID(i)


def test_konu_tasima_tyt_agacindan_kitabin_agacina(mig: object, agac: object) -> None:
    k = mig.KONU_TASIMA  # type: ignore[attr-defined]
    assert len(k) == len({x[0] for x in k}) == KONU_SAYISI
    kitap = {u for u, _ in agac.UNITELER} | {x[1] for x in agac.KONULAR}  # type: ignore[attr-defined]
    for sid, eski, yeni in k:
        uuid.UUID(sid)
        assert eski.startswith("TYT-KIM-"), sid
        assert yeni in kitap, sid


def test_ikiz_0051_in_dokunmadigi_satir(mig: object, cevap: object) -> None:
    """Pasife alinan satir 0051'in duzelttigi satirlardan biri DEGIL; ikizi duzeltildi."""
    ikiz = mig.IKIZ_PASIF  # type: ignore[attr-defined]
    duzeltilen = {x[0] for x in cevap.DUZELTMELER}  # type: ignore[attr-defined]
    assert ikiz not in duzeltilen
    assert "2e60703b-ae1d-586c-817f-5c14cc4ad451" in duzeltilen
    assert ikiz in mig.TYT_SATIRLARI  # type: ignore[attr-defined]


def test_upgrade_yalniz_guvenli_guncelleme(mig: object) -> None:
    """Guard'lar kaynakta: TYT kontrolu, eski dugum kontrolu, aktiflik kontrolu, gunluk."""
    src = MIG_YOLU.read_text("ascii")
    assert "exam_type = 'TYT'" in src
    assert "mevcut.get(sid) != eski" in src
    assert "if aktif is True:" in src
    assert src.count("_gunlukle(") == 4  # tanim + uc degisiklik turu
