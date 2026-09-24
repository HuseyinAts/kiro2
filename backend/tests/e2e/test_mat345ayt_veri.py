"""345 2025 AYT Matematik veri hattinin koruma testleri.

Canli DB istemez, sayfa goruntusu istemez; depodaki olcum dosyalarini okur --
CI'da koser. Her test OLCULEN bir capayi civiler; bir capa degisirse once
olculur, sonra burada guncellenir.

NE KORUR
--------
1. CEVAP ANAHTARI  -- 1942 cevap, 187 test, okuma kanallari, numara surekliligi.
2. KONU HARITASI   -- 6 bolum / 15 konu (icindekiler), 187 test tek aralikta,
                      tur ici sira kesintisiz.
3. CAPA / KUTU     -- sutun basina secilen kanalin sayisi == cevap satiri
                      girdisi; kutular kartta, cakismasiz, cevap satirina
                      sizmiyor, capayi iceriyor.
4. ORTME           -- olcum tam kitap, kenar kapisi temiz.
5. METIN           -- 1942 kayit, basili numara == test ici sira (istisna:
                      numarasi okuyucu diski altinda), bes sik, cevap alani
                      yok; kusur notu normalizasyonu kayitli ve uygulanmis.
6. ASCII           -- depo ciktilari ASCII.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_ayt_matematik_"
ANAHTAR_YOLU = CIKTI / f"{ON}cevap_anahtari.json"
HARITA_YOLU = CIKTI / f"{ON}konu_haritasi.json"
TARAMA_YOLU = CIKTI / f"{ON}capa_taramasi.json"
KUTU_YOLU = CIKTI / f"{ON}kirpim_kutulari.json"
ORTME_YOLU = CIKTI / f"{ON}ortme_olcumu.json"
METIN_YOLU = CIKTI / f"{ON}metin.json"
MUKERRER_YOLU = CIKTI / f"{ON}mukerrer_adaylari.json"
HAM_YOLU = CIKTI / f"{ON}ham_okumalar.json"
NORM_YOLU = CIKTI / f"{ON}kusur_normalizasyonu.json"

BEKLENEN_SORU = 1942
BEKLENEN_TEST = 187
BEKLENEN_BOLUM, BEKLENEN_KONU = 6, 15
SORU_SAYFASI = 374
TOPLAM_SAYFA = 384
AYRAC = {5, 97, 155, 185, 219, 361}
KAYNAK_DAGILIMI = {
    "iki_okuma+piksel": 1870,
    "iki_okuma(biri_tereddutlu)+goz": 24,
    "iki_okuma+piksel_supheli+goz": 2,
    "iki_okuma+goz(piksel_kapsam_disi)": 46,
}
HARF_DAGILIMI = {"A": 385, "B": 405, "C": 418, "D": 365, "E": 369}
TUR_TEST = {"klasiklesmis": 100, "osym_tadinda": 77, "orijinal": 10}
TUR_SORU = {"klasiklesmis": 1311, "osym_tadinda": 575, "orijinal": 56}
BANT_KONUSUZ = 11
SIMGE_TOPLAM, NUMARA_TOPLAM = 1936, 1897
SUTUN_KANALI = {"numara": 704, "simge": 44}
SAYFA_ALTI = 896
CEVAP_SATIRI_UST = 899
KART_G, KART_Y = 742, 977
ORTME_SORU = 175
SEKILLI, GORSEL_SIKLI, KUSURLU, ETIKETLI = 581, 10, 135, 142
DUZELTME_OKUMASI = 6
NUMARASI_ORTULU = 61
# Capasi numaradan alinan ama diski numaranin ilk rakamini ortuyor (olculdu).
DISK_ORTULU_NULL = [
    "MAT345AYT-T005_15",
    "MAT345AYT-T015_14",
    "MAT345AYT-T042_04",
    "MAT345AYT-T076_16",
    "MAT345AYT-T113_06",
    "MAT345AYT-T114_04",
    "MAT345AYT-T140_08",
    "MAT345AYT-T174_04",
    "MAT345AYT-T175_03",
    "MAT345AYT-T175_06",
]
DISK_ORTULU_KUTU = 23
KUSUR_DUSURULEN = 57
GUCLU_MUKERRER = 22


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
    assert "basili cevap satirindan" in anahtar["nereden"]
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


def test_soru_sayfalari_ve_ayraclar(anahtar: dict) -> None:
    sayfa = {x["dosya"] for x in anahtar["cevaplar"]}
    assert len(sayfa) == SORU_SAYFASI
    assert not sayfa & AYRAC
    assert not sayfa & {1, 2, 3, 4}


def test_test_sayfalari_ardisik(anahtar: dict) -> None:
    sayfalar: dict[str, set[int]] = {}
    for x in anahtar["cevaplar"]:
        sayfalar.setdefault(x["birim"], set()).add(x["dosya"])
    for b, s in sayfalar.items():
        assert max(s) - min(s) + 1 == len(s) <= 3, b


def _girdiler(serit: str) -> list[tuple[int, str, bool]]:
    if serit in ("", "-"):
        return []
    out = []
    for tok in serit.split():
        no, harf = tok.split(".")
        out.append((int(no.rstrip("?")), harf.rstrip("?"), "?" in tok))
    return out


def test_anahtar_ham_okumalardan_turetilebilir(anahtar: dict) -> None:
    """Iki okuma birebir ayni (tereddut isareti haric); anahtar ve kanal etiketi onlardan."""
    ok = _oku(HAM_YOLU)["okumalar"]
    a, b = ok["A"]["serit"], ok["B"]["serit"]
    assert set(a) == set(b) and len(a) == 2 * SORU_SAYFASI
    cevap = {(x["dosya"], x["sutun"], x["serit_sira"]): x for x in anahtar["cevaplar"]}
    n = tereddut = 0
    for yarim in a:
        ga, gb = _girdiler(a[yarim]), _girdiler(b[yarim])
        assert [g[:2] for g in ga] == [g[:2] for g in gb], yarim
        for i, ((no, harf, qa), (_, _, qb)) in enumerate(zip(ga, gb, strict=True)):
            x = cevap[(int(yarim[:-1]), yarim[-1], i)]
            assert (x["soru"], x["cevap"]) == (no, harf), (yarim, i)
            if qa or qb:
                tereddut += 1
                assert x["kaynak"] == "iki_okuma(biri_tereddutlu)+goz", (yarim, i)
            n += 1
    assert n == BEKLENEN_SORU
    assert tereddut == KAYNAK_DAGILIMI["iki_okuma(biri_tereddutlu)+goz"]


def test_konu_haritasi_bant_okumasindan(harita: dict) -> None:
    bant = _oku(HAM_YOLU)["bant_okumasi"]["testler"]
    tur = {"K": "klasiklesmis", "O": "osym_tadinda", "R": "orijinal"}
    assert len(bant) == BEKLENEN_TEST
    for t in harita["testler"]:
        k, sira, konu = bant[t["birim"]]
        assert (tur[k], sira) == (t["tur"], t["tur_sira"]), t["birim"]
        assert (None if konu == "-" else konu) == t["bant_konu"], t["birim"]


# ------------------------------------------------------- 2. konu haritasi


def test_harita_sayilari(harita: dict) -> None:
    assert harita["bolum_sayisi"] == len(harita["bolumler"]) == BEKLENEN_BOLUM
    assert harita["konu_sayisi"] == len(harita["konular"]) == BEKLENEN_KONU
    assert harita["test_sayisi"] == len(harita["testler"]) == BEKLENEN_TEST
    assert sum(t["soru_sayisi"] for t in harita["testler"]) == BEKLENEN_SORU


def test_bolum_adi_uydurulmadi(harita: dict) -> None:
    for b in harita["bolumler"]:
        assert b["ad"] == f"B\u00f6l\u00fcm {b['no']:02d}", b
        assert b["ayrac_sayfasi"] in AYRAC
    assert "uydurulmadi" in harita["nereden"]


def test_konu_araliklari_sirali_ve_ayraci_atliyor(harita: dict) -> None:
    kon = harita["konular"]
    for a, b in itertools.pairwise(kon):
        assert b["ilk_sayfa"] > a["son_sayfa"], (a["kod"], b["kod"])
        assert b["ilk_sayfa"] - a["son_sayfa"] in (1, 2), (a["kod"], b["kod"])
    for k in kon:
        assert not (set(range(k["ilk_sayfa"], k["son_sayfa"] + 1)) & AYRAC), k["kod"]
        assert k["kod"].startswith(f"MAT-345A25-B{k['bolum']:02d}-")


def test_her_test_tek_konu_araliginda(harita: dict) -> None:
    aralik = {k["kod"]: (k["ilk_sayfa"], k["son_sayfa"]) for k in harita["konular"]}
    for t in harita["testler"]:
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
    assert sum(1 for x in t if x["bant_konu"] is None) == BANT_KONUSUZ


def test_harita_anahtarla_ayni_testleri_goruyor(harita: dict, anahtar: dict) -> None:
    say = Counter(x["birim"] for x in anahtar["cevaplar"])
    assert {t["birim"]: t["soru_sayisi"] for t in harita["testler"]} == dict(say)


# ----------------------------------------------------------- 3. capa / kutu


def test_tarama_toplamlari(tarama: dict) -> None:
    s = tarama["sayfalar"]
    assert len(s) == TOPLAM_SAYFA
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


def test_capa_kanali_cevap_satiriyla_birebir(
    kutu: dict, tarama: dict, anahtar: dict
) -> None:
    """Kutunun capasi, sayisi o sutunun cevap satiri girdi sayisina esit olan kanal."""
    say = Counter((x["dosya"], x["sutun"]) for x in anahtar["cevaplar"])
    kanal: dict[tuple[int, str], str] = {}
    for k in kutu["kutular"]:
        kanal[(k["dosya"], k["sutun"])] = k["capa_kanali"]
    assert dict(Counter(kanal.values())) == kutu["sutun_kanali"] == SUTUN_KANALI
    for (d, t), kan in kanal.items():
        s = tarama["sayfalar"][str(d)]
        if kan == "numara":
            assert len(s["numara"][t]) == say[(d, t)], (d, t)
        else:
            assert len(s["numara"][t]) != say[(d, t)], (d, t)


def test_kutular_kartta_ve_cevap_satirina_sizmiyor(kutu: dict) -> None:
    assert kutu["kutu_sayisi"] == len(kutu["kutular"]) == BEKLENEN_SORU
    assert kutu["kutusuz_soru"] == 0
    for k in kutu["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k
        assert y1 <= SAYFA_ALTI < CEVAP_SATIRI_UST, k
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


def test_kesim_metne_degen_kutular_civili(kutu: dict) -> None:
    """Ust kesimi +-3 satirda metne degen 4 kutu gozle incelendi (bkz. yontem notu).

    Dordu de OSYM kosesi logosunun hemen ustunde; kesim onceki sorunun secenek
    satirinin 2 px altinda (logo_yakin_secenek kurali 3 kutuda uygulandi).
    """
    assert kutu["kesim_metne_degen_kutu"] == [
        "MAT345AYT-T114_05",
        "MAT345AYT-T143_06",
        "MAT345AYT-T157_11",
        "MAT345AYT-T165_07",
    ]
    assert kutu["ust_kurali_sayaci"] == {"logo": 139, "logo_yakin_secenek": 3}


# ----------------------------------------------------------------- 4. ortme


def test_ortme_olcumu_tam_kitap(ortme: dict) -> None:
    assert ortme["tam_kitap"] is True
    assert ortme["kenar_kapisi_ihlali"] == len(ortme["kenar"]) == 0
    sorular = {(o["birim"], o["soru"]) for o in ortme["ortme"]}
    assert ortme["ortme_suphesi_soru"] == len(sorular) == ORTME_SORU


# ----------------------------------------------------------------- 5. metin


def test_metin_her_kirpima_bir_kayit(metin: dict, kutu: dict) -> None:
    s = metin["sorular"]
    assert metin["soru_sayisi"] == len(s) == BEKLENEN_SORU
    assert {x["dosya"] for x in s} == {
        f"{k['birim']}_{k['soru']:02d}" for k in kutu["kutular"]
    }


def test_metin_basili_numara_test_ici_sira(metin: dict, kutu: dict) -> None:
    """Okuyucuya sira soylenmedi; basili numara capayi bagimsiz dogrular.

    Numara yalniz okuyucu diski altindaysa bos olabilir: capasi simgeden
    alinan kutu ya da diskin numarayi ortugu olculen kutu (numara_disk_ortulu).
    """
    k = {f"{x['birim']}_{x['soru']:02d}": x for x in kutu["kutular"]}
    assert (
        sum(1 for x in kutu["kutular"] if x["numara_disk_ortulu"]) == DISK_ORTULU_KUTU
    )
    assert all(
        x["capa_kanali"] == "numara" for x in kutu["kutular"] if x["numara_disk_ortulu"]
    )
    ortulu, disk = [], []
    for s in metin["sorular"]:
        if s["basili_no"] is None:
            x = k[s["dosya"]]
            assert x["capa_kanali"] == "simge" or x["numara_disk_ortulu"], s["dosya"]
            ortulu.append(s["dosya"])
            if x["capa_kanali"] != "simge":
                disk.append(s["dosya"])
        else:
            assert s["basili_no"] == int(s["dosya"].rsplit("_", 1)[1]), s["dosya"]
    assert len(ortulu) == NUMARASI_ORTULU
    assert disk == DISK_ORTULU_NULL


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


def test_kusur_normalizasyonu_kayitli_ve_uygulanmis(metin: dict) -> None:
    """Dusurulen her not kayitli; metinde artik yok; yalniz ilk 6 grup ya da numara-disk notu."""
    n = _oku(NORM_YOLU)
    assert n["dusurulen"] == len(n["kayitlar"]) == KUSUR_DUSURULEN
    by = {s["dosya"]: s for s in metin["sorular"]}
    ilk = {f"grup_{i:02d}" for i in range(1, 7)}
    for r in n["kayitlar"]:
        assert by[r["dosya"]]["kaynak_kusuru"] is None, r["dosya"]
        assert r["okuma"] in ilk, r["dosya"]
        assert r["neden"].startswith(
            ("soluk_ama_okunan_isaret", "numara_okuyucu_diski")
        ), r


def test_mukerrer_adaylari_isaretli_silinmedi() -> None:
    m = _oku(MUKERRER_YOLU)
    guclu = [a for a in m["adaylar"] if a["ayni_sik_sayisi"] >= 3]
    assert m["guclu_aday_sayisi"] == len(guclu) == GUCLU_MUKERRER


# ------------------------------------------------------------------ 6. ASCII


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
        NORM_YOLU,
    ],
    ids=lambda p: p.name,
)
def test_ciktilar_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name
