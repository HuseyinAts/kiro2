"""ACIL 2023-2024 Geometri konu agacinin koruma testleri.

Canli DB istemez; konu haritasini, cevap anahtarini, metin veri setini ve
migration 0034'u DOSYADAN okur -- CI'da da koser.

NE KORUR
--------
1. HARITA ICI TUTARLILIK -- konu sayfa araliklari s5..s446'yi bosluksuz ve
   ustuste binmeden ortuyor; her testin sayfalari tek bir konuda kaliyor.
2. HARITA <-> MIGRATION  -- migration'daki dugum listesi ile haritadaki
   liste BIREBIR; kod oneki, ust-alt bagi ve duzey tutarli.
3. HARITA <-> VERI SETI  -- metin veri setindeki her test haritada var.
4. MIGRATION KIMLIGI     -- revizyon adi, zincir, ASCII, GEO-U* agacina
   dokunmama sozu.
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
HARITA_YOLU = CIKTI / "acil_2324_geometri_konu_haritasi.json"
ANAHTAR_YOLU = CIKTI / "acil_2324_geometri_cevap_anahtari.json"
METIN_YOLU = CIKTI / "acil_2324_geometri_metin.json"
MIG_YOLU = KOK / "alembic" / "versions" / "0034_acil_geo_konu_agaci.py"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_BOLUM = 6
BEKLENEN_KONU = 27
BEKLENEN_ALT_KONU = 3
BEKLENEN_TEST = 138
ILK_SAYFA, SON_SAYFA = 5, 446
ONEK = "GEO-ACL24"


@pytest.fixture(scope="module")
def harita() -> dict:
    return json.loads(HARITA_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def anahtar() -> list[dict]:
    return json.loads(ANAHTAR_YOLU.read_text("utf-8"))["anahtar"]


@pytest.fixture(scope="module")
def mig():
    spec = importlib.util.spec_from_file_location("mig0034", MIG_YOLU)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ---------------------------------------------------------------- 1. harita


def test_harita_sayilari(harita: dict) -> None:
    assert len(harita["bolumler"]) == BEKLENEN_BOLUM
    assert len(harita["konular"]) == BEKLENEN_KONU
    assert len(harita["alt_konular"]) == BEKLENEN_ALT_KONU
    assert len(harita["test_konu"]) == BEKLENEN_TEST


def test_konu_araliklari_bosluksuz_ve_cakismasiz(harita: dict) -> None:
    araliklar = sorted(
        (k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]
    )
    assert araliklar[0][0] == ILK_SAYFA
    assert araliklar[-1][1] == SON_SAYFA
    for onceki, sonraki in itertools.pairwise(araliklar):
        assert (
            onceki[1] + 1 == sonraki[0]
        ), f"{onceki[2]} s{onceki[1]} ile {sonraki[2]} s{sonraki[0]} arasi bosluk/cakisma"


def test_her_test_tek_konuda_kaliyor(harita: dict, anahtar: list[dict]) -> None:
    araliklar = [(k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]]
    sayfalar = {c["test"]: (c["bas_sayfa"], c["son_sayfa"]) for c in anahtar}
    assert len(sayfalar) == BEKLENEN_TEST
    for t, (bs, ss) in sayfalar.items():
        kapsayan = [a for a in araliklar if not (ss < a[0] or bs > a[1])]
        assert (
            len(kapsayan) == 1
        ), f"test {t} (s{bs}-{ss}) {len(kapsayan)} konuya yayildi"


def test_test_konu_atamasi_araliga_uyuyor(harita: dict, anahtar: list[dict]) -> None:
    """Atanan dugum, testin sayfa araligindaki konunun kendisi ya da cocugu."""
    konu = {k["kod"]: (k["bas_sayfa"], k["son_sayfa"]) for k in harita["konular"]}
    alt_ust = {a["kod"]: a["ust"] for a in harita["alt_konular"]}
    sayfalar = {c["test"]: (c["bas_sayfa"], c["son_sayfa"]) for c in anahtar}
    for t_str, kod in harita["test_konu"].items():
        t = int(t_str)
        bs, ss = sayfalar[t]
        ust = alt_ust.get(kod, kod)
        kbas, kson = konu[ust]
        assert (
            kbas <= bs and ss <= kson
        ), f"test {t} (s{bs}-{ss}) {ust} (s{kbas}-{kson}) disinda"


def test_alt_konu_testleri_atamayla_ayni(harita: dict) -> None:
    for alt in harita["alt_konular"]:
        for t in alt["testler"]:
            assert harita["test_konu"][str(t)] == alt["kod"]
    # Alt konuya atanan baska test yok.
    beyan = {t for a in harita["alt_konular"] for t in a["testler"]}
    atanan = {
        int(t)
        for t, k in harita["test_konu"].items()
        if k in {a["kod"] for a in harita["alt_konular"]}
    }
    assert beyan == atanan


def test_kodlar_onekli_ve_benzersiz(harita: dict) -> None:
    kodlar = (
        [b["kod"] for b in harita["bolumler"]]
        + [k["kod"] for k in harita["konular"]]
        + [a["kod"] for a in harita["alt_konular"]]
    )
    assert len(kodlar) == len(set(kodlar))
    assert all(k.startswith(ONEK + "-") for k in kodlar)
    assert harita["kok"] == "GEO"


# ------------------------------------------------------ 2. harita <-> migration


def test_migration_dugumleri_haritayla_birebir(harita: dict, mig) -> None:
    assert {k for k, _ in mig.BOLUMLER} == {b["kod"] for b in harita["bolumler"]}
    assert {k for _, k, _ in mig.KONULAR} == {k["kod"] for k in harita["konular"]}
    assert {k for _, k, _ in mig.ALT_KONULAR} == {
        a["kod"] for a in harita["alt_konular"]
    }


def test_migration_adlari_haritayla_ayni(harita: dict, mig) -> None:
    hb = {b["kod"]: b["ad"] for b in harita["bolumler"]}
    hk = {k["kod"]: k["ad"] for k in harita["konular"]}
    ha = {a["kod"]: a["ad"] for a in harita["alt_konular"]}
    assert dict(mig.BOLUMLER) == hb
    assert {k: a for _, k, a in mig.KONULAR} == hk
    assert {k: a for _, k, a in mig.ALT_KONULAR} == ha


def test_migration_ust_baglari_haritayla_ayni(harita: dict, mig) -> None:
    assert {k: u for u, k, _ in mig.KONULAR} == {
        k["kod"]: k["ust"] for k in harita["konular"]
    }
    assert {k: u for u, k, _ in mig.ALT_KONULAR} == {
        a["kod"]: a["ust"] for a in harita["alt_konular"]
    }


def test_kod_hiyerarsisi_kendini_anlatiyor(harita: dict) -> None:
    """Konu kodu bolum kodunun, alt konu kodu konu kodunun uzantisi."""
    for k in harita["konular"]:
        assert k["kod"].startswith(k["ust"] + "-")
    for a in harita["alt_konular"]:
        assert a["kod"].startswith(a["ust"] + "-")


# ------------------------------------------------------- 3. harita <-> veri seti


def test_veri_setindeki_her_test_haritada(harita: dict) -> None:
    veri = json.loads(METIN_YOLU.read_text("utf-8"))
    testler = {str(s["test"]) for s in veri["sorular"]}
    eksik = testler - set(harita["test_konu"])
    assert not eksik, f"haritada olmayan test: {sorted(eksik)[:5]}"


# ------------------------------------------------------------ 4. migration kimligi


def test_migration_kimligi_ve_zinciri(mig) -> None:
    assert mig.revision == "0034_acilgeo_agac"
    assert mig.down_revision == "0033_fiz345_agac"
    assert len(mig.revision) <= 32
    assert mig.KOD_ONEKI == ONEK
    assert mig.GEO_KOK_KODU == "GEO"


def test_migration_ascii(mig) -> None:
    metin = MIG_YOLU.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


def test_migration_mevcut_geo_agacina_dokunmuyor() -> None:
    """LIKE deseni yalniz GEO-ACL24; GEO-U* dugumleri kapsam disi."""
    metin = MIG_YOLU.read_text("utf-8")
    assert 'KOD_ONEKI + "%"' in metin
    assert not re.search(r"'GEO-U|\"GEO-U", metin)
    # Downgrade yalniz gunlukteki dugumleri hedefler.
    assert "FROM acilgeo_konu_gunlugu_0034" in metin or "FROM {GUNLUK}" in metin
