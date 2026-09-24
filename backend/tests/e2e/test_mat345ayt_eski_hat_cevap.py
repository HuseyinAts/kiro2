"""0047: 345 AYT eski hat satirlarinin cevap duzeltmesi kitabin basili anahtarina bagli mi.

Canli DB istemez: migration sabitlerini, 345 2025 AYT Matematik cevap
anahtarini ve mukerrer aday dosyasini DOSYADAN okur.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
MIG_YOLU = KOK / "alembic" / "versions" / "0047_mat345ayt_eski_hat_cevap.py"
# eski hat satiri -> ayni sorunun bu kitaptaki (2025) karsiligi
KARSILIK = {
    "d2b4fdfc-fb70-5a1a-8e0d-a0be32fa0154": "MAT345AYT-T005_13",
    "af48fac5-4031-5ba8-b451-aef329e794c8": "MAT345AYT-T011_05",
    "ada94c26-9a41-5f37-8648-2a7764d09e20": "MAT345AYT-T036_01",
}


@pytest.fixture(scope="module")
def mig() -> object:
    spec = importlib.util.spec_from_file_location("mig0047", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_zincir_ve_ascii(mig: object) -> None:
    assert mig.down_revision == "0046_mat345ayt_kaynak_adi"  # type: ignore[attr-defined]
    assert len(mig.revision) <= 32  # type: ignore[attr-defined]
    assert all(b < 128 for b in MIG_YOLU.read_bytes())


def test_yeni_cevap_kitabin_basili_anahtari(mig: object) -> None:
    """Her duzeltme, ayni sorunun iki okumayla okunmus basili cevabina esit."""
    anahtar = {
        f"{c['birim']}_{c['soru']:02d}": c["cevap"]
        for c in json.loads(
            (CIKTI / "345_2025_ayt_matematik_cevap_anahtari.json").read_text("ascii")
        )["cevaplar"]
    }
    d = mig.DUZELTMELER  # type: ignore[attr-defined]
    assert {x[0] for x in d} == set(KARSILIK)
    for sid, _eh, _yh, eski, yeni, *_ in d:
        assert yeni == anahtar[KARSILIK[sid]] != eski, sid


def test_duzeltilen_satirlar_mukerrer_taramasindaki_celiskiler(mig: object) -> None:
    aday = json.loads(
        (CIKTI / "345_2025_ayt_matematik_mukerrer_adaylari.json").read_text("ascii")
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
    assert [x[7] for x in mig.DUZELTMELER] == [False, True, False]  # type: ignore[attr-defined]
