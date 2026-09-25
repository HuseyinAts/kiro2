"""0051: 345 AYT Kimya eski hat satirlarinin duzeltmesi kitabin basili haline bagli mi.

Canli DB istemez: migration sabitlerini, 345 2025 AYT Kimya cevap anahtarini,
metnini ve mukerrer aday dosyasini DOSYADAN okur.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
MIG_YOLU = KOK / "alembic" / "versions" / "0051_kim345ayt_eski_hat_cevap.py"
# eski hat satiri -> ayni sorunun bu kitaptaki (2025) karsiligi
KARSILIK = {
    "a0ee5afc-2697-5e46-ab8c-5cf3cf187dc1": "KIM345AYT-T014_02",
    "118a2a68-432a-524b-90f5-ccbe4fbc2c82": "KIM345AYT-T016_02",
    "2e60703b-ae1d-586c-817f-5c14cc4ad451": "KIM345AYT-T061_06",
    "6453cd45-1c4d-5b75-ae68-e6794bf56ef8": "KIM345AYT-T014_09",
    "076f3caa-d8ac-5405-8b1c-f0d95bdc3d34": "KIM345AYT-T100_01",
    "53c380ed-07ee-5bab-8898-9238baf3b9b1": "KIM345AYT-T136_06",
}
# Mukerrer taramasinin (soru basina EN IYI satir) harf celiskileri arasinda olup
# bu migration'in bilerek DOKUNMADIGI satirlar:
DOKUNULMAYAN = {
    # 2e60703b'nin 2024 etiketli ikizi; basiliya cekilirse ayni aktif hash -> 0052 ile pasif
    "0344bdd2-b463-5b43-9dd9-8cf1190e48c4",
    # harf farkli ama cevap ICERIGI ayni ('I ve III'; eski hatta sik C/D yer degismis)
    "096bab8a-dc45-57c6-84f6-8f8f4289f5ab",
}


def _n(t: str) -> str:
    """LaTeX / bizim gosterim farkini at: $ { } _ ^ ( ) \\ bosluk, eksi bicimi."""
    t = t.replace("\u2212", "-")
    return re.sub(r"[\s${}_^()\\]", "", t)


@pytest.fixture(scope="module")
def mig() -> object:
    spec = importlib.util.spec_from_file_location("mig0051", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def metin() -> dict[str, dict]:
    s = json.loads((CIKTI / "345_2025_ayt_kimya_metin.json").read_text("ascii"))
    return {x["dosya"]: x for x in s["sorular"]}


def test_zincir_ve_ascii(mig: object) -> None:
    assert mig.down_revision == "0050_kim345ayt_kaynak_adi"  # type: ignore[attr-defined]
    assert len(mig.revision) <= 32  # type: ignore[attr-defined]
    assert all(b < 128 for b in MIG_YOLU.read_bytes())


def test_yeni_cevap_kitabin_basili_anahtari(mig: object) -> None:
    """Her duzeltme, ayni sorunun iki okumayla okunmus basili cevabina esit."""
    anahtar = {
        f"{c['birim']}_{c['soru']:02d}": c["cevap"]
        for c in json.loads(
            (CIKTI / "345_2025_ayt_kimya_cevap_anahtari.json").read_text("ascii")
        )["cevaplar"]
    }
    d = mig.DUZELTMELER  # type: ignore[attr-defined]
    assert {x[0] for x in d} == set(KARSILIK)
    assert not {x[0] for x in d} & DOKUNULMAYAN
    for sid, _eh, _yh, eski, yeni, *_ in d:
        assert yeni == anahtar[KARSILIK[sid]] != eski, sid


def test_metin_ve_sik_duzeltmesi_basili_metinle_ayni(
    mig: object, metin: dict[str, dict]
) -> None:
    """Yeni metin parcasi basili govdede, yeni sik basili sikla ayni (gosterim haric)."""
    for sid, _eh, _yh, _e, _y, parcalar, sikler, _sil, _k in mig.DUZELTMELER:  # type: ignore[attr-defined]
        s = metin[KARSILIK[sid]]
        for eski, yeni in parcalar:
            assert _n(yeni) in _n(s["govde"]), (sid, yeni)
            assert _n(eski) not in _n(s["govde"]), (sid, eski)
        for h, eski, yeni in sikler:
            assert _n(yeni) == _n(s["sikler"][h]) != _n(eski), (sid, h)


def test_mukerrer_celiskileri_ya_duzeltildi_ya_gerekceli(mig: object) -> None:
    aday = json.loads(
        (CIKTI / "345_2025_ayt_kimya_mukerrer_adaylari.json").read_text("ascii")
    )["adaylar"]
    celiski = {
        a["db_id"] for a in aday if a["ayni_sik_sayisi"] >= 3 and not a["cevap_ayni"]
    }
    d = {x[0] for x in mig.DUZELTMELER}  # type: ignore[attr-defined]
    assert celiski <= d | DOKUNULMAYAN
    assert DOKUNULMAYAN.issubset(celiski)


def test_metin_ya_da_sik_degisirse_hash_de_degisir(mig: object) -> None:
    for sid, eh, yh, _e, _y, parcalar, sikler, _sil, _k in mig.DUZELTMELER:  # type: ignore[attr-defined]
        if parcalar or sikler:
            assert eh != yh, sid
        else:
            assert eh == yh, sid
        assert len({h for h, *_ in sikler}) == len(sikler), sid
