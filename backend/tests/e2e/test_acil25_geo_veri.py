"""ACIL 2025 KURS Geometri veri hattinin koruma testleri (Faz 1).

Canli DB istemez, sayfa goruntusu istemez; depodaki olcum dosyalarini okur --
CI'da koser. Her test OLCULEN bir capayi civiler; bir capa degisirse once
olculur, sonra burada guncellenir.

NE KORUR
--------
1. CEVAP ANAHTARI  -- 1948 cevap, uc okuma kanali, numara surekliligi.
2. KONU AGACI      -- 33 konu / 315 alt konu, adlar sayfa basligi ve sari
                      kutudan, konu sirasi geri donmuyor.
3. BIRIM HARITASI  -- 429 birim = 318 sari kutu + 111 test; birim ici
                      numara 1..N; devam kutulari.
4. CAPA / KUTU     -- sutun basina numara capasi == serit girdisi; kutular
                      kartta, cakismasiz, seride sizmiyor, numarayi iceriyor.
5. ORTME           -- olcum kirpimlara bagli; okunamayan her sik ortme
                      olcumunde de isaretli (iki bagimsiz kanal).
6. METIN           -- 1948 kayit, basili numara == birim ici sira, bes sik,
                      cevap alani yok.
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
HARITA_YOLU = CIKTI / "acil_2025_geometri_konu_haritasi.json"
BIRIM_YOLU = CIKTI / "acil_2025_geometri_birim_haritasi.json"
ANAHTAR_YOLU = CIKTI / "acil_2025_geometri_cevap_anahtari.json"
NUMARA_YOLU = CIKTI / "acil_2025_geometri_numara_taramasi.json"
SIMGE_YOLU = CIKTI / "acil_2025_geometri_simge_taramasi.json"
SARI_YOLU = CIKTI / "acil_2025_geometri_sari_kutular.json"
KUTU_YOLU = CIKTI / "acil_2025_geometri_kirpim_kutulari.json"
ORTME_YOLU = CIKTI / "acil_2025_geometri_ortme_olcumu.json"
METIN_YOLU = CIKTI / "acil_2025_geometri_metin.json"
SERIT_OKUMA_YOLU = CIKTI / "acil_2025_geometri_serit_okumalari.json"
BASLIK_OKUMA_YOLU = CIKTI / "acil_2025_geometri_baslik_okumalari.json"

KAYNAK = "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi"
ONEK = "GEO-ACL25"
BEKLENEN_SORU = 1948
BEKLENEN_KONU, BEKLENEN_ALT = 33, 315
BEKLENEN_BIRIM = 429
BIRIM_TURU = {"konu_ogrenme": 318, "test": 111}
SARI_KUTU, DEVAM_KUTUSU = 331, 13
ILK_DOSYA, SON_DOSYA = 7, 398
SUTUN_SAYISI = 2 * (SON_DOSYA - ILK_DOSYA + 1)  # 784
KAYNAK_DAGILIMI = {"uc_okuma": 1915, "iki_okuma+piksel_BD": 31, "goz_zoom": 2}
HARF_DAGILIMI = {"A": 266, "B": 361, "C": 575, "D": 460, "E": 286}
SIMGE_TOPLAM = 1963
SAYFA_ALTI = 906
SUTUNLAR = {
    "tek": {"L": [41, 351], "R": [368, 684]},
    "cift": {"L": [57, 368], "R": [384, 700]},
}
ORTME_SORU = 82
SEKILLI, GORSEL_SIKLI, KUSURLU, OKUNAMAYAN_SIK = 1692, 10, 83, 4
DUZELTME_OKUMASI = 38
SIK_OKUNAMADI = "[okunamad\u0131]"
TEKRAR_EDEN_ALT_BASLIK = 3


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def harita() -> dict:
    return _oku(HARITA_YOLU)


@pytest.fixture(scope="module")
def birim() -> dict:
    return _oku(BIRIM_YOLU)


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return _oku(ANAHTAR_YOLU)


@pytest.fixture(scope="module")
def numara() -> dict:
    return _oku(NUMARA_YOLU)


@pytest.fixture(scope="module")
def sari() -> dict:
    return _oku(SARI_YOLU)


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


def test_anahtar_her_soruya_bir_cevap(anahtar: dict, birim: dict) -> None:
    c = anahtar["cevaplar"]
    assert anahtar["toplam_cevap"] == len(c) == BEKLENEN_SORU
    beklenen = {
        (b["kod"], i) for b in birim["birimler"] for i in range(1, b["soru_sayisi"] + 1)
    }
    assert {(x["birim"], x["soru"]) for x in c} == beklenen


def test_anahtar_kaynak_ve_harf_dagilimi(anahtar: dict) -> None:
    c = anahtar["cevaplar"]
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
    assert "basili cevap seridinden" in anahtar["nereden"]
    assert "hicbir cevap uretilmedi" in anahtar["nereden"].lower()


def test_serit_numarasi_kitap_boyunca_kesintisiz(anahtar: dict) -> None:
    """Okuma sirasinda her numara ya oncekinin +1'i ya da 1 (yeni birim)."""
    sirali = sorted(
        anahtar["cevaplar"], key=lambda x: (x["dosya"], x["sutun"], x["serit_sira"])
    )
    birim_bas = 0
    for a, b in itertools.pairwise(sirali):
        if b["soru"] == 1:
            birim_bas += 1
        else:
            assert b["soru"] == a["soru"] + 1, (a, b)
            assert b["birim"] == a["birim"], (a, b)
    assert birim_bas + 1 == BEKLENEN_BIRIM


def test_bd_kanali_yalniz_b_ve_goz_kanali_yalniz_c(anahtar: dict) -> None:
    """31 tartismali girdinin hepsi B cikti (orta cubuk); 2 goz girdisi C."""
    for x in anahtar["cevaplar"]:
        if x["kaynak"] == "iki_okuma+piksel_BD":
            assert x["cevap"] == "B", x
        if x["kaynak"] == "goz_zoom":
            assert x["cevap"] == "C", x


def _girdiler(serit: str) -> list[tuple[int, str]]:
    out = []
    for tok in serit.split():
        if tok == "/":
            continue
        no, harf = tok.split(".")
        out.append((int(no), harf.rstrip("?")))
    return out


def test_anahtar_ham_okumalardan_turetilebilir(anahtar: dict) -> None:
    """Uc okuma dosyasi anahtari birebir uretir; kanal etiketi de okumadan gelir."""
    ok = _oku(SERIT_OKUMA_YOLU)
    a, b, c = (ok["okumalar"][x]["serit"] for x in "ABC")
    assert len(a) == len(b) == len(c) == SUTUN_SAYISI
    cevap = {(x["dosya"], x["sutun"], x["serit_sira"]): x for x in anahtar["cevaplar"]}
    kanal: Counter[str] = Counter()
    for anah in a:
        ga, gb, gc = _girdiler(a[anah]), _girdiler(b[anah]), _girdiler(c[anah])
        assert len(ga) == len(gb) == len(gc), anah
        for i, ((na, ha), (nb, hb), (nc, hc)) in enumerate(
            zip(ga, gb, gc, strict=True)
        ):
            assert na == nb == nc, (anah, i)
            x = cevap[(int(anah[:-1]), anah[-1], i)]
            assert x["soru"] == na, (anah, i)
            if ha == hb == hc:
                beklenen = ("uc_okuma", ha)
            elif ha == hb:
                assert {ha, hc} == {"B", "D"}, (anah, i)
                beklenen = ("iki_okuma+piksel_BD", ha)
            else:
                beklenen = ("goz_zoom", ok["goz_ile_cozulen"][f"{anah}#{i + 1}"])
            assert (x["kaynak"], x["cevap"]) == beklenen, (anah, i)
            kanal[x["kaynak"]] += 1
    assert dict(kanal) == KAYNAK_DAGILIMI


def test_baslik_ve_kutu_okumalari_tek_farkla_ayni(harita: dict) -> None:
    ok = _oku(BASLIK_OKUMA_YOLU)
    h1, h2 = ok["baslik"]["H1"], ok["baslik"]["H2"]
    assert sorted(int(k) for k in h1) == list(range(ILK_DOSYA, SON_DOSYA + 1))
    assert [k for k in h1 if h1[k] != h2[k]] == ["139"]
    k1, k2 = ok["kutu"]["K1"], ok["kutu"]["K2"]
    assert len(k1) == len(k2) == SARI_KUTU
    assert [k for k in k1 if k1[k] != k2[k]] == ["19"]
    # konu adlari ve sirasi basliklardan turetilebilir
    sira: list[str] = []
    for k in sorted(h1, key=int):
        ad = h1[k][2]
        if not sira or sira[-1] != ad:
            sira.append(ad)
    assert sira == [c["ad_basili"] for c in harita["konular"]]
    alt_adlar = {a["ad_basili"] for a in harita["alt_konular"]}
    assert alt_adlar <= {v[0] for v in k1.values()}


# ---------------------------------------------------------- 2. konu agaci


def test_agac_sayilari_ve_kimligi(harita: dict) -> None:
    assert (
        harita["kaynak"] == KAYNAK and harita["onek"] == ONEK and harita["kok"] == "GEO"
    )
    assert len(harita["konular"]) == BEKLENEN_KONU
    assert len(harita["alt_konular"]) == BEKLENEN_ALT


def test_konu_araliklari_kitabi_tam_ve_sirali_ortuyor(harita: dict) -> None:
    kon = harita["konular"]
    assert kon[0]["bas_sayfa"] == ILK_DOSYA and kon[-1]["son_sayfa"] == SON_DOSYA
    for a, b in itertools.pairwise(kon):
        assert b["bas_sayfa"] == a["son_sayfa"] + 1, (a["kod"], b["kod"])


def test_kodlar_hiyerarsik_ve_benzersiz(harita: dict) -> None:
    kodlar = [k["kod"] for k in harita["konular"]] + [
        a["kod"] for a in harita["alt_konular"]
    ]
    assert len(kodlar) == len(set(kodlar))
    konu = {k["kod"] for k in harita["konular"]}
    for a in harita["alt_konular"]:
        assert a["ust"] in konu and a["kod"].startswith(a["ust"] + "-A"), a


def test_adlar_ascii_katlanmis_basili_hali_saklanmis(harita: dict) -> None:
    for x in harita["konular"] + harita["alt_konular"]:
        assert all(ord(c) < 128 for c in x["ad"]), x["kod"]
        assert x["ad_basili"].strip(), x["kod"]


def test_bolum_duzeyi_uydurulmadi(harita: dict) -> None:
    assert "bolumler" not in harita
    assert "ACILMADI" in harita["nereden"]


# ------------------------------------------------------- 3. birim haritasi


def test_birim_sayisi_ve_turleri(birim: dict) -> None:
    b = birim["birimler"]
    assert birim["birim_sayisi"] == len(b) == BEKLENEN_BIRIM
    assert dict(Counter(x["tur"] for x in b)) == birim["tur_dagilimi"] == BIRIM_TURU
    assert sum(x["soru_sayisi"] for x in b) == BEKLENEN_SORU


def test_birim_turu_ile_alt_konu_tutarli(birim: dict, harita: dict) -> None:
    alt = {a["kod"]: a["ust"] for a in harita["alt_konular"]}
    for b in birim["birimler"]:
        if b["tur"] == "konu_ogrenme":
            assert alt[b["alt_konu"]] == b["konu"], b["kod"]
        else:
            assert b["alt_konu"] is None and "Test" in b["ad_basili"], b["kod"]


def test_birimler_konu_araliginda(birim: dict, harita: dict) -> None:
    aralik = {k["kod"]: (k["bas_sayfa"], k["son_sayfa"]) for k in harita["konular"]}
    for b in birim["birimler"]:
        bas, son = aralik[b["konu"]]
        assert bas <= b["bas_sayfa"] <= b["son_sayfa"] <= son, b["kod"]
        assert len(b["sorular"]) == b["soru_sayisi"], b["kod"]


def test_tekrar_eden_alt_basliklar_civili(birim: dict) -> None:
    """Kitap ayni alt basligi uc kez yeniden aciyor (d306 sag, d309 sol, d328 sag)."""
    assert len(birim["tekrar_eden_alt_baslik"]) == TEKRAR_EDEN_ALT_BASLIK


def test_sari_kutular_ikiye_ayriliyor(sari: dict, birim: dict) -> None:
    """318 kutu bir birim baslatir, 13 kutu onceki birimin devamidir."""
    assert sari["kutu_sayisi"] == len(sari["kutular"]) == SARI_KUTU
    baslar = {
        tuple(b["sorular"][0].values())
        for b in birim["birimler"]
        if b["tur"] == "konu_ogrenme"
    }
    ilk = [tuple(k["ilk_soru"]) for k in sari["kutular"]]
    assert sum(1 for x in ilk if x in baslar) == BIRIM_TURU["konu_ogrenme"]
    assert sum(1 for x in ilk if x not in baslar) == DEVAM_KUTUSU


# ----------------------------------------------------------- 4. capa / kutu


def test_numara_capasi_serit_girdisiyle_birebir(numara: dict, anahtar: dict) -> None:
    s = numara["sutunlar"]
    assert len(s) == SUTUN_SAYISI
    sayim = Counter(f"{x['dosya']}{x['sutun']}" for x in anahtar["cevaplar"])
    for k, v in s.items():
        assert len(v) == sayim.get(k, 0), k
    assert sum(len(v) for v in s.values()) == BEKLENEN_SORU


def test_simge_taramasi_toplami() -> None:
    s = _oku(SIMGE_YOLU)
    assert (
        s["simge_sayisi"] == sum(len(v) for v in s["sayfalar"].values()) == SIMGE_TOPLAM
    )


def test_kutular_kartta_sutunda_ve_seride_sizmiyor(kutu: dict) -> None:
    assert kutu["kutu_sayisi"] == len(kutu["kutular"]) == BEKLENEN_SORU
    assert kutu["sutun_sinirlari"] == SUTUNLAR
    for k in kutu["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        par = "tek" if k["dosya"] % 2 else "cift"
        assert [x0, x1] == SUTUNLAR[par][k["sutun"]], k
        assert 0 <= y0 < y1 <= SAYFA_ALTI, k
        assert y0 <= k["capa"][0] < y1, k


def test_kutular_cakismiyor_ve_sonraki_numarayi_yutmuyor(kutu: dict) -> None:
    grup: dict[tuple, list] = {}
    for k in kutu["kutular"]:
        grup.setdefault((k["dosya"], k["sutun"]), []).append(k)
    for g in grup.values():
        g.sort(key=lambda k: k["kutu"][1])
        for a, b in itertools.pairwise(g):
            assert a["kutu"][3] <= b["kutu"][1], (a, b)
            assert a["kutu"][3] <= b["capa"][0], (a, b)


def test_kutu_capasi_numara_taramasindan(kutu: dict, numara: dict) -> None:
    for k in kutu["kutular"]:
        capalar = sorted(numara["sutunlar"][f"{k['dosya']}{k['sutun']}"])
        assert capalar[k["serit_sira"]] == k["capa"], k


def test_kutu_ozeti_gercek(kutu: dict) -> None:
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutu["kutular"])
    assert kutu["yukseklik"] == {
        "min": yuk[0],
        "medyan": yuk[len(yuk) // 2],
        "max": yuk[-1],
    }


# ----------------------------------------------------------------- 5. ortme


def test_ortme_olcumu_tam_kitap_ve_ozet_gercek(ortme: dict) -> None:
    assert ortme["tam_kitap"] is True
    assert ortme["kenar_kapisi_ihlali"] == len(ortme["kenar"]) == 0
    sorular = {(o["birim"], o["soru"]) for o in ortme["ortme"]}
    assert ortme["ortme_suphesi_soru"] == len(sorular) == ORTME_SORU


def test_okunamayan_her_sik_ortme_olcumunde_de_var(ortme: dict, metin: dict) -> None:
    """Okuyucunun 'okunamadi' dedigi sik ile piksel olcumu bagimsiz iki kanal."""
    olculen = {f"{o['birim']}_{o['soru']:02d}" for o in ortme["ortme"]}
    okunamayan = [
        s["dosya"] for s in metin["sorular"] if SIK_OKUNAMADI in s["sikler"].values()
    ]
    assert len(okunamayan) == OKUNAMAYAN_SIK
    assert set(okunamayan) <= olculen


# ----------------------------------------------------------------- 6. metin


def test_metin_her_kirpima_bir_kayit(metin: dict, kutu: dict) -> None:
    s = metin["sorular"]
    assert metin["soru_sayisi"] == len(s) == BEKLENEN_SORU
    beklenen = {f"{k['birim']}_{k['soru']:02d}" for k in kutu["kutular"]}
    assert {x["dosya"] for x in s} == beklenen


def test_metin_basili_numara_birim_ici_sira(metin: dict) -> None:
    """Okuyucuya sira soylenmedi; basili numara kutu capasini bagimsiz dogrular."""
    for s in metin["sorular"]:
        assert s["basili_no"] == int(s["dosya"].rsplit("_", 1)[1]), s["dosya"]


def test_metin_bes_sik_dolu(metin: dict) -> None:
    for s in metin["sorular"]:
        assert set(s["sikler"]) == set("ABCDE"), s["dosya"]
        for h in "ABCDE":
            assert str(s["sikler"][h]).strip(), (s["dosya"], h)
        if SIK_OKUNAMADI in s["sikler"].values():
            assert s.get("kaynak_kusuru"), s["dosya"]


def test_metin_cevap_tasimiyor(metin: dict) -> None:
    yasak = {"cevap", "dogru_cevap", "correct_answer", "answer", "anahtar"}
    for s in metin["sorular"]:
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
    assert sum(1 for x in s if x["okuma"].startswith("duzeltme")) == DUZELTME_OKUMASI


def test_metin_govde_tekrari_yalniz_sekil_ikizi(metin: dict) -> None:
    """Birebir ayni govde + sikler yalniz d8 sol #2 / sag #5 (farkli sekil)."""
    anahtar = Counter(
        (s["govde"], tuple(s["sikler"][h] for h in "ABCDE")) for s in metin["sorular"]
    )
    tekrar = [k for k, v in anahtar.items() if v > 1]
    assert len(tekrar) == 1
    ikiz = sorted(
        s["dosya"]
        for s in metin["sorular"]
        if (s["govde"], tuple(s["sikler"][h] for h in "ABCDE")) == tekrar[0]
    )
    assert ikiz == ["GEO-ACL25-K01-B04_02", "GEO-ACL25-K01-B04_05"]


# ------------------------------------------------------------------ 7. ASCII


@pytest.mark.parametrize(
    "yol",
    [
        HARITA_YOLU,
        BIRIM_YOLU,
        ANAHTAR_YOLU,
        NUMARA_YOLU,
        SIMGE_YOLU,
        SARI_YOLU,
        KUTU_YOLU,
        ORTME_YOLU,
        METIN_YOLU,
        SERIT_OKUMA_YOLU,
        BASLIK_OKUMA_YOLU,
    ],
)
def test_ciktilar_ascii(yol: Path) -> None:
    ham = yol.read_bytes()
    assert all(b < 128 for b in ham), yol.name
