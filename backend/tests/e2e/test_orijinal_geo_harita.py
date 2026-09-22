"""Orijinal 2024 Geometri konu haritasinin koruma testleri (Faz 1).

Canli DB istemez, sayfa goruntusu istemez; haritayi, onu ureten IKI
ICINDEKILER OKUMASINI ve TEST ROZETI TARAMASINI dosyadan okur -- CI'da koser.

NEDEN UC DOSYA
--------------
Faz 0 fisi "sayim otoritesi piksel degil, iki bagimsiz okuma olmali" demisti.
Iki okuma yapildi ve birebir tuttu -- ama okunan sey ICINDEKILER tablosuydu,
yani kitabin kendi OZETI. Rozet taramasi bu ozeti sayfalarin kendisiyle
karsilastirdi ve iki konuda sapma buldu:

    B01-02 Ucgende Acilar          rozet 8, icindekiler 9
    B01-11 Ucgende Aci-Kenar Bag.  rozet 5, icindekiler 4

Sapmalar ZIT YONLU oldugu icin TOPLAM (226) iki kanalda da ayni. Yani
"toplam tutuyor" demek dagilimin dogru oldugunu GOSTERMEZ; bu testler
toplami degil, konu konu dagilimi capalar.

Otorite sayfadaki rozettir: 30 adli konunun 30'unda da o konudaki rozet
sayisi son rozetin uzerindeki numaraya esit cikti (elle okundu).

NE KORUR
--------
1. IKI BAGIMSIZ OKUMA -- iki okuma satir satir ayni, AMA farkli kirpimdan.
   Ikisi ayni kirpimin kopyasi olsaydi "iki okuma" bir sey kanitlamazdi.
2. HARITA <-> OKUMA -- sayfa numaralari ve icindekiler test sayilari.
3. HARITA <-> ROZET TARAMASI -- test sayilari ve test baslangic sayfalari.
4. BILINEN SAPMALAR CIVILI -- iki sapma tam olarak bu ikisi; ucuncusu
   cikarsa ya da biri sessizce duzelirse test kirmizi olur.
5. HARITA ICI TUTARLILIK + sayim capalari + ASCII.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
HARITA_YOLU = CIKTI / "orijinal_2024_geometri_konu_haritasi.json"
OKUMA1_YOLU = CIKTI / "orijinal_2024_geometri_icindekiler_okuma1.json"
OKUMA2_YOLU = CIKTI / "orijinal_2024_geometri_icindekiler_okuma2.json"
ROZET_YOLU = CIKTI / "orijinal_2024_geometri_rozet_taramasi.json"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_BOLUM = 5
BEKLENEN_ADLI_KONU = 30
BEKLENEN_OSYM_DUGUM = 5
BEKLENEN_TEST = 226
ILK_SAYFA, SON_SAYFA = 8, 432
ONEK = "GEO-ORJ24"
KAYNAK = "Orijinal 2024 TYT-AYT Geometri Soru Bankasi"
# kod -> (rozet, icindekiler); olculen sapmalar, civili
BILINEN_SAPMALAR = {
    "GEO-ORJ24-B01-02": (8, 9),
    "GEO-ORJ24-B01-11": (5, 4),
}


@pytest.fixture(scope="module")
def harita() -> dict:
    return json.loads(HARITA_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def okuma1() -> dict:
    return json.loads(OKUMA1_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def okuma2() -> dict:
    return json.loads(OKUMA2_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def rozet() -> dict:
    return json.loads(ROZET_YOLU.read_text("utf-8"))


def _duzle(okuma: dict) -> list[tuple]:
    cik = []
    for bol in okuma["bolumler"]:
        for k in bol["konular"]:
            cik.append((bol["no"], bol["ad"], k["ad"], k["test"], k["sayfa"]))
    return cik


def _adli(harita: dict) -> list[dict]:
    return [k for k in harita["konular"] if k["test_sayisi"] is not None]


# ------------------------------------------------------- 1. iki bagimsiz okuma


def test_iki_okuma_birebir_ayni(okuma1: dict, okuma2: dict) -> None:
    a, b = _duzle(okuma1), _duzle(okuma2)
    assert len(a) == len(b), f"satir sayisi farkli: {len(a)} != {len(b)}"
    for i, (x, y) in enumerate(zip(a, b, strict=True)):
        assert x == y, f"satir {i}: {x!r} != {y!r}"


def test_iki_okuma_farkli_kirpimdan_geliyor(okuma1: dict, okuma2: dict) -> None:
    """Ayni kirpimin kopyasi olsalardi 'iki okuma' bir sey kanitlamazdi."""
    assert (
        okuma1["kaynak"] != okuma2["kaynak"]
    ), "iki okumanin kaynagi ayni -- bu iki okuma degil, bir okumanin kopyasi"


def test_okuma_sayilari(okuma1: dict) -> None:
    satirlar = _duzle(okuma1)
    osym = [r for r in satirlar if r[2].startswith("OSYM")]
    assert len(okuma1["bolumler"]) == BEKLENEN_BOLUM
    assert len(osym) == BEKLENEN_OSYM_DUGUM
    assert len(satirlar) - len(osym) == BEKLENEN_ADLI_KONU
    assert sum(r[3] for r in satirlar if r[3]) == BEKLENEN_TEST
    assert all(r[3] is None for r in osym), "OSYM bolumunun test sayisi bilinmiyor"


def test_okumadaki_sayfalar_monoton_artiyor(okuma1: dict) -> None:
    sayfalar = [r[4] for r in _duzle(okuma1)]
    assert all(x < y for x, y in itertools.pairwise(sayfalar))
    assert sayfalar[0] == ILK_SAYFA


# ------------------------------------------------------------ 2. harita <-> okuma


def test_harita_okumadan_turetilebilir(harita: dict, okuma1: dict) -> None:
    satirlar = _duzle(okuma1)
    konular = harita["konular"]
    assert len(konular) == len(satirlar)
    for dugum, satir in zip(konular, satirlar, strict=True):
        bolum_no, _, _, test, sayfa = satir
        assert dugum["bas_sayfa"] == sayfa, dugum["kod"]
        assert dugum["test_sayisi_icindekiler"] == test, dugum["kod"]
        assert dugum["ust"] == f"{ONEK}-B{bolum_no:02d}", dugum["kod"]


def test_son_sayfalar_bir_sonrakinin_basindan_turuyor(harita: dict) -> None:
    konular = harita["konular"]
    for onceki, sonraki in itertools.pairwise(konular):
        assert onceki["son_sayfa"] == sonraki["bas_sayfa"] - 1, onceki["kod"]
    assert konular[-1]["son_sayfa"] == SON_SAYFA


# -------------------------------------------------- 3. harita <-> rozet taramasi


def test_rozet_taramasi_kendi_icinde_tutarli(rozet: dict) -> None:
    olcum = {int(s): v for s, v in rozet["sayfa_olcumu"].items()}
    esik = rozet["esik"]
    turetilen = sorted(s for s, v in olcum.items() if v >= esik)
    assert (
        turetilen == rozet["rozetli_sayfalar"]
    ), "rozetli sayfa listesi olcumden turetilemiyor -- liste elle duzenlenmis"
    assert len(turetilen) == rozet["rozetli_sayfa_sayisi"] == BEKLENEN_TEST
    assert sorted(olcum) == list(range(ILK_SAYFA, SON_SAYFA + 1))


def test_rozet_esigi_genis_bir_bosluga_oturuyor(rozet: dict) -> None:
    """Esik 1000-1300 arasinda sonucu degistirmiyorsa dedektor esige hassas degil."""
    d = rozet["esik_duyarliligi"]
    assert d["1000"] == d["1100"] == d["1300"] == BEKLENEN_TEST


def test_harita_test_sayilari_rozetten_geliyor(harita: dict, rozet: dict) -> None:
    rozetli = set(rozet["rozetli_sayfalar"])
    toplandi: list[int] = []
    for k in harita["konular"]:
        sayfalar = k["test_bas_sayfalari"]
        toplandi.extend(sayfalar)
        assert set(sayfalar) <= rozetli, k["kod"]
        assert all(k["bas_sayfa"] <= s <= k["son_sayfa"] for s in sayfalar), k["kod"]
        if k["test_sayisi"] is None:
            assert sayfalar == [], f"{k['kod']}: OSYM dugumunde rozet olmamali"
        else:
            assert k["test_sayisi"] == len(sayfalar), k["kod"]
            assert (
                sayfalar[0] == k["bas_sayfa"]
            ), f"{k['kod']}: konunun ilk sayfasi Test 1'in ilk sayfasi olmali"
            assert all(x < y for x, y in itertools.pairwise(sayfalar)), k["kod"]
    assert sorted(toplandi) == sorted(
        rozetli
    ), "taramadaki her rozet tam olarak bir konuya dagitilmali"


def test_otorite_alani_yazili(harita: dict) -> None:
    assert "rozet" in harita["test_sayisi_otoritesi"]
    assert "icindekiler degil" in harita["test_sayisi_otoritesi"]


# ---------------------------------------------------- 4. bilinen sapmalar civili


def test_sapmalar_tam_olarak_bilinen_ikisi(harita: dict) -> None:
    sapan = {
        k["kod"]: (k["test_sayisi"], k["test_sayisi_icindekiler"])
        for k in _adli(harita)
        if k["test_sayisi"] != k["test_sayisi_icindekiler"]
    }
    assert (
        sapan == BILINEN_SAPMALAR
    ), "icindekiler <-> rozet sapmalari degisti; once olc, sonra bu capayi guncelle"


def test_sapmalar_zit_yonlu_oldugu_icin_toplam_ayni(harita: dict) -> None:
    """Toplamin tutmasi dagilimin dogru oldugunu gostermez -- bunu belgeleyen test."""
    adli = _adli(harita)
    assert sum(k["test_sayisi"] for k in adli) == BEKLENEN_TEST
    assert sum(k["test_sayisi_icindekiler"] for k in adli) == BEKLENEN_TEST
    fark = [
        k["test_sayisi"] - k["test_sayisi_icindekiler"]
        for k in adli
        if k["test_sayisi"] != k["test_sayisi_icindekiler"]
    ]
    assert sorted(fark) == [-1, 1]


# ------------------------------------------------------- 5. harita ici tutarlilik


def test_harita_kimligi(harita: dict) -> None:
    assert harita["kaynak"] == KAYNAK
    assert harita["kok"] == "GEO"
    assert harita["onek"] == ONEK
    assert len(harita["bolumler"]) == BEKLENEN_BOLUM


def test_araliklar_bosluksuz_ve_cakismasiz(harita: dict) -> None:
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
    bolum = {b["kod"] for b in harita["bolumler"]}
    for k in harita["konular"]:
        assert k["ust"] in bolum, k["kod"]
        assert k["kod"].startswith(k["ust"] + "-")


def test_her_bolum_en_az_bir_konu_tasiyor(harita: dict) -> None:
    ustler = {k["ust"] for k in harita["konular"]}
    bos = {b["kod"] for b in harita["bolumler"]} - ustler
    assert not bos, f"konusuz bolum: {sorted(bos)}"


def test_her_bolumun_son_dugumu_osym(harita: dict) -> None:
    """Kitapta her bolum OSYM'de cikmis sorularla bitiyor -- yapi kapisi."""
    son = {}
    for k in harita["konular"]:
        son[k["ust"]] = k
    for kod, dugum in son.items():
        assert dugum["ad"].startswith(
            "OSYM'de Cikmis Sorular"
        ), f"{kod} bolumu OSYM dugumuyle bitmiyor: {dugum['ad']}"
        assert dugum["test_sayisi"] is None, kod


def test_adli_konu_sayilari(harita: dict) -> None:
    adli = _adli(harita)
    assert len(adli) == BEKLENEN_ADLI_KONU
    assert len(harita["konular"]) - len(adli) == BEKLENEN_OSYM_DUGUM
    assert all(k["test_sayisi"] > 0 for k in adli)


# ------------------------------------------------------------------- 6. ASCII


@pytest.mark.parametrize("yol", [HARITA_YOLU, OKUMA1_YOLU, OKUMA2_YOLU, ROZET_YOLU])
def test_ciktilar_ascii(yol: Path) -> None:
    metin = yol.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"{yol.name}: ASCII disi karakter: {disarida}"
