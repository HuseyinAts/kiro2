"""345 2025 AYT Kimya veri hattinin koruma testleri.

Canli DB istemez, sayfa goruntusu istemez; depodaki olcum dosyalarini okur --
CI'da koser. Her test OLCULEN bir capayi civiler; bir capa degisirse once
olculur, sonra burada guncellenir.

NE KORUR
--------
1. CEVAP ANAHTARI  -- 1304 cevap, 160 test, okuma kanallari, numara
                      surekliligi, ham okumalardan turetilebilirlik.
2. KONU HARITASI   -- 12 unite / 50 konu (icindekiler); Kazanim Odakli testler
                      konu, OSYM Tadinda / Orijinal testler unite araliginda;
                      tur ici sira kesintisiz; bant okumasiyla ayni.
3. CAPA / KUTU     -- sutun basina secilen kanal cevap satiriyla birebir;
                      kutular kartta, cakismasiz, cevap satirina sizmiyor.
4. ORTME           -- olcum tam kitap, kenar kapisi civili.
5. METIN           -- 1304 kayit, basili numara == test ici sira (istisna:
                      numarasi okuyucu diski altinda), bes sik, cevap alani
                      yok; iyon yuklu HER soru yuk isareti hakemliginden gecti.
6. IKINCI OKUMA    -- on kayit + orneklem hukmu + hedefli okuma kaydi tutarli.
7. ASCII           -- depo ciktilari ASCII.
"""

from __future__ import annotations

import difflib
import itertools
import json
import re
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_ayt_kimya_"
ANAHTAR_YOLU = CIKTI / f"{ON}cevap_anahtari.json"
HARITA_YOLU = CIKTI / f"{ON}konu_haritasi.json"
TARAMA_YOLU = CIKTI / f"{ON}capa_taramasi.json"
KUTU_YOLU = CIKTI / f"{ON}kirpim_kutulari.json"
ORTME_YOLU = CIKTI / f"{ON}ortme_olcumu.json"
METIN_YOLU = CIKTI / f"{ON}metin.json"
MUKERRER_YOLU = CIKTI / f"{ON}mukerrer_adaylari.json"
HAM_YOLU = CIKTI / f"{ON}ham_okumalar.json"
IKINCI_YOLU = CIKTI / f"{ON}ikinci_okuma.json"

BEKLENEN_SORU = 1304
BEKLENEN_TEST = 160
BEKLENEN_UNITE, BEKLENEN_KONU = 12, 50
SORU_SAYFASI = 316
TOPLAM_SAYFA = 336
AYRAC = {5, 39, 71, 107, 127, 151, 175, 205, 243, 265, 295, 325}
KAYNAK_DAGILIMI = {
    "iki_okuma+piksel": 1054,
    "iki_okuma(biri_tereddutlu)+goz": 211,
    "iki_okuma+goz(piksel_kapsam_disi)": 18,
    "iki_okuma+piksel_supheli+goz": 21,
}
HARF_DAGILIMI = {"A": 155, "B": 249, "C": 304, "D": 296, "E": 300}
TUR_TEST = {"kazanim_odakli": 100, "osym_tadinda": 48, "orijinal": 12}
TUR_SORU = {"kazanim_odakli": 834, "osym_tadinda": 430, "orijinal": 40}
TUR_HARF = {"K": "kazanim_odakli", "O": "osym_tadinda", "R": "orijinal"}
SIMGE_TOPLAM, NUMARA_TOPLAM = 1376, 1507
SUTUN_KANALI = {"numara": 524, "simge": 25, "birlesik": 3, "numara_alt": 1}
NUMARA_EN_GENIS = 12
UST_KURALI = {"ayrac_bandi": 95, "logo": 90, "logo_yakin_secenek": 1}
SAYFA_ALTI = 896
CEVAP_SATIRI_UST = 899
KART_G, KART_Y = 742, 977
ORTME_SORU = 94
# Kenar kapisi: kirpimin sol 2 px'inde koyu piksel; ucu de soru kutusunun
# kendi cercevesi (gozle incelendi), metin kesilmiyor.
KENAR = [("KIM345AYT-T066", 3), ("KIM345AYT-T111", 1), ("KIM345AYT-T148", 2)]
SEKILLI, GORSEL_SIKLI, KUSURLU, ETIKETLI = 544, 12, 278, 94
# 57 ilk yuk isareti hakemligi + 124 hedefli ikinci okuma (yuk isareti tabakasi).
DUZELTME_OKUMASI = 181
YUKLU_SORU = 178
NUMARASI_ORTULU = 34
# Capasi numaradan alinan ama diski numarayi ortuyor (olculdu).
DISK_ORTULU_NULL = [
    "KIM345AYT-T004_06",
    "KIM345AYT-T087_04",
    "KIM345AYT-T105_13",
    "KIM345AYT-T123_10",
    "KIM345AYT-T137_10",
    "KIM345AYT-T138_08",
    "KIM345AYT-T144_08",
]
DISK_ORTULU_KUTU = 57
GUCLU_MUKERRER = 211
ESKI = "\u2212"
# Iyon yuku: harf / ) / ] / alt indis sonrasi ^+ ^- ^(n+) ^(n-) ^? ; 10^(...) ve e^- haric,
# birim uslerinde (L^(-1)) isaretin ardindan rakam gelir -> haric.
YUK = re.compile(
    r"(?<![0-9])(?<!\b10)(?:[A-Za-z\)\]]|_\d+)\^\(?\d*[+\u2212\-'?](?!\d)\)?"
)


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
        assert max(s) - min(s) + 1 == len(s) <= 4, b


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
    """Tur ve sira bant okumasindan; K bandinin bolum no'su ve basligi konunun."""
    bant = _oku(HAM_YOLU)["bant_okumasi"]["testler"]
    assert len(bant) == BEKLENEN_TEST
    konu = {k["kod"]: k for k in harita["konular"]}
    unite = {u["kod"]: u for u in harita["uniteler"]}
    esle = harita["bant_esleme"]
    for t in harita["testler"]:
        tur, bolum, sira, baslik = bant[t["birim"]]
        assert (TUR_HARF[tur], sira) == (t["tur"], t["tur_sira"]), t["birim"]
        if tur == "K":
            k = konu[t["konu"]]
            assert bolum == k["sira"], t["birim"]
            assert esle.get(baslik, baslik) == k["ad_ascii"], t["birim"]
        elif tur == "O":
            assert esle.get(baslik, baslik) == unite[t["unite"]]["ad_ascii"], t["birim"]


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
        assert k["kod"] == f"KIM-345A25-U{k['unite']:02d}-{k['sira']:02d}", k["kod"]


def _unite_araligi(harita: dict) -> dict[str, tuple[int, int]]:
    u = sorted(harita["uniteler"], key=lambda x: x["no"])
    son = [x["ayrac_sayfasi"] - 1 for x in u[1:]] + [TOPLAM_SAYFA]
    return {x["kod"]: (x["ayrac_sayfasi"] + 1, s) for x, s in zip(u, son, strict=True)}


def test_her_test_tek_araligin_icinde(harita: dict) -> None:
    """Kazanim Odakli: konu araligi; OSYM Tadinda / Orijinal: unite araligi."""
    aralik = {k["kod"]: (k["ilk_sayfa"], k["son_sayfa"]) for k in harita["konular"]}
    aralik |= _unite_araligi(harita)
    for t in harita["testler"]:
        duzey = "konu" if t["tur"] == "kazanim_odakli" else "unite"
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
    """'numara' kanali: dar numara sayisi == cevap satiri girdisi; digerlerinde degil."""
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
    assert kutu["kesim_metne_degen_kutu"] == []
    assert kutu["ust_kurali_sayaci"] == UST_KURALI


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


def test_metin_basili_numara_test_ici_sira(metin: dict, kutu: dict) -> None:
    """Okuyucuya sira soylenmedi; basili numara capayi bagimsiz dogrular.

    Numara yalniz okuyucu diski altindaysa bos olabilir: capasi basili
    numaradan alinmayan kutu ya da diskin numarayi ortugu olculen kutu.
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
            numaradan = x["capa_kanali"] in ("numara", "numara_alt")
            assert not numaradan or x["numara_disk_ortulu"], s["dosya"]
            ortulu.append(s["dosya"])
            if numaradan:
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


def _metin(s: dict) -> str:
    return s["govde"] + "\n" + "\n".join(s["sikler"][h] for h in "ABCDE")


def _yuk_var(metin: str) -> bool:
    """Elektron gosterimi (e^-, 2e^-: 'e' oncesinde harf yok) yuk sayilmaz."""
    for m in YUK.finditer(metin):
        if (
            m.group(0).startswith("e^")
            and not metin[max(0, m.start() - 1) : m.start()].isalpha()
        ):
            continue
        return True
    return False


def test_iyon_yuklu_her_soru_isaret_hakemliginden_gecti(metin: dict) -> None:
    """'+' nin bir cizgisi sik kayboluyor; yuk tasiyan her soru hakemden gecmeli."""
    yuklu = [s for s in metin["sorular"] if _yuk_var(_metin(s))]
    assert len(yuklu) == YUKLU_SORU
    for s in yuklu:
        assert (s.get("hakem_notu") or "").startswith("yuk isareti hakemligi"), s[
            "dosya"
        ]


def test_belirsiz_yuk_isareti_notlu(metin: dict) -> None:
    """Her '?' yuk isareti icin kaynak_kusuru'nda 'yuk isareti belirsiz' notu var."""
    n = 0
    for s in metin["sorular"]:
        if re.search(r"\^\(?\d*\?", _metin(s)):
            n += 1
            kusur = (s.get("kaynak_kusuru") or "").lower().replace("\u00fc", "u")
            kusur = kusur.replace("\u015f", "s")
            assert "isareti belirsiz" in kusur, s["dosya"]
    assert n > 0


def test_mukerrer_adaylari_isaretli_silinmedi() -> None:
    m = _oku(MUKERRER_YOLU)
    guclu = [a for a in m["adaylar"] if a["ayni_sik_sayisi"] >= 3]
    assert m["guclu_aday_sayisi"] == len(guclu) == GUCLU_MUKERRER


# ---------------------------------------------------------- 6. ikinci okuma


def test_ikinci_okuma_hukmu_on_kayitla_tutarli() -> None:
    """Esasli hata sayisindan Clopper-Pearson ust siniri ve karar yeniden uretilir."""
    beta = pytest.importorskip("scipy.stats").beta
    k = _oku(IKINCI_YOLU)
    h = k["orneklem_hukmu"]
    assert len(k["on_kayit"]["orneklem_listesi"]) == h["orneklem"] == 210
    assert h["ayni"] + h["farkli"] == h["orneklem"]
    hk = h["hukumler"]
    assert sum(len(v) for v in hk.values()) == h["farkli"]
    x = len(hk["ilk_okuma_hatasi"])
    assert x == h["esasli_hata"] == 5
    ust = float(beta.ppf(0.975, x + 1, h["orneklem"] - x))
    assert round(ust, 4) == h["cp95_ust_sinir"]
    assert h["karar"] == (
        "TAM_IKINCI_OKUMA_YOK" if ust <= 0.03 else "HEDEFLI_IKINCI_OKUMA"
    )


def test_hedefli_okuma_yalniz_yuk_isaretini_degistirdi(metin: dict) -> None:
    k = _oku(IKINCI_YOLU)["hedefli_okuma"]
    assert k["metni_degisen"] == len(k["degisenler"]) == 68
    by = {s["dosya"]: s for s in metin["sorular"]}
    izin = set("+-?()" + ESKI)
    for d in k["degisenler"]:
        s = by[d["dosya"]]
        for f in d["fark"]:
            son = s["govde"] if f["alan"] == "govde" else s["sikler"][f["alan"]]
            assert son == f["sonra"], d["dosya"]
            ops = difflib.SequenceMatcher(
                None, f["once"], f["sonra"], autojunk=False
            ).get_opcodes()
            for op, i1, i2, j1, j2 in ops:
                if op != "equal":
                    assert set(f["once"][i1:i2]) <= izin, d["dosya"]
                    assert set(f["sonra"][j1:j2]) <= izin, d["dosya"]
    # orneklemin bes esasli hatasi hedefli okumada duzeldi
    for ad in _oku(IKINCI_YOLU)["orneklem_hukmu"]["hukumler"]["ilk_okuma_hatasi"]:
        assert "?" in _metin(by[f"KIM345AYT-{ad}"]), ad


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
