"""C1CELL 2024 Geometri konu agacinin koruma testleri.

Canli DB istemez; konu haritasini, metin veri setini ve migration 0035'i
DOSYADAN okur -- CI'da da koser.

NE KORUR
--------
1. HARITA ICI TUTARLILIK -- konu sayfa araliklari s7..s414'u bosluksuz ve
   ustuste binmeden ortuyor; kodlar onekli, benzersiz, hiyerarsiyi tasiyor.
2. HARITA <-> MIGRATION  -- migration'daki dugum listesi ile haritadaki
   liste BIREBIR; ad ve ust-alt bagi tutarli.
3. HARITA <-> VERI SETI  -- her birimin sayfalari tek bir konuda kaliyor ve
   haritanin her konusu soru aliyor (bos dugum yok).
4. MIGRATION KIMLIGI     -- revizyon adi, zincir, ASCII, mevcut GEO-U* ve
   GEO-ACL24 agaclarina dokunmama sozu.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
HARITA_YOLU = CIKTI / "c1cell_2024_geometri_konu_haritasi.json"
METIN_YOLU = CIKTI / "c1cell_2024_geometri_metin.json"
MIG_YOLU = KOK / "alembic" / "versions" / "0035_c1cell_geo_konu_agaci.py"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_BOLUM = 5
BEKLENEN_KONU = 21
BEKLENEN_BIRIM = 163
ILK_SAYFA, SON_SAYFA = 7, 414
ONEK = "GEO-C1C24"


@pytest.fixture(scope="module")
def harita() -> dict:
    return json.loads(HARITA_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def veri() -> dict:
    return json.loads(METIN_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def mig():
    spec = importlib.util.spec_from_file_location("mig0035", MIG_YOLU)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ---------------------------------------------------------------- 1. harita


def test_harita_sayilari(harita: dict) -> None:
    assert len(harita["bolumler"]) == BEKLENEN_BOLUM
    assert len(harita["konular"]) == BEKLENEN_KONU
    assert harita["kok"] == "GEO"
    assert harita["onek"] == ONEK


def test_konu_araliklari_bosluksuz_ve_cakismasiz(harita: dict) -> None:
    araliklar = sorted(
        (k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]
    )
    assert araliklar[0][0] == ILK_SAYFA
    assert araliklar[-1][1] == SON_SAYFA
    for onceki, sonraki in itertools.pairwise(araliklar):
        assert onceki[1] + 1 == sonraki[0], (
            f"{onceki[2]} s{onceki[1]} ile {sonraki[2]} s{sonraki[0]} "
            "arasi bosluk/cakisma"
        )


def test_kodlar_onekli_ve_benzersiz(harita: dict) -> None:
    kodlar = [b["kod"] for b in harita["bolumler"]] + [
        k["kod"] for k in harita["konular"]
    ]
    assert len(kodlar) == len(set(kodlar))
    assert all(k.startswith(ONEK + "-") for k in kodlar)


def test_kod_hiyerarsisi_kendini_anlatiyor(harita: dict) -> None:
    """Konu kodu bolum kodunun uzantisi; kod agaci kendi tasir."""
    bolum = {b["kod"] for b in harita["bolumler"]}
    for k in harita["konular"]:
        assert k["ust"] in bolum, k["kod"]
        assert k["kod"].startswith(k["ust"] + "-")


def test_her_bolum_en_az_bir_konu_tasiyor(harita: dict) -> None:
    ustler = {k["ust"] for k in harita["konular"]}
    bos = {b["kod"] for b in harita["bolumler"]} - ustler
    assert not bos, f"konusuz bolum: {sorted(bos)}"


# ------------------------------------------------------ 2. harita <-> migration


def test_migration_dugumleri_haritayla_birebir(harita: dict, mig) -> None:
    assert {k for k, _ in mig.BOLUMLER} == {b["kod"] for b in harita["bolumler"]}
    assert {k for _, k, _ in mig.KONULAR} == {k["kod"] for k in harita["konular"]}
    assert len(mig.BOLUMLER) == BEKLENEN_BOLUM
    assert len(mig.KONULAR) == BEKLENEN_KONU


def test_migration_adlari_haritayla_ayni(harita: dict, mig) -> None:
    assert dict(mig.BOLUMLER) == {b["kod"]: b["ad"] for b in harita["bolumler"]}
    assert {k: a for _, k, a in mig.KONULAR} == {
        k["kod"]: k["ad"] for k in harita["konular"]
    }


def test_migration_ust_baglari_haritayla_ayni(harita: dict, mig) -> None:
    assert {k: u for u, k, _ in mig.KONULAR} == {
        k["kod"]: k["ust"] for k in harita["konular"]
    }


# ------------------------------------------------------- 3. harita <-> veri seti


def test_her_birim_tek_konuda_kaliyor(harita: dict, veri: dict) -> None:
    """Konu atamasi birim duzeyinde yapiliyor; bolunen birim atamayi bozar."""
    araliklar = [(k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]]
    birim_sayfa: dict[int, set[int]] = {}
    for s in veri["sorular"]:
        birim_sayfa.setdefault(int(s["birim"]), set()).add(int(s["sayfa"]))
    assert len(birim_sayfa) == BEKLENEN_BIRIM
    for birim, sayfalar in birim_sayfa.items():
        bs, ss = min(sayfalar), max(sayfalar)
        kapsayan = [a for a in araliklar if not (ss < a[0] or bs > a[1])]
        assert (
            len(kapsayan) == 1
        ), f"birim {birim} (s{bs}-{ss}) {len(kapsayan)} konuya yayildi"


def test_haritanin_her_konusu_soru_aliyor(harita: dict, veri: dict) -> None:
    araliklar = [(k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]]
    dolu = set()
    for s in veri["sorular"]:
        p = int(s["sayfa"])
        dolu.update(kod for bas, son, kod in araliklar if bas <= p <= son)
    bos = {k["kod"] for k in harita["konular"]} - dolu
    assert not bos, f"soru almayan konu: {sorted(bos)}"


def test_veri_setindeki_her_sayfa_haritada(harita: dict, veri: dict) -> None:
    araliklar = [(k["bas_sayfa"], k["son_sayfa"]) for k in harita["konular"]]
    disarida = {
        int(s["sayfa"])
        for s in veri["sorular"]
        if not any(bas <= int(s["sayfa"]) <= son for bas, son in araliklar)
    }
    assert not disarida, f"haritasiz sayfa: {sorted(disarida)[:5]}"


# ------------------------------------------------------------ 4. migration kimligi


def test_migration_kimligi_ve_zinciri(mig) -> None:
    assert mig.revision == "0035_c1cellgeo_agac"
    assert mig.down_revision == "0034_acilgeo_agac"
    assert len(mig.revision) <= 32
    assert mig.KOD_ONEKI == ONEK
    assert mig.GEO_KOK_KODU == "GEO"


def test_migration_ascii() -> None:
    metin = MIG_YOLU.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


def test_migration_mevcut_geo_agaclarina_dokunmuyor() -> None:
    """LIKE deseni yalniz GEO-C1C24; GEO-U* ve GEO-ACL24 kapsam disi."""
    metin = MIG_YOLU.read_text("utf-8")
    assert 'KOD_ONEKI + "%"' in metin
    kod = "\n".join(
        satir for satir in metin.splitlines() if not satir.lstrip().startswith("#")
    )
    assert not re.search(r"['\"]GEO-U", kod)
    assert not re.search(r"['\"]GEO-ACL24", kod)
    # Downgrade yalniz gunlukteki dugumleri hedefler.
    assert mig_gunluk_referansi(metin), "downgrade gunluk tablosuna bagli degil"


def mig_gunluk_referansi(metin: str) -> bool:
    return "FROM c1cellgeo_konu_gunlugu_0035" in metin or "FROM {GUNLUK}" in metin
