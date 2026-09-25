"""345 2025 Paragraf Sifir Risk veri hattinin koruma testleri.

Canli DB istemez, sayfa goruntusu istemez; depodaki olcum dosyalarini okur --
CI'da koser. Her test OLCULEN bir capayi civiler; bir capa degisirse once
olculur, sonra burada guncellenir.

NE KORUR
--------
1. CEVAP ANAHTARI  -- 1012 cevap, 85 test, okuma kanallari, numara
                      surekliligi, ham okumalardan (A/B) turetilebilirlik.
2. KONU HARITASI   -- 7 bolum (ayrac sayfalari), her test tek bolum
                      araliginda, bant okumasiyla ayni.
3. CAPA / KUTU     -- sutun kanali, kutular kartta / cakismasiz / sayfa alti
                      siniri, ortak metin kutulari, sahipsiz murekkep kapisi.
4. ORTME           -- olcum tam kitap, kenar kapisi temiz.
5. METIN           -- 1012 kayit, basili numara == test ici sira (gorunmeyen
                      2 haric), bes sik, cevap alani yok; 30 ortak metin.
6. MUKERRER        -- GUCLU adaylar ve eski hat satirlari (cevaplar ayni).
7. IKINCI OKUMA    -- on kayit + orneklem hukmu + tam ikinci okuma kaydi.
8. ASCII           -- depo ciktilari ASCII.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_paragraf_"
ANAHTAR_YOLU = CIKTI / f"{ON}cevap_anahtari.json"
HARITA_YOLU = CIKTI / f"{ON}konu_haritasi.json"
TARAMA_YOLU = CIKTI / f"{ON}capa_taramasi.json"
KUTU_YOLU = CIKTI / f"{ON}kirpim_kutulari.json"
ORTME_YOLU = CIKTI / f"{ON}ortme_olcumu.json"
METIN_YOLU = CIKTI / f"{ON}metin.json"
MUKERRER_YOLU = CIKTI / f"{ON}mukerrer_adaylari.json"
HAM_YOLU = CIKTI / f"{ON}ham_okumalar.json"
IKINCI_YOLU = CIKTI / f"{ON}ikinci_okuma.json"

BEKLENEN_SORU = 1012
BEKLENEN_TEST = 85
BEKLENEN_BOLUM = 7
ICERIK_SAYFA = 355
ANAHTAR_SAYFALARI = set(range(356, 369))
KAPAK = {3, 63, 123, 183, 251, 283, 329}
BOLUM_TEST = {1: 9, 2: 9, 3: 9, 4: 11, 5: 15, 6: 22, 7: 10}
KAYNAK_DAGILIMI = {"iki_okuma": 978, "iki_okuma(biri_tereddutlu)+goz": 34}
HARF_DAGILIMI = {"A": 175, "B": 173, "C": 240, "D": 232, "E": 192}
SIMGE_TOPLAM, NUMARA_TOPLAM = 1005, 1740
SUTUN_KANALI = {"numara": 614, "numara_alt": 2, "simge": 57}
NUMARA_EN_GENIS = 12
SAYFA_ALTI = 904
KART_G, KART_Y = 742, 977
DISK_ORTULU_KUTU = 229
KESIM, KISA_BANT = 105, 8
ORTME_SORU = 250
BEKLENEN_ORTAK = 30
ORTAK_KAPSANAN = 65
# Numara gorunmuyor: T069_06 kitapta basilmamis ('18. yuzyildaki ...' ile
# baslar), T023_08 okuyucu diski altinda. Ikisinin capasi simgeden.
NUMARASIZ = {"PRG345-T023_08", "PRG345-T069_06"}
SEKILLI, KUSURLU, ETIKETLI, BULANIK = 16, 143, 84, 8
DUZELTME_OKUMASI = 71
GUCLU_MUKERRER, ESKI_HAT = 11, 8
# OSYM Cikmis Sorular Ozel Denemesi (s242-250) bandinda bolum adi basilmaz.
BANTSIZ_TEST_SAYFASI = 9


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return _oku(ANAHTAR_YOLU)


@pytest.fixture(scope="module")
def harita() -> dict:
    return _oku(HARITA_YOLU)


@pytest.fixture(scope="module")
def kutu() -> dict:
    return _oku(KUTU_YOLU)


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


def test_soru_sayfalari_kapak_ve_anahtar_disinda(anahtar: dict) -> None:
    sayfa = {x["dosya"] for x in anahtar["cevaplar"]}
    assert not sayfa & KAPAK
    assert not sayfa & ANAHTAR_SAYFALARI
    assert max(sayfa) <= ICERIK_SAYFA
    # '6. NUANS TESTI' (s340-343) acik uclu, anahtarda yok -> kapsam disi.
    assert not sayfa & {340, 341, 342, 343}


def _girdiler(satir: str) -> list[tuple[int, str, bool]]:
    out = []
    for tok in satir.split():
        no, harf = tok.split(".")
        out.append((int(no.rstrip("?")), harf.rstrip("?"), "?" in tok))
    return out


def test_anahtar_ham_okumalardan_turetilebilir(anahtar: dict, harita: dict) -> None:
    """A ve B ayni 85 test satirini okur; harf farki 0; '?' -> tereddutlu kanal."""
    ok = _oku(HAM_YOLU)["okumalar"]
    a, b = ok["A"], ok["B"]
    assert [(r["sayfa"], r["test"]) for r in a] == [
        (t["anahtar_sayfasi"], t["test_adi"]) for t in harita["testler"]
    ]
    bb = {(r["sayfa"], r["test"]): r for r in b}
    assert set(bb) == {(r["sayfa"], r["test"]) for r in a}
    cevap = {(x["birim"], x["soru"]): x for x in anahtar["cevaplar"]}
    n = tereddut = 0
    for r, t in zip(a, harita["testler"], strict=True):
        ga, gb = _girdiler(r["cevap"]), _girdiler(bb[(r["sayfa"], r["test"])]["cevap"])
        assert (
            [g[0] for g in ga]
            == [g[0] for g in gb]
            == list(range(1, t["soru_sayisi"] + 1))
        ), t["birim"]
        for (no, ha, qa), (_, hb, qb) in zip(ga, gb, strict=True):
            x = cevap[(t["birim"], no)]
            assert ha == hb == x["cevap"], (t["birim"], no)
            beklenen = "iki_okuma(biri_tereddutlu)+goz" if qa or qb else "iki_okuma"
            assert x["kaynak"] == beklenen, (t["birim"], no)
            tereddut += bool(qa or qb)
            n += 1
    assert n == BEKLENEN_SORU
    assert tereddut == KAYNAK_DAGILIMI["iki_okuma(biri_tereddutlu)+goz"]


# ------------------------------------------------------- 2. konu haritasi


def test_harita_sayilari(harita: dict, anahtar: dict) -> None:
    assert harita["bolum_sayisi"] == len(harita["bolumler"]) == BEKLENEN_BOLUM
    assert harita["test_sayisi"] == len(harita["testler"]) == BEKLENEN_TEST
    assert sum(t["soru_sayisi"] for t in harita["testler"]) == BEKLENEN_SORU
    assert {b["kapak_sayfasi"] for b in harita["bolumler"]} == KAPAK
    say = Counter(x["birim"] for x in anahtar["cevaplar"])
    assert {t["birim"]: t["soru_sayisi"] for t in harita["testler"]} == dict(say)


def test_her_test_tek_bolum_araliginda(harita: dict) -> None:
    b = sorted(harita["bolumler"], key=lambda x: x["no"])
    son = [x["kapak_sayfasi"] - 1 for x in b[1:]] + [ICERIK_SAYFA]
    aralik = {
        x["kod"]: (x["kapak_sayfasi"] + 1, s) for x, s in zip(b, son, strict=True)
    }
    for x in b:
        assert x["kod"] == f"TUR-345P25-B{x['no']:02d}"
    sayac: Counter[int] = Counter()
    for t in harita["testler"]:
        bas, sn = aralik[t["bolum"]]
        assert bas <= min(t["sayfalar"]) and max(t["sayfalar"]) <= sn, t["birim"]
        s = sorted(t["sayfalar"])
        assert s == list(range(s[0], s[-1] + 1)), t["birim"]
        sayac[int(t["bolum"][-2:])] += 1
    assert dict(sayac) == BOLUM_TEST


def test_harita_bant_okumasiyla_ayni(harita: dict) -> None:
    """Test sayfalarinin ust bandi testin bolumunu basar; kapaklar bossuz."""
    bant = {r["sayfa"]: r for r in _oku(HAM_YOLU)["bant_okumasi"]}
    assert set(bant) == set(range(3, ICERIK_SAYFA + 1))
    ad = {b["kod"]: b["ad_ascii"] for b in harita["bolumler"]}
    bossuz = 0
    for t in harita["testler"]:
        for s in t["sayfalar"]:
            if bant[s]["bolum"] == "-":  # bandinda bolum adi basilmayan sayfa
                bossuz += 1
                continue
            assert bant[s]["bolum"] == ad[t["bolum"]], (t["birim"], s)
    assert bossuz == BANTSIZ_TEST_SAYFASI
    assert {s for s, r in bant.items() if r["tur"] == "KAPAK"} == KAPAK


# ----------------------------------------------------------- 3. capa / kutu


def test_tarama_toplamlari() -> None:
    t = _oku(TARAMA_YOLU)
    s = t["sayfalar"]
    assert len(s) == ICERIK_SAYFA
    assert t["simge_toplam"] == sum(len(v["simge"]) for v in s.values()) == SIMGE_TOPLAM
    assert (
        t["numara_toplam"]
        == sum(len(v["numara"]["L"]) + len(v["numara"]["R"]) for v in s.values())
        == NUMARA_TOPLAM
    )


def test_capa_kanali_numara_sayisiyla_birebir(kutu: dict, anahtar: dict) -> None:
    """'numara' kanali: dar numara sayisi == sutunun soru sayisi."""
    tarama = _oku(TARAMA_YOLU)["sayfalar"]
    say = Counter((x["dosya"], x["sutun"]) for x in anahtar["cevaplar"])
    kanal = {(k["dosya"], k["sutun"]): k["capa_kanali"] for k in kutu["kutular"]}
    assert dict(Counter(kanal.values())) == kutu["sutun_kanali"] == SUTUN_KANALI
    for (d, t), kan in kanal.items():
        num = [n for n in tarama[str(d)]["numara"][t] if n[3] - n[2] <= NUMARA_EN_GENIS]
        if kan == "numara":
            # Ortak baslik icindeki '1 - 2.' rakamlari capa sayilmaz.
            assert len(num) >= say[(d, t)], (d, t)
        elif kan == "numara_alt":
            assert len(num) > say[(d, t)], (d, t)


def test_kutular_kartta_ve_sayfa_altinda(kutu: dict) -> None:
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
    assert len(kutu["kesim_metne_degen_kutu"]) == KESIM
    assert len(kutu["kisa_bant_kutu"]) == KISA_BANT
    assert sum(1 for x in kutu["kutular"] if x["numara_disk_ortulu"]) == (
        DISK_ORTULU_KUTU
    )


def test_ortak_metin_kutulari(kutu: dict) -> None:
    """Ortak kutu basligin ustunden altindaki ilk soru kutusunun ustune kadar."""
    o = kutu["ortak_metinler"]
    assert len(o) == BEKLENEN_ORTAK
    assert kutu["soru_kutusu_icinde_ortak_baslik"] == []
    by = {(k["birim"], k["soru"]): k for k in kutu["kutular"]}
    for x in o:
        q = by[(x["ilk_soru"]["birim"], x["ilk_soru"]["soru"])]
        assert (q["dosya"], q["sutun"]) == (x["dosya"], x["sutun"]), x["ortak"]
        assert x["kutu"][0] == q["kutu"][0] and x["kutu"][2] == q["kutu"][2]
        assert x["kutu"][1] < x["baslik"][0] < x["baslik"][1] < x["kutu"][3]
        assert x["kutu"][3] == q["kutu"][1] - 1, x["ortak"]
        assert x["ortak"] == f"PRG345-O{x['dosya']:03d}{x['sutun']}{x['baslik'][0]:03d}"


def test_sahipsiz_murekkep_yalniz_test_ilk_sayfasinda(kutu: dict, harita: dict) -> None:
    """Ikinci kanal: sutun ustunde sahipsiz murekkep = kacirilmis ortak adayi."""
    ilk = {t["sayfalar"][0] for t in harita["testler"]}
    s = kutu["sutun_ustu_sahipsiz_murekkep"]
    assert s and all(int(e["sutun"][:-1]) in ilk for e in s)


# ----------------------------------------------------------------- 4. ortme


def test_ortme_olcumu_tam_kitap() -> None:
    o = _oku(ORTME_YOLU)
    assert o["tam_kitap"] is True
    assert o["kenar_kapisi_ihlali"] == len(o["kenar"]) == 0
    sorular = {(x["birim"], x["soru"]) for x in o["ortme"]}
    assert o["ortme_suphesi_soru"] == len(sorular) == ORTME_SORU


# ----------------------------------------------------------------- 5. metin


def test_metin_her_kirpima_bir_kayit(metin: dict, kutu: dict) -> None:
    s = metin["sorular"]
    assert metin["soru_sayisi"] == len(s) == BEKLENEN_SORU
    assert {x["dosya"] for x in s} == {
        f"{k['birim']}_{k['soru']:02d}" for k in kutu["kutular"]
    }


def test_metin_basili_numara_test_ici_sira(metin: dict, kutu: dict) -> None:
    """Okuyucuya sira soylenmedi; basili numara capayi bagimsiz dogrular."""
    kanal = {f"{k['birim']}_{k['soru']:02d}": k["capa_kanali"] for k in kutu["kutular"]}
    bos = {s["dosya"] for s in metin["sorular"] if s["basili_no"] is None}
    assert bos == NUMARASIZ
    assert all(kanal[d] == "simge" for d in bos)
    for s in metin["sorular"]:
        if s["dosya"] not in bos:
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
    assert sum(1 for x in s if x.get("kaynak_kusuru")) == KUSURLU
    assert sum(1 for x in s if x.get("etiket")) == ETIKETLI
    assert sum(1 for x in s if "[bulan\u0131k metin]" in x["govde"]) == BULANIK
    assert sum(1 for x in s if x["okuma"].startswith("duzeltme")) == DUZELTME_OKUMASI
    assert not any(" </u>" in x["govde"] for x in s)


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
        assert x["metin"].strip(), x["ortak"]
        n += b - a + 1
    assert n == ORTAK_KAPSANAN


# -------------------------------------------------------------- 6. mukerrer


def test_mukerrer_adaylari_ve_eski_hat() -> None:
    m = _oku(MUKERRER_YOLU)
    guclu = [a for a in m["adaylar"] if a["ayni_sik_sayisi"] >= 3]
    assert m["guclu_aday_sayisi"] == len(guclu) == GUCLU_MUKERRER
    e = m["eski_hat_satirlari"]
    assert len(e) == ESKI_HAT
    # Eski hattin 8 satirinin hepsi ayni basili sayfada ve cevabi basili anahtarla ayni.
    assert all(x["cevap_ayni"] and x["db_sayfa"] == x["kitap_sayfa"] for x in e)


# ---------------------------------------------------------- 7. ikinci okuma


def test_ikinci_okuma_on_kayit_ve_karar(metin: dict) -> None:
    """Esasli hata sayisindan tek yanli CP95 ust siniri ve karar yeniden uretilir."""
    beta = pytest.importorskip("scipy.stats").beta
    k = _oku(IKINCI_YOLU)
    n = len(k["on_kayit"]["orneklem_listesi"])
    h = k["orneklem_hukmu"]
    assert n == h["okundu"] == 200
    assert h["ayni"] + h["yalniz_noktalama"] + h["farkli"] == n
    x = h["esasli_hata"]
    assert x == len(h["hukum"]["ilk_okuma_hatasi_esasli"]) == 2
    ust = float(beta.ppf(0.95, x + 1, n - x))
    assert round(ust, 4) == h["cp95_ust"]
    assert h["karar"] == ("TAM_IKINCI_OKUMA" if ust > 0.03 else "TAM_IKINCI_OKUMA_YOK")
    assert h["karar"] == "TAM_IKINCI_OKUMA"
    assert "tam_ikinci_okuma" in k


def test_tam_ikinci_okuma_duzeltmeleri_metinde(metin: dict) -> None:
    """Tam ikinci okumanin esasli ilk okuma hatalari metne islenmis."""
    by = {s["dosya"]: s for s in metin["sorular"]}
    t = _oku(IKINCI_YOLU)["tam_ikinci_okuma"]
    hk = t["hukum"]
    assert sum(hk.values()) == t["karsilastirma"]["kelime_farki_kaydi"]
    for d in t["duzeltilen_esasli_ilk_okuma_hatasi"]:
        assert by[d]["okuma"].startswith("duzeltme"), d
    assert "1991" in by["PRG345-T057_01"]["govde"]
    assert "aktiftir" in by["PRG345-T034_02"]["sikler"]["E"]


# ------------------------------------------------------------------ 8. ASCII


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
