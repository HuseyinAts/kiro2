"""0044: eski hat satirlarinin cevap duzeltmesi kitabin basili anahtarina bagli mi.

Canli DB istemez: migration sabitlerini, 345 2025 TYT Matematik cevap
anahtarini ve mukerrer aday dosyasini DOSYADAN okur.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
MIG_YOLU = KOK / "alembic" / "versions" / "0044_mat345_eski_hat_cevap.py"
# eski hat satiri -> ayni sorunun bu kitaptaki (2025) karsiligi
KARSILIK = {
    "b5aa8e19-7658-5f96-98b8-a9c8f6e5b918": "MAT345-T055_09",
    "a4919225-930d-52d5-93a4-063c300b3a82": "MAT345-T055_13",
    "2c50e760-7d21-53d4-a843-ad267371e5d6": "MAT345-T084_01",
    "58e3f697-aa25-5be1-a52e-06c95e396a8a": "MAT345-T169_02",
}


@pytest.fixture(scope="module")
def mig() -> object:
    spec = importlib.util.spec_from_file_location("mig0044", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_zincir_ve_ascii(mig: object) -> None:
    assert mig.down_revision == "0043_mat345tyt_kaynak_adi"  # type: ignore[attr-defined]
    assert len(mig.revision) <= 32  # type: ignore[attr-defined]
    assert all(b < 128 for b in MIG_YOLU.read_bytes())


def test_yeni_cevap_kitabin_basili_anahtari(mig: object) -> None:
    """Her duzeltme, ayni sorunun iki okumayla okunmus basili cevabina esit."""
    anahtar = {
        f"{c['birim']}_{c['soru']:02d}": c["cevap"]
        for c in json.loads(
            (CIKTI / "345_2025_tyt_matematik_cevap_anahtari.json").read_text("ascii")
        )["cevaplar"]
    }
    d = mig.DUZELTMELER  # type: ignore[attr-defined]
    assert {x[0] for x in d} == set(KARSILIK)
    for sid, _eh, _yh, eski, yeni, *_ in d:
        assert yeni == anahtar[KARSILIK[sid]] != eski, sid


def test_duzeltilen_satirlar_mukerrer_taramasindaki_celiskiler(mig: object) -> None:
    aday = json.loads(
        (CIKTI / "345_2025_tyt_matematik_mukerrer_adaylari.json").read_text("ascii")
    )["adaylar"]
    celiski = {
        a["db_id"]: (a["dosya"], a["db_cevap"])
        for a in aday
        if a["ayni_sik_sayisi"] >= 3 and not a["cevap_ayni"]
    }
    d = {x[0]: x[3] for x in mig.DUZELTMELER}  # type: ignore[attr-defined]
    assert {k: v[0] for k, v in celiski.items()} == KARSILIK
    assert {k: v[1] for k, v in celiski.items()} == d


def test_metin_degisirse_hash_de_degisir(mig: object) -> None:
    for sid, eh, yh, _e, _y, ep, yp, _sil, _k in mig.DUZELTMELER:  # type: ignore[attr-defined]
        if ep is None:
            assert yp is None and eh == yh, sid
        else:
            assert ep != yp and eh != yh, sid
    assert [x[7] for x in mig.DUZELTMELER] == [False, False, True, False]  # type: ignore[attr-defined]
