"""345 2025 AYT Turk Edebiyati veri hattinin koruma testleri.

Canli DB istemez, sayfa goruntusu istemez; depodaki olcum dosyalarini okur --
CI'da koser. Her test OLCULEN bir capayi civiler; bir capa degisirse once
olculur, sonra burada guncellenir.

NE KORUR
--------
1. CEVAP ANAHTARI  -- 1384 cevap, 148 test, okuma kanallari, numara
                      surekliligi, ham okumalardan (kitap sonu anahtar)
                      turetilebilirlik.
2. KONU HARITASI   -- 10 unite / 46 konu (icindekiler); Kazanim Odakli ve OSYM
                      Tadinda testler konu, Karma / Orijinal / Genel Bakis unite
                      araliginda; tur ici sira kesintisiz; bant okumasiyla ayni.
3. CAPA / KUTU     -- sutun basina secilen kanal numara sayisiyla birebir;
                      kutular kartta, cakismasiz; ortak metin kutulari.
4. ORTME           -- olcum tam kitap, kenar kapisi civili.
5. METIN           -- 1384 kayit, basili numara == test ici sira, bes sik,
                      cevap alani yok; 11 ortak metin, kapsamlari testte.
6. IKINCI OKUMA    -- on kayit + orneklem hukmu tutarli.
7. ASCII           -- depo ciktilari ASCII.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_ayt_edebiyat_"
ANAHTAR_YOLU = CIKTI / f"{ON}cevap_anahtari.json"
HARITA_YOLU = CIKTI / f"{ON}konu_haritasi.json"
TARAMA_YOLU = CIKTI / f"{ON}capa_taramasi.json"
KUTU_YOLU = CIKTI / f"{ON}kirpim_kutulari.json"
ORTME_YOLU = CIKTI / f"{ON}ortme_olcumu.json"
METIN_YOLU = CIKTI / f"{ON}metin.json"
MUKERRER_YOLU = CIKTI / f"{ON}mukerrer_adaylari.json"
HAM_YOLU = CIKTI / f"{ON}ham_okumalar.json"
IKINCI_YOLU = CIKTI / f"{ON}ikinci_okuma.json"

BEKLENEN_SORU = 1384
BEKLENEN_TEST = 148
BEKLENEN_UNITE, BEKLENEN_KONU = 10, 46
SORU_SAYFASI = 306
ICERIK_SAYFA = 328
ANAHTAR_SAYFALARI = set(range(321, 329))
SON_SORU_SAYFASI = 320
AYRAC = {5, 39, 71, 113, 147, 191, 221, 255, 275, 299}
KAYNAK_DAGILIMI = {
    "iki_okuma+piksel": 1325,
    "iki_okuma(biri_tereddutlu)+piksel+goz": 58,
    "iki_okuma(uyusmaz)+piksel+goz": 1,
}
HARF_DAGILIMI = {"A": 265, "B": 284, "C": 307, "D": 273, "E": 255}
TUR_TEST = {
    "kazanim_odakli": 46,
    "osym_tadinda": 58,
    "orijinal": 8,
    "karma": 26,
    "genel_bakis": 10,
}
TUR_SORU = {
    "kazanim_odakli": 496,
    "osym_tadinda": 530,
    "orijinal": 34,
    "karma": 247,
    "genel_bakis": 77,
}
TUR_HARF = {
    "K": "kazanim_odakli",
    "O": "osym_tadinda",
    "R": "orijinal",
    "M": "karma",
    "G": "genel_bakis",
}
KONU_TURLERI = ("kazanim_odakli", "osym_tadinda")
# Iki okumanin tek harf farki (s323 Tanzimat Siiri OSYM Tadinda 1, soru 5).
UYUSMAZ = ("EDB345AYT-T053", 5)
SIMGE_TOPLAM, NUMARA_TOPLAM = 1355, 1484
SUTUN_KANALI = {"numara": 611, "simge": 1}
NUMARA_EN_GENIS = 12
UST_KURALI = {"logo": 61, "logo_yakin_secenek": 1, "tavan_asimi": 1}
# Ust kesimi +-3 satirda notr koyu piksel: ikisi de OSYM KOSESI logosu ustu
# (gozle incelendi), metin kesilmiyor.
KESIM = ["EDB345AYT-T043_02", "EDB345AYT-T145_04"]
SAYFA_ALTI = 896
KART_G, KART_Y = 742, 977
ORTME_SORU = 94
# Kenar kapisi: kirpimin sol 2 px'inde koyu piksel; T068_11 dikey 'CIKMIS SORU'
# yazisi, digerleri Genel Bakis sag sutununun turuncu kose susu (gozle).
KENAR = [
    ("EDB345AYT-T068", 11),
    ("EDB345AYT-T141", 6),
    ("EDB345AYT-T143", 6),
    ("EDB345AYT-T144", 7),
    ("EDB345AYT-T145", 6),
    ("EDB345AYT-T146", 6),
    ("EDB345AYT-T147", 7),
    ("EDB345AYT-T148", 5),
]
SEKILLI, GORSEL_SIKLI, KUSURLU, ETIKETLI = 96, 1, 59, 61
# 3 cozunurluk kurali (rn~m, grup 03) + 2 ikinci okuma orneklemi ilk okuma hatasi.
DUZELTME_OKUMASI = 5
DISK_ORTULU_KUTU = 18
GUCLU_MUKERRER = 6
BEKLENEN_ORTAK = 11
ORTAK_KAPSANAN = 23


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return _oku(ANAHTAR_YOLU)


@pytest.fixture(scope="module")
def harita() -> dict:
    return _oku(HARITA_YOLU)


@pytest.fixture(scope="module")
def tarama() -> dict:
    return _oku(TARAMA_YOLU)


@pytest.fixture(scope="module")
def kutu() -> dict:
    return _oku(KUTU_YOLU)


@pytest.fixture(scope="module")
def ortme() -> dict:
    return _oku(ORTME_YOLU)


@pytest.fixture(scope="module")
def metin() -> dict:
    return _oku(METIN_YOLU)


# ------------------------------------------------------- 1. cevap anahtari


def test_anahtar_sayilari_ve_dagilim(anahtar: dict) -> None:
    c = anahtar["cevaplar"]
    assert anahtar["toplam_cevap"] == len(c) == BEKLENEN_SORU
    assert anahtar["test_sayisi"] == BEKLENEN_TEST
    assert (
        dict(Counter(x["kaynak"] for x in c))
        == anahtar["kaynak_dagilimi"]
        == KAYNAK_DAGILIMI
    )
    assert (
        dict(Counter(x["cevap"] for x in c))
        == anahtar["harf_dagilimi"]
        == HARF_DAGILIMI
    )


def test_anahtar_cozumle_degil_kitaptan(anahtar: dict) -> None:
    assert "basili cevap anahtarindan" in anahtar["nereden"]
    assert "hicbir cevap uretilmedi" in anahtar["nereden"].lower()


def test_numara_kitap_boyunca_kesintisiz(anahtar: dict) -> None:
    """Okuma sirasinda her numara ya oncekinin +1'i ya da 1 (yeni test)."""
    sirali = sorted(
        anahtar["cevaplar"], key=lambda x: (x["dosya"], x["sutun"], x["serit_sira"])
    )
    test_bas = 1
    for a, b in itertools.pairwise(sirali):
        if b["soru"] == 1:
            test_bas += 1
            assert b["birim"] != a["birim"], (a, b)
        else:
            assert b["soru"] == a["soru"] + 1, (a, b)
            assert b["birim"] == a["birim"], (a, b)
    assert test_bas == BEKLENEN_TEST


def test_soru_sayfalari_ayraclar_ve_anahtar_sayfalari(anahtar: dict) -> None:
    sayfa = {x["dosya"] for x in anahtar["cevaplar"]}
    assert len(sayfa) == SORU_SAYFASI
    assert not sayfa & AYRAC
    assert not sayfa & ANAHTAR_SAYFALARI
    assert max(sayfa) == SON_SORU_SAYFASI
    assert not sayfa & {1, 2, 3, 4}


def test_test_sayfalari_ardisik(anahtar: dict) -> None:
    sayfalar: dict[str, set[int]] = {}
    for x in anahtar["cevaplar"]:
        sayfalar.setdefault(x["birim"], set()).add(x["dosya"])
    for b, s in sayfalar.items():
        assert max(s) - min(s) + 1 == len(s) <= 3, b


def _girdiler(satir: str) -> list[tuple[int, str, bool]]:
    out = []
    for tok in satir.split():
        no, harf = tok.split(".")
        out.append((int(no.rstrip("?")), harf.rstrip("?"), "?" in tok))
    return out


def test_anahtar_ham_okumalardan_turetilebilir(anahtar: dict, harita: dict) -> None:
    """A ve B ayni test satirlarini okur; harf farki yalniz UYUSMAZ girdide."""
    ok = _oku(HAM_YOLU)["okumalar"]
    harf = {v: k for k, v in TUR_HARF.items()}
    a = ok["A"]
    assert [(r["tur"], r["sira"]) for r in a] == [
        (harf[t["tur"]], t["tur_sira"]) for t in harita["testler"]
    ]

    def anahtar_(r: dict) -> tuple:
        return (r["sayfa"], r["unite"], r["konu"], r["tur"], r["sira"])

    b = {anahtar_(r): r for r in ok["B"]}
    assert set(b) == {anahtar_(r) for r in a}
    cevap = {(x["birim"], x["soru"]): x for x in anahtar["cevaplar"]}
    n = tereddut = 0
    for r, t in zip(a, harita["testler"], strict=True):
        ga, gb = _girdiler(r["cevap"]), _girdiler(b[anahtar_(r)]["cevap"])
        assert (
            [g[0] for g in ga]
            == [g[0] for g in gb]
            == list(range(1, t["soru_sayisi"] + 1))
        ), t["birim"]
        assert r["sayfa"] == t["anahtar_sayfasi"], t["birim"]
        for (no, ha, qa), (_, hb, qb) in zip(ga, gb, strict=True):
            x = cevap[(t["birim"], no)]
            if (t["birim"], no) == UYUSMAZ:
                # A 'B?' / B 'D'; glif NN 5/5 ve 12x goz: B.
                assert (ha, hb, x["cevap"]) == ("B", "D", "B")
                assert x["kaynak"] == "iki_okuma(uyusmaz)+piksel+goz"
            else:
                assert ha == hb == x["cevap"], (t["birim"], no)
                beklenen = (
                    "iki_okuma(biri_tereddutlu)+piksel+goz"
                    if qa or qb
                    else "iki_okuma+piksel"
                )
                assert x["kaynak"] == beklenen, (t["birim"], no)
                tereddut += bool(qa or qb)
            n += 1
    assert n == BEKLENEN_SORU
    assert tereddut == KAYNAK_DAGILIMI["iki_okuma(biri_tereddutlu)+piksel+goz"]


def test_konu_haritasi_bant_okumasindan(harita: dict) -> None:
    """Her test sayfasinin ust bandi testin turunu ve sirasini basar."""
    bant = {r["sayfa"]: r for r in _oku(HAM_YOLU)["bant_okumasi"]}
    konu = {k["kod"]: k for k in harita["konular"]}
    unite = {u["kod"]: u for u in harita["uniteler"]}
    esle = harita["bant_esleme"]
    for t in harita["testler"]:
        for s in t["sayfalar"]:
            r = bant[s]
            assert (TUR_HARF[r["tur"]], r["sira"]) == (t["tur"], t["tur_sira"]), s
            if r["konu"] == "-":  # devam sayfasi bandi basligi basmayabilir
                continue
            baslik = esle.get(r["konu"], r["konu"])
            if t["tur"] in KONU_TURLERI:
                assert baslik == konu[t["konu"]]["ad_ascii"], s
            else:
                # Karma / Orijinal / Genel Bakis bandi unite adini serbest
                # kisaltmayla basar ('... EDEBIYAT'A SIIR'); tam ad kiyaslanmaz,
                # yalniz basligin ilk kelimesi unite adinda gecer.
                assert baslik.split()[0] in unite[t["unite"]]["ad_ascii"], s
    kapsanan = {s for t in harita["testler"] for s in t["sayfalar"]}
    bos = {s for s, r in bant.items() if r["tur"] == "-"}
    assert bos == AYRAC
    assert set(bant) - bos == kapsanan


# ------------------------------------------------------- 2. konu haritasi


def test_harita_sayilari(harita: dict) -> None:
    assert harita["unite_sayisi"] == len(harita["uniteler"]) == BEKLENEN_UNITE
    assert harita["konu_sayisi"] == len(harita["konular"]) == BEKLENEN_KONU
    assert harita["test_sayisi"] == len(harita["testler"]) == BEKLENEN_TEST
    assert sum(t["soru_sayisi"] for t in harita["testler"]) == BEKLENEN_SORU
    assert {u["ayrac_sayfasi"] for u in harita["uniteler"]} == AYRAC


def test_konu_araliklari_sirali_ve_ayraci_atliyor(harita: dict) -> None:
    kon = harita["konular"]
    for a, b in itertools.pairwise(kon):
        assert b["ilk_sayfa"] > a["son_sayfa"], (a["kod"], b["kod"])
    for k in kon:
        assert not (set(range(k["ilk_sayfa"], k["son_sayfa"] + 1)) & AYRAC), k["kod"]
        assert k["kod"] == f"EDB-345A25-U{k['unite']:02d}-{k['sira']:02d}", k["kod"]


def _unite_araligi(harita: dict) -> dict[str, tuple[int, int]]:
    u = sorted(harita["uniteler"], key=lambda x: x["no"])
    son = [x["ayrac_sayfasi"] - 1 for x in u[1:]] + [SON_SORU_SAYFASI]
    return {x["kod"]: (x["ayrac_sayfasi"] + 1, s) for x, s in zip(u, son, strict=True)}


def test_her_test_tek_araligin_icinde(harita: dict) -> None:
    """Kazanim Odakli / OSYM Tadinda: konu araligi; digerleri: unite araligi."""
    aralik = {k["kod"]: (k["ilk_sayfa"], k["son_sayfa"]) for k in harita["konular"]}
    aralik |= _unite_araligi(harita)
    for t in harita["testler"]:
        duzey = "konu" if t["tur"] in KONU_TURLERI else "unite"
        assert t["eslesme_duzeyi"] == duzey, t["birim"]
        assert (t["konu"] == t["unite"]) == (duzey == "unite"), t["birim"]
        assert t["konu"].startswith(t["unite"]), t["birim"]
        bas, son = aralik[t["konu"]]
        assert bas <= min(t["sayfalar"]) and max(t["sayfalar"]) <= son, t["birim"]


def test_tur_dagilimi_ve_sira(harita: dict) -> None:
    t = harita["testler"]
    assert dict(Counter(x["tur"] for x in t)) == TUR_TEST
    soru: Counter[str] = Counter()
    for x in t:
        soru[x["tur"]] += x["soru_sayisi"]
    assert dict(soru) == TUR_SORU
    sayac: dict[tuple[str, str], int] = {}
    for x in t:
        a = (x["konu"], x["tur"])
        assert x["tur_sira"] == sayac.get(a, 0) + 1, x["birim"]
        sayac[a] = x["tur_sira"]
    assert {x["konu"] for x in t if x["tur"] == "kazanim_odakli"} == {
        k["kod"] for k in harita["konular"]
    }
    # Genel Bakis testleri yalniz unite 10'da; unite 10'un konusu yok.
    assert {x["unite"] for x in t if x["tur"] == "genel_bakis"} == {"EDB-345A25-U10"}
    assert not [k for k in harita["konular"] if k["unite"] == BEKLENEN_UNITE]


def test_harita_anahtarla_ayni_testleri_goruyor(harita: dict, anahtar: dict) -> None:
    say = Counter(x["birim"] for x in anahtar["cevaplar"])
    assert {t["birim"]: t["soru_sayisi"] for t in harita["testler"]} == dict(say)


# ----------------------------------------------------------- 3. capa / kutu


def test_tarama_toplamlari(tarama: dict) -> None:
    s = tarama["sayfalar"]
    assert len(s) == ICERIK_SAYFA
    assert (
        tarama["simge_toplam"]
        == sum(len(v["simge"]) for v in s.values())
        == SIMGE_TOPLAM
    )
    assert (
        tarama["numara_toplam"]
        == sum(len(v["numara"]["L"]) + len(v["numara"]["R"]) for v in s.values())
        == NUMARA_TOPLAM
    )


def test_capa_kanali_numara_sayisiyla_birebir(
    kutu: dict, tarama: dict, anahtar: dict
) -> None:
    """'numara' kanali: dar numara sayisi == sutunun soru sayisi; digerlerinde degil."""
    say = Counter((x["dosya"], x["sutun"]) for x in anahtar["cevaplar"])
    kanal: dict[tuple[int, str], str] = {}
    for k in kutu["kutular"]:
        kanal[(k["dosya"], k["sutun"])] = k["capa_kanali"]
    assert dict(Counter(kanal.values())) == kutu["sutun_kanali"] == SUTUN_KANALI
    for (d, t), kan in kanal.items():
        num = [
            n
            for n in tarama["sayfalar"][str(d)]["numara"][t]
            if n[3] - n[2] <= NUMARA_EN_GENIS
        ]
        if kan == "numara":
            assert len(num) == say[(d, t)], (d, t)
        else:
            assert len(num) != say[(d, t)], (d, t)


def test_kutular_kartta(kutu: dict) -> None:
    assert kutu["kutu_sayisi"] == len(kutu["kutular"]) == BEKLENEN_SORU
    assert kutu["kutusuz_soru"] == 0
    for k in kutu["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k
        assert y1 <= SAYFA_ALTI, k
        assert y0 <= k["capa"][0] < y1, k


def test_kutular_cakismiyor_ve_sonraki_capayi_yutmuyor(kutu: dict) -> None:
    grup: dict[tuple, list] = {}
    for k in kutu["kutular"]:
        grup.setdefault((k["dosya"], k["sutun"]), []).append(k)
    for g in grup.values():
        g.sort(key=lambda k: k["kutu"][1])
        assert [k["serit_sira"] for k in g] == list(range(len(g)))
        for a, b in itertools.pairwise(g):
            assert a["kutu"][3] < b["kutu"][1], (a, b)
            assert a["kutu"][3] < b["capa"][0], (a, b)


def test_kutu_ozeti_gercek(kutu: dict) -> None:
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutu["kutular"])
    assert kutu["yukseklik"] == {
        "min": yuk[0],
        "medyan": yuk[len(yuk) // 2],
        "max": yuk[-1],
    }
    assert kutu["kesim_metne_degen_kutu"] == KESIM
    assert kutu["ust_kurali_sayaci"] == UST_KURALI
    assert sum(1 for x in kutu["kutular"] if x["numara_disk_ortulu"]) == (
        DISK_ORTULU_KUTU
    )


def test_ortak_metin_kutulari_ilk_sorunun_ustunde(kutu: dict) -> None:
    """Kirmizi baslikli parca sutunun ilk sorusunun ustunde; soru kutusu icinde yok."""
    o = kutu["ortak_metinler"]
    assert len(o) == BEKLENEN_ORTAK
    assert kutu["soru_kutusu_icinde_ortak_baslik"] == []
    ilk = {}
    for k in kutu["kutular"]:
        if k["serit_sira"] == 0:
            ilk[(k["dosya"], k["sutun"])] = k
    for x in o:
        q = ilk[(x["dosya"], x["sutun"])]
        assert (q["birim"], q["soru"]) == (
            x["ilk_soru"]["birim"],
            x["ilk_soru"]["soru"],
        ), x["ortak"]
        assert x["kutu"][0] == q["kutu"][0] and x["kutu"][2] == q["kutu"][2]
        assert x["kutu"][1] < x["baslik"][0] < x["baslik"][1] < x["kutu"][3]
        assert x["kutu"][3] == q["kutu"][1] - 1, x["ortak"]
        assert x["ortak"] == f"EDB345AYT-O{x['dosya']:03d}{x['sutun']}"


# ----------------------------------------------------------------- 4. ortme


def test_ortme_olcumu_tam_kitap(ortme: dict) -> None:
    assert ortme["tam_kitap"] is True
    assert ortme["kenar_kapisi_ihlali"] == len(ortme["kenar"]) == len(KENAR)
    assert sorted((k["birim"], k["soru"]) for k in ortme["kenar"]) == KENAR
    assert all(k["sag"] == 0 for k in ortme["kenar"])
    sorular = {(o["birim"], o["soru"]) for o in ortme["ortme"]}
    assert ortme["ortme_suphesi_soru"] == len(sorular) == ORTME_SORU


# ----------------------------------------------------------------- 5. metin


def test_metin_her_kirpima_bir_kayit(metin: dict, kutu: dict) -> None:
    s = metin["sorular"]
    assert metin["soru_sayisi"] == len(s) == BEKLENEN_SORU
    assert {x["dosya"] for x in s} == {
        f"{k['birim']}_{k['soru']:02d}" for k in kutu["kutular"]
    }


def test_metin_basili_numara_test_ici_sira(metin: dict) -> None:
    """Okuyucuya sira soylenmedi; basili numara capayi bagimsiz dogrular.

    Bu kitapta numarasi diskin altinda kalan 18 kutunun hepsinde numara
    okundu; bos numara yok.
    """
    for s in metin["sorular"]:
        assert s["basili_no"] == int(s["dosya"].rsplit("_", 1)[1]), s["dosya"]


def test_metin_bes_sik_dolu_ve_cevapsiz(metin: dict) -> None:
    yasak = {"cevap", "dogru_cevap", "correct_answer", "answer", "anahtar"}
    for s in metin["sorular"]:
        assert set(s["sikler"]) == set("ABCDE"), s["dosya"]
        assert all(str(s["sikler"][h]).strip() for h in "ABCDE"), s["dosya"]
        assert not (set(s) & yasak), s["dosya"]
    assert "cozulmedi" in metin["nereden"]


def test_metin_olculen_capalar(metin: dict) -> None:
    s = metin["sorular"]
    assert sum(1 for x in s if x["sekil_var"]) == SEKILLI
    assert (
        sum(1 for x in s if all("rsel" in v for v in x["sikler"].values()))
        == GORSEL_SIKLI
    )
    assert sum(1 for x in s if x.get("kaynak_kusuru")) == KUSURLU
    assert sum(1 for x in s if x.get("etiket")) == ETIKETLI
    assert sum(1 for x in s if x["okuma"].startswith("duzeltme")) == DUZELTME_OKUMASI


def test_ortak_metinler_kapsami_testte(metin: dict, kutu: dict) -> None:
    """Basliktaki kapsamin ilk sorusu == kutudaki ilk soru; kapsam testin icinde."""
    ku = {x["ortak"]: x for x in kutu["ortak_metinler"]}
    o = metin["ortak_metinler"]
    assert metin["ortak_metin_sayisi"] == len(o) == BEKLENEN_ORTAK
    assert {x["ortak"] for x in o} == set(ku)
    sorular = {x["dosya"] for x in metin["sorular"]}
    n = 0
    for x in o:
        ilk = ku[x["ortak"]]["ilk_soru"]
        a, b = x["kapsam"]
        assert a == ilk["soru"] and a < b, x["ortak"]
        for i in range(a, b + 1):
            assert f"{ilk['birim']}_{i:02d}" in sorular, x["ortak"]
        assert x["metin"].strip() and "sorular" in x["baslik"].lower().replace(
            "\u0131", "i"
        ), x["ortak"]
        n += b - a + 1
    assert n == ORTAK_KAPSANAN


def test_mukerrer_adaylari_isaretli_silinmedi() -> None:
    m = _oku(MUKERRER_YOLU)
    guclu = [a for a in m["adaylar"] if a["ayni_sik_sayisi"] >= 3]
    assert m["guclu_aday_sayisi"] == len(guclu) == GUCLU_MUKERRER


# ---------------------------------------------------------- 6. ikinci okuma


def test_ikinci_okuma_hukmu_on_kayitla_tutarli(metin: dict) -> None:
    """Esasli hata sayisindan Clopper-Pearson ust siniri ve karar yeniden uretilir."""
    beta = pytest.importorskip("scipy.stats").beta
    k = _oku(IKINCI_YOLU)
    h = k["orneklem_hukmu"]
    assert len(k["on_kayit"]["orneklem_listesi"]) == h["orneklem"] == 224
    assert h["ayni"] + h["yalniz_noktalama"] + h["farkli"] == h["orneklem"]
    hk = h["hukumler"]
    assert sum(len(v) for v in hk.values()) == h["farkli"]
    x = h["esasli_hata"]
    assert x == 0
    ust = float(beta.ppf(0.975, x + 1, h["orneklem"] - x))
    assert round(ust, 4) == h["cp95_ust_sinir"]
    assert h["karar"] == (
        "TAM_IKINCI_OKUMA_YOK" if ust <= 0.03 else "HEDEFLI_IKINCI_OKUMA"
    )
    # esasli sayilmayan ilk okuma hatalari da ithal oncesi duzeltildi
    by = {s["dosya"]: s for s in metin["sorular"]}
    for ad in hk["ilk_okuma_hatasi"]:
        assert by[f"EDB345AYT-{ad}"]["okuma"].startswith("duzeltme"), ad


# ------------------------------------------------------------------ 7. ASCII


@pytest.mark.parametrize(
    "yol",
    [
        ANAHTAR_YOLU,
        HARITA_YOLU,
        TARAMA_YOLU,
        KUTU_YOLU,
        ORTME_YOLU,
        METIN_YOLU,
        MUKERRER_YOLU,
        HAM_YOLU,
        IKINCI_YOLU,
    ],
    ids=lambda p: p.name,
)
def test_ciktilar_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name
