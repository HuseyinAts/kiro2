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
SERIT_YOLU = CIKTI / "orijinal_2024_geometri_serit_taramasi.json"
BIRIM_YOLU = CIKTI / "orijinal_2024_geometri_birim_haritasi.json"
SIMGE_YOLU = CIKTI / "orijinal_2024_geometri_simge_taramasi.json"
KUTU_YOLU = CIKTI / "orijinal_2024_geometri_kirpim_kutulari.json"
ORTME_YOLU = CIKTI / "orijinal_2024_geometri_ortme_olcumu.json"
SAYFANO_YOLU = CIKTI / "orijinal_2024_geometri_sayfa_numarasi.json"
ANAHTAR_YOLU = CIKTI / "orijinal_2024_geometri_cevap_anahtari.json"
GOZLE_YOLU = CIKTI / "orijinal_2024_geometri_serit_gozle_okuma.json"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_BOLUM = 5
BEKLENEN_ADLI_KONU = 30
BEKLENEN_OSYM_DUGUM = 5
BEKLENEN_TEST = 226
BEKLENEN_BIRIM = 231  # 226 adli test + 5 OSYM bolumu
SORU_DISI_SAYFALAR = [149, 150, 260, 261, 321, 322, 388, 389]
BIRIM_TURU_SAYIMI = {
    "kazanim": 103,
    "osym_tarzi": 95,
    "orijinal": 28,
    "osym_cikmis": 5,
}
BEKLENEN_SORU = 2072  # cevap seridi girdisi -- otorite
BEKLENEN_SIMGE_TOPLAM = 2099  # tum kitap (soru disi sayfalar dahil)
BEKLENEN_SIMGE_BIRIM = 2070  # birim sayfalarinda
SIMGESIZ_SORULAR = [[151, 8], [323, 3]]
HARF_DAGILIMI = {"A": 208, "B": 392, "C": 634, "D": 564, "E": 274}
GOZLE_SAYFA, GOZLE_GIRDI = 90, 823
EN_DUSUK_MARJ = 0.0845
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


@pytest.fixture(scope="module")
def serit() -> dict:
    return json.loads(SERIT_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def birim() -> dict:
    return json.loads(BIRIM_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def simge() -> dict:
    return json.loads(SIMGE_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def kutu() -> dict:
    return json.loads(KUTU_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def ortme() -> dict:
    return json.loads(ORTME_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def sayfano() -> dict:
    return json.loads(SAYFANO_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return json.loads(ANAHTAR_YOLU.read_text("utf-8"))


@pytest.fixture(scope="module")
def gozle() -> dict:
    return json.loads(GOZLE_YOLU.read_text("utf-8"))


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


def test_konu_araliklari_ile_soru_disi_sayfalar_kitabi_tam_ortuyor(
    harita: dict,
) -> None:
    """Bolum ayraci ve bilgi notlari sayfalari hicbir konuya ait DEGIL.

    Once bu sayfalar OSYM dugumlerinin araligina dahil edilmisti; serit
    taramasi OSYM bolumlerinin bir onceki sayfada bittigini gosterdi.
    """
    ortulen: list[int] = []
    for k in harita["konular"]:
        ortulen.extend(range(k["bas_sayfa"], k["son_sayfa"] + 1))
    ortulen.extend(harita["soru_disi_sayfalar"])
    assert sorted(ortulen) == list(
        range(ILK_SAYFA, SON_SAYFA + 1)
    ), "konu araliklari + soru disi sayfalar kitabi tam bir kez ortmeli"


def test_soru_disi_sayfalar_olculen_sekiz_sayfa(harita: dict) -> None:
    assert harita["soru_disi_sayfalar"] == SORU_DISI_SAYFALAR


def test_sayfa_turu_sayimi_toplami_kitap_kadar(harita: dict) -> None:
    sayim = harita["sayfa_turu_sayimi"]
    assert sum(sayim.values()) == SON_SAYFA - ILK_SAYFA + 1
    assert sayim["bolum_ayraci"] == sayim["bilgi_notlari"] == 4
    assert sayim["kazanim"] + sayim["osym_tarzi"] + sayim["orijinal"] == 400


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


def test_araliklar_cakismiyor_ve_kitap_sinirlarinda(harita: dict) -> None:
    araliklar = sorted(
        (k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]
    )
    assert araliklar[0][0] == ILK_SAYFA
    assert araliklar[-1][1] == SON_SAYFA
    for onceki, sonraki in itertools.pairwise(araliklar):
        assert (
            onceki[1] < sonraki[0]
        ), f"{onceki[2]} s{onceki[1]} ile {sonraki[2]} s{sonraki[0]} cakisiyor"


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


# ------------------------------------------ 6. birim haritasi (iki kanal kapanisi)


def test_birim_sayisi_iki_kanalda_da_ayni(birim: dict, harita: dict) -> None:
    """Birim basi rozetten, birim sonu seritten; ikisi birebir eslesmeli."""
    assert birim["birim_sayisi"] == len(birim["birimler"]) == BEKLENEN_BIRIM
    rozetten = sum(len(k["test_bas_sayfalari"]) for k in harita["konular"])
    assert rozetten + BEKLENEN_OSYM_DUGUM == BEKLENEN_BIRIM


def test_birimler_kitabi_cakismadan_ortuyor(birim: dict) -> None:
    ortulen: list[int] = []
    for b in birim["birimler"]:
        assert b["bas_sayfa"] <= b["son_sayfa"], b["kod"]
        assert b["sayfa_sayisi"] == b["son_sayfa"] - b["bas_sayfa"] + 1, b["kod"]
        ortulen.extend(range(b["bas_sayfa"], b["son_sayfa"] + 1))
    ortulen.extend(birim["soru_disi_sayfalar"])
    assert sorted(ortulen) == list(range(ILK_SAYFA, SON_SAYFA + 1))


def test_her_birimin_sonunda_serit_var(birim: dict, serit: dict) -> None:
    seritli = {int(s) for s in serit["sayfalar"]}
    assert len(seritli) == serit["seritli_sayfa_sayisi"] == BEKLENEN_BIRIM
    sonlar = {b["son_sayfa"] for b in birim["birimler"]}
    assert (
        sonlar == seritli
    ), "her serit tam olarak bir birimi kapatmali; artan ya da eksik serit yok"


def test_birim_baslari_rozet_sayfalari(birim: dict, harita: dict) -> None:
    rozet_sayfalari = {s for k in harita["konular"] for s in k["test_bas_sayfalari"]}
    osym_baslari = {
        k["bas_sayfa"] for k in harita["konular"] if not k["test_bas_sayfalari"]
    }
    baslar = {b["bas_sayfa"] for b in birim["birimler"]}
    assert baslar == rozet_sayfalari | osym_baslari


def test_birim_turleri_olculen_dagilim(birim: dict) -> None:
    sayim: dict[str, int] = {}
    for b in birim["birimler"]:
        sayim[b["tur"]] = sayim.get(b["tur"], 0) + 1
    assert sayim == BIRIM_TURU_SAYIMI
    adli = sum(v for t, v in sayim.items() if t != "osym_cikmis")
    assert adli == BEKLENEN_TEST


def test_osym_birimleri_bolum_sonunda(birim: dict) -> None:
    osym = [b for b in birim["birimler"] if b["tur"] == "osym_cikmis"]
    assert len(osym) == BEKLENEN_OSYM_DUGUM
    assert all(b["kod"].endswith("-O01") for b in osym), [b["kod"] for b in osym]


def test_serit_taramasi_desenle_kuruldu(serit: dict) -> None:
    """Dedektorun neden esik degil desen oldugu belgede degil, dosyada dursun."""
    assert "desen" in serit["neden_esik_degil_desen"] or (
        "bicim" in serit["neden_esik_degil_desen"]
    )
    assert serit["seritli_sayfa_sayisi"] == BEKLENEN_BIRIM


# ------------------------------------- 7. soru sayisi <-> simge sayisi kapanisi


def test_soru_sayisi_otoritesi_serit(birim: dict) -> None:
    """Otorite serit girdisi; simge degil -- kitap 2 soruda simgeyi basmamis."""
    assert "cevap seridi" in birim["soru_sayisi_otoritesi"]
    assert "simge sayisi degil" in birim["soru_sayisi_otoritesi"]
    assert birim["toplam_soru"] == BEKLENEN_SORU
    assert sum(b["soru_sayisi"] for b in birim["birimler"]) == BEKLENEN_SORU


def test_simgesiz_sorular_civili(birim: dict) -> None:
    assert birim["simgesiz_sorular"] == SIMGESIZ_SORULAR


def test_soru_ile_simge_farki_tam_olarak_simgesizler_kadar(birim: dict) -> None:
    fark = birim["toplam_soru"] - birim["toplam_simge_birim_icinde"]
    assert fark == len(SIMGESIZ_SORULAR) == 2
    assert birim["toplam_simge_birim_icinde"] == BEKLENEN_SIMGE_BIRIM


def test_sapan_birimler_yalniz_simgesiz_sayfalari_tasiyanlar(birim: dict) -> None:
    sapan = {
        b["kod"]: (b["soru_sayisi"], b["simge_sayisi"])
        for b in birim["birimler"]
        if b["soru_sayisi"] != b["simge_sayisi"]
    }
    assert len(sapan) == 2, sapan
    assert all(g - s == 1 for g, s in sapan.values()), sapan
    simgesiz_sayfa = {s for s, _ in SIMGESIZ_SORULAR}
    for kod in sapan:
        b = next(x for x in birim["birimler"] if x["kod"] == kod)
        aralik = set(range(b["bas_sayfa"], b["son_sayfa"] + 1))
        assert aralik & simgesiz_sayfa, kod


def test_simge_taramasi_toplami(simge: dict) -> None:
    toplam = sum(len(v) for v in simge["sayfalar"].values())
    assert toplam == simge["toplam_simge"] == BEKLENEN_SIMGE_TOPLAM


def test_simgeler_birim_ici_ve_bilgi_notlarinda(simge: dict, birim: dict) -> None:
    """Birim disinda simge yalniz BILGI NOTLARI sayfalarinda olabilir."""
    birim_sayfalari: set[int] = set()
    for b in birim["birimler"]:
        birim_sayfalari.update(range(b["bas_sayfa"], b["son_sayfa"] + 1))
    disarida = {
        int(s): len(v)
        for s, v in simge["sayfalar"].items()
        if int(s) not in birim_sayfalari
    }
    # s5-s7 Bolum 1'in bilgi notlari; digerleri haritadaki soru disi sayfalar
    bilgi_notlari = {150, 261, 322, 389}
    assert set(disarida) - {5, 6, 7} == bilgi_notlari, disarida
    assert sum(disarida.values()) == BEKLENEN_SIMGE_TOPLAM - BEKLENEN_SIMGE_BIRIM


def test_bolum_ayraci_sayfalarinda_simge_yok(simge: dict) -> None:
    for s in (149, 260, 321, 388):
        assert str(s) not in simge["sayfalar"], s


# --------------------------------------------------- 8. kirpim kutulari (Faz 2.4)


def test_kutu_sayisi_soru_sayisina_esit(kutu: dict, birim: dict) -> None:
    assert kutu["kutu_sayisi"] == len(kutu["kutular"]) == BEKLENEN_SORU
    assert birim["toplam_soru"] == BEKLENEN_SORU


def test_elle_girilen_kutu_yalniz_iki_simgesiz_soru(kutu: dict) -> None:
    elle = [k for k in kutu["kutular"] if k.get("elle")]
    assert len(elle) == len(SIMGESIZ_SORULAR) == 2
    assert {(k["sayfa"], k["sutun"]) for k in elle} == {(151, "sag"), (323, "sol")}
    assert all(k["simge"] is None for k in elle)
    # simge capali kutularin hepsinde simge var
    capali = [k for k in kutu["kutular"] if not k.get("elle")]
    assert len(capali) == BEKLENEN_SIMGE_BIRIM
    assert all(k["simge"] is not None for k in capali)


def test_kutular_kart_icinde_ve_ters_degil(kutu: dict) -> None:
    kart_g, kart_y = kutu["kart"][2], kutu["kart"][3]
    for k in kutu["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        assert 0 <= x0 < x1 <= kart_g, k
        assert 0 <= y0 < y1 <= kart_y, k
        assert y1 - y0 >= 40, k


def test_kutular_sayfanin_kendi_sutun_sinirlarina_oturuyor(kutu: dict) -> None:
    """Sinirlar SAYFA BASINA; tek sabit sinir kullanilamaz (bkz. bolum 16)."""
    sinir = kutu["sayfa_sutunlari"]
    for k in kutu["kutular"]:
        s = sinir[str(k["sayfa"])][k["sutun"]]
        assert [k["kutu"][0], k["kutu"][2]] == s, k
    for s, v in sinir.items():
        assert v["sol"][0] < v["sol"][1] < v["sag"][0] < v["sag"][1], s


def test_sutun_sinirlari_sayfanin_kendi_simgelerinden(kutu: dict, simge: dict) -> None:
    """Sol kenarlar o sayfanin en soldaki SOL/SAG simgesinden 7 px solda."""
    for s, v in kutu["sayfa_sutunlari"].items():
        konum = simge["sayfalar"][s]
        sol = min(x for _, x in konum if x < 200)
        sag = min(x for _, x in konum if x >= 200)
        assert v["sag"][0] == sag - 7, s
        # cift sayfada sol kenar filigran bandinin sagina itilir
        ham = sol - 7
        bant = kutu["filigran_bantlari"]["cift" if int(s) % 2 == 0 else "tek"]
        beklenen = max(ham, bant[1] + 1) if int(s) % 2 == 0 else ham
        assert v["sol"][0] == beklenen, s


def test_sutun_sinirlari_paritede_kayiyor(kutu: dict) -> None:
    """Kitabin metin blogu tek/cift sayfada kayiyor -- sabit sinir bu yuzden yanlisti."""
    tek = sorted(v["sag"][0] for s, v in kutu["sayfa_sutunlari"].items() if int(s) % 2)
    cift = sorted(
        v["sag"][0] for s, v in kutu["sayfa_sutunlari"].items() if int(s) % 2 == 0
    )
    assert tek and cift
    kayma = cift[len(cift) // 2] - tek[len(tek) // 2]
    assert 10 <= kayma <= 22, kayma


def test_kutular_filigran_bandina_girmiyor(kutu: dict) -> None:
    """Yayinevi dis kenar filigrani kirpimin disinda kalmali."""
    tek = kutu["filigran_bantlari"]["tek"]
    cift = kutu["filigran_bantlari"]["cift"]
    for k in kutu["kutular"]:
        x0, _, x1, _ = k["kutu"]
        if k["sayfa"] % 2:
            assert x1 < tek[0], k
        else:
            assert x0 > cift[1], k
    # kutusu olmayan sayfanin siniri de banda giremez (yoksa sinir sessizce
    # bozulur ve hicbir kutu onu tasimadigi icin kapi goremez)
    for s, v in kutu["sayfa_sutunlari"].items():
        if int(s) % 2:
            assert v["sag"][1] < tek[0], s
        else:
            assert v["sol"][0] > cift[1], s


def test_kutu_genisligi_olculen_aralikta(kutu: dict) -> None:
    gen = sorted(k["kutu"][2] - k["kutu"][0] for k in kutu["kutular"])
    assert gen[0] == 312 and gen[-1] == 330, (gen[0], gen[-1])
    assert gen[len(gen) // 2] == 320


def test_ayni_sayfa_sutununda_kutular_cakismiyor(kutu: dict) -> None:
    grup: dict[tuple, list] = {}
    for k in kutu["kutular"]:
        grup.setdefault((k["sayfa"], k["sutun"]), []).append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        for a, b in itertools.pairwise(g):
            assert a["kutu"][3] <= b["kutu"][1], (anahtar, a["kutu"], b["kutu"])


def test_hicbir_kutu_cevap_seridine_girmiyor(kutu: dict, serit: dict) -> None:
    """Sizinti kapisi: kirpim alti, o sayfadaki seridin ust kenarinin ustunde."""
    serit_ust = {
        int(s): min(b["y"][0] for b in bloklar)
        for s, bloklar in serit["sayfalar"].items()
    }
    for k in kutu["kutular"]:
        ust = serit_ust.get(k["sayfa"])
        if ust is None:
            continue
        assert k["kutu"][3] <= ust, (k["sayfa"], k["kutu"], ust)


def test_kutu_capasi_simge_taramasindan_geliyor(kutu: dict, simge: dict) -> None:
    konumlar = {(int(s), tuple(p)) for s, v in simge["sayfalar"].items() for p in v}
    for k in kutu["kutular"]:
        if k.get("elle"):
            continue
        assert (k["sayfa"], tuple(k["simge"])) in konumlar, k


def test_kutu_yukseklik_ozeti_gercek(kutu: dict) -> None:
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutu["kutular"])
    ozet = kutu["yukseklik"]
    assert ozet["min"] == yuk[0]
    assert ozet["max"] == yuk[-1]
    assert ozet["medyan"] == yuk[len(yuk) // 2]


# ------------------------------------------------- 9. ortme olcumu (Faz 2.6)


def test_ortme_olcumu_her_simgeyi_kapsiyor(ortme: dict, simge: dict) -> None:
    assert ortme["olculen_simge"] == BEKLENEN_SIMGE_TOPLAM
    assert len(ortme["olcum"]) == BEKLENEN_SIMGE_TOPLAM
    konumlar = {(int(s), tuple(p)) for s, v in simge["sayfalar"].items() for p in v}
    assert {(r["sayfa"], (r["y"], r["x"])) for r in ortme["olcum"]} == konumlar


def test_ortme_ozeti_olcumden_turetilebilir(ortme: dict) -> None:
    disi = set(ortme["soru_disi_sayfalar"])
    soru = [r for r in ortme["olcum"] if r["sayfa"] not in disi]
    assert len(soru) == ortme["soru_sayfasindaki_simge"] == BEKLENEN_SIMGE_BIRIM
    v = sorted(r["halka"] for r in soru)
    assert ortme["soru_sayfasi_ozeti"]["max"] == v[-1]
    assert ortme["soru_sayfasi_ozeti"]["medyan"] == v[len(v) // 2]


def test_yuksek_simgeler_esikten_turetilebilir(ortme: dict) -> None:
    disi = set(ortme["soru_disi_sayfalar"])
    esik = ortme["yuksek_esik"]
    beklenen = [
        r for r in ortme["olcum"] if r["sayfa"] not in disi and r["halka"] >= esik
    ]
    assert ortme["yuksek_simge"] == beklenen
    assert len(beklenen) == 20


def test_yuksek_simgeler_sutun_araligindaki_filigranda(ortme: dict) -> None:
    """19'u sag sutunun gutter'inda, 1'i sol sutunda -- soru icerigi degil."""
    xler = sorted({r["x"] for r in ortme["yuksek_simge"]})
    assert min(xler) == 56, xler
    assert all(358 <= x <= 390 for x in xler if x != 56), xler
    sag = [r for r in ortme["yuksek_simge"] if r["x"] >= 200]
    assert len(sag) == 19
    assert len(ortme["yuksek_simge"]) - len(sag) == 1


def test_ortme_sonucu_disk_beyazlatmayi_onaylyor(ortme: dict) -> None:
    assert "soru kaybettirmez" in ortme["sonuc"]
    assert ortme["soru_sayfasi_ozeti"]["medyan"] == 0


# ----------------------------------------- 10. basili sayfa numarasi (Faz 2.3)


def test_sayfa_numarasi_taramasi_tum_kitabi_kapsiyor(sayfano: dict) -> None:
    basamak = sayfano["sayfa_basamak_sayisi"]
    assert sayfano["taranan_sayfa"] == SON_SAYFA - ILK_SAYFA + 1 == len(basamak)
    assert sorted(int(s) for s in basamak) == list(range(ILK_SAYFA, SON_SAYFA + 1))


def test_basamak_sayisi_dosya_numarasiyla_uyusuyor(sayfano: dict) -> None:
    """Duzgun bir kaydirmayi disliyor: 9/10 ve 99/100 sinirlarinda patlardi."""
    basamak = sayfano["sayfa_basamak_sayisi"]
    rakamsiz = set(sayfano["rakamsiz_sayfalar"])
    uyusan = 0
    for s, n in basamak.items():
        if int(s) in rakamsiz:
            assert n == 0, s
            continue
        assert n == len(s), (s, n)
        uyusan += 1
    assert uyusan == sayfano["basamak_uyusan"] == 421
    assert sayfano["basamak_uyusmayan"] == []
    assert sayfano["ofset"] == 0


def test_rakamsiz_sayfalar_bolum_ayraclari(sayfano: dict, harita: dict) -> None:
    """Numarasiz dort sayfa, renk kanalinin rozetsiz dedigi dort sayfa."""
    assert sayfano["rakamsiz_sayfalar"] == [149, 260, 321, 388]
    assert set(sayfano["rakamsiz_sayfalar"]) < set(harita["soru_disi_sayfalar"])


def test_dogrudan_okunan_capalar_kendini_dogruluyor(sayfano: dict) -> None:
    capalar = sayfano["dogrudan_okunan_capalar"]
    assert len(capalar) == 7
    for dosya, basili in capalar.items():
        assert int(dosya) == basili, (dosya, basili)
    assert min(int(s) for s in capalar) == ILK_SAYFA
    assert max(int(s) for s in capalar) == SON_SAYFA


def test_deger_okunmadigi_yazili(sayfano: dict) -> None:
    """Basamak sayildi, rakamin DEGERI okunmadi -- cikti bunu soylemeli."""
    assert "DEGERI okunmadi" in sayfano["ne_olculdu"]
    assert "kaydirma" in sayfano["neden_yeterli"]


# ------------------------------------------------- 11. cevap anahtari (Faz 3)


def test_anahtar_her_soruya_bir_cevap_veriyor(anahtar: dict, birim: dict) -> None:
    cevaplar = anahtar["cevaplar"]
    assert anahtar["toplam_cevap"] == len(cevaplar) == BEKLENEN_SORU
    beklenen = {
        (b["kod"], i) for b in birim["birimler"] for i in range(1, b["soru_sayisi"] + 1)
    }
    assert {(c["birim"], c["soru"]) for c in cevaplar} == beklenen


def test_cevaplar_yalniz_a_e(anahtar: dict) -> None:
    assert {c["cevap"] for c in anahtar["cevaplar"]} == set("ABCDE")


def test_harf_dagilimi_olculen_dagilim(anahtar: dict) -> None:
    sayim: dict[str, int] = {}
    for c in anahtar["cevaplar"]:
        sayim[c["cevap"]] = sayim.get(c["cevap"], 0) + 1
    assert sayim == anahtar["harf_dagilimi"] == HARF_DAGILIMI
    assert sum(sayim.values()) == BEKLENEN_SORU


def test_kaynak_dagilimi_gozle_ve_makine(anahtar: dict) -> None:
    sayim: dict[str, int] = {}
    for c in anahtar["cevaplar"]:
        sayim[c["kaynak"]] = sayim.get(c["kaynak"], 0) + 1
    assert sayim == anahtar["kaynak_dagilimi"]
    assert sayim["gozle"] == GOZLE_GIRDI
    assert sayim["gozle"] + sayim["makine"] == BEKLENEN_SORU


def test_gozle_okuma_dosyasi_kendi_icinde_tutarli(gozle: dict) -> None:
    seritler = gozle["seritler"]
    assert gozle["sayfa_sayisi"] == len(seritler) == GOZLE_SAYFA
    assert sum(len(v) for v in seritler.values()) == gozle["girdi_sayisi"]
    assert gozle["girdi_sayisi"] == GOZLE_GIRDI
    assert all(set(v) <= set("ABCDE") for v in seritler.values())


def test_gozle_okunan_sayfalar_birim_sonu(gozle: dict, birim: dict) -> None:
    sonlar = {b["son_sayfa"] for b in birim["birimler"]}
    assert {int(s) for s in gozle["seritler"]} <= sonlar


def test_gozle_okunan_serit_uzunlugu_birim_soru_sayisi(
    gozle: dict, birim: dict
) -> None:
    soru = {b["son_sayfa"]: b["soru_sayisi"] for b in birim["birimler"]}
    for s, metin in gozle["seritler"].items():
        assert len(metin) == soru[int(s)], s


def test_gozle_okunan_cevaplar_anahtarla_ayni(
    anahtar: dict, gozle: dict, birim: dict
) -> None:
    """Gozle okunan yerde otorite okuma; anahtar onu tasimali."""
    birim_of = {b["son_sayfa"]: b["kod"] for b in birim["birimler"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    for s, metin in gozle["seritler"].items():
        kod = birim_of[int(s)]
        for i, h in enumerate(metin, start=1):
            c = cevap[(kod, i)]
            assert c["cevap"] == h, (s, i)
            assert c["kaynak"] == "gozle", (s, i)


def test_makine_kaynakli_cevaplarda_marj_yuksek(anahtar: dict) -> None:
    """Ilk turda yanlis cikan 7 girdinin marji 0.0101 idi; o bant bos."""
    makine = [c for c in anahtar["cevaplar"] if c["kaynak"] == "makine"]
    assert len(makine) == BEKLENEN_SORU - GOZLE_GIRDI
    assert min(c["marj"] for c in makine) >= 0.10
    assert anahtar["en_dusuk_marj"] == EN_DUSUK_MARJ


def test_anahtar_cozumle_degil_kitaptan(anahtar: dict) -> None:
    assert "basili cevap seridinden" in anahtar["nereden"]
    assert "hicbir cevap uretilmedi" in anahtar["nereden"].lower()
    assert anahtar["gozle_ile_uyusmayan"] == 0
    assert anahtar["gozle_ile_uyusan"] == GOZLE_GIRDI


# ------------------------------------------------------------------ 12. ASCII


@pytest.mark.parametrize(
    "yol",
    [
        HARITA_YOLU,
        OKUMA1_YOLU,
        OKUMA2_YOLU,
        ROZET_YOLU,
        SERIT_YOLU,
        BIRIM_YOLU,
        SIMGE_YOLU,
        KUTU_YOLU,
        ORTME_YOLU,
        SAYFANO_YOLU,
        ANAHTAR_YOLU,
        GOZLE_YOLU,
    ],
)
def test_ciktilar_ascii(yol: Path) -> None:
    metin = yol.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"{yol.name}: ASCII disi karakter: {disarida}"
