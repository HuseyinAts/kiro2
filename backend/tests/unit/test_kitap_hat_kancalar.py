"""Aktif duzeni icin eklenen profil kancalari (28 Eyl 2026, AKT20K0).

* bas_listesi.baski_duzelt: kitapta yanlis basilmis serit numaralari
  (s342 '6 7 8 10 11 12') sira numarasiyla degisir; okunan dizi profildekinden
  farkliysa durur.
* anahtar._disla / _harf_bloblari(bolme_x): iki kutulu seritte sayfa numarasi
  harf sayilmaz; okuma sirasi sol kutu (tum satirlari) sonra sag kutu.
* kutu.ust_bant: profil kancasi ya da sabit UST_BANT.
* kirp.sayfa_no_lekesi: SUS_BOLGELERI'nde yalniz DOYGUN pikseller beyazlar.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kitap_hat import anahtar, bas_listesi, kirp, kutu


def _okuma(*sayfa: list[int]) -> list[dict]:
    return [
        {"test": i, "konu": "K", "test_no": "1", "hucreler": [[n, "A"] for n in s]}
        for i, s in enumerate(sayfa, 1)
    ]


def test_baski_duzelt_sira_numarasina_cevirir() -> None:
    p = SimpleNamespace(
        SERIT_NUMARA_BASKI_HATASI={342: ((6, 7, 8, 10, 11, 12), (7, 8, 9, 10, 11, 12))}
    )
    ok = _okuma([1, 2, 3, 4, 5, 6], [6, 7, 8, 10, 11, 12])
    out = bas_listesi.baski_duzelt(p, ok, [341, 342])
    assert [x[0] for x in out[1]["hucreler"]] == [7, 8, 9, 10, 11, 12]
    assert [x[0] for x in ok[1]["hucreler"]] == [6, 7, 8, 10, 11, 12]  # girdi korunur
    assert out[0] == ok[0]
    # profil yoksa girdi aynen doner
    assert bas_listesi.baski_duzelt(SimpleNamespace(), ok, [341, 342]) is ok


def test_baski_duzelt_okuma_profille_uyusmazsa_durur() -> None:
    p = SimpleNamespace(
        SERIT_NUMARA_BASKI_HATASI={342: ((6, 7, 8, 10, 11, 12), (7, 8, 9, 10, 11, 12))}
    )
    with pytest.raises(SystemExit):
        bas_listesi.baski_duzelt(p, _okuma([1, 2], [7, 8, 9]), [341, 342])


def _harf(a: np.ndarray, y: int, x: int) -> None:
    a[y : y + 7, x : x + 5] = 0


def test_disla_ve_iki_kutulu_okuma_sirasi() -> None:
    p = SimpleNamespace(
        ANAHTAR_DISLA_X=(100, 140),
        GLIF_HARF_ESIK=150,
        GLIF_HARF_H=(6, 8),
        GLIF_HARF_W_EN_COK=8,
    )
    s = np.full((30, 240, 3), 255, np.uint8)
    for y, x in ((2, 10), (2, 40), (15, 10), (2, 160), (15, 160)):
        _harf(s, y, x)
    _harf(s, 8, 115)  # sayfa numarasi (disarida)
    t = anahtar._disla(p, s, 0)
    assert int((t[:, 100:140] < 255).sum()) == 0
    assert int((s[:, 100:140] < 255).sum()) > 0  # girdi kopyalanir
    bl = anahtar._harf_bloblari(p, t, 120)
    # dikey 2 px genisletme blob ustunu 1 satir yukari tasir; satir-once
    # olsaydi (1,10) (1,40) (1,160) (14,10) (14,160)
    assert [(o[0].start, o[1].start) for o in bl] == [
        (1, 10),
        (1, 40),
        (14, 10),
        (1, 160),
        (14, 160),
    ]


def test_ust_bant_kancasi() -> None:
    a = np.zeros((10, 10, 3), np.uint8)
    assert kutu.ust_bant(SimpleNamespace(UST_BANT=70), a) == 70
    assert kutu.ust_bant(SimpleNamespace(UST_BANT=70, ust_bant=lambda _a: 91), a) == 91


def test_ortak_oncul_bayragi_ve_beta_disi() -> None:
    from scripts.kitap.kitap_hat import beta_olc, ithal

    r = {"dosya": "X-T001_02", "govde": "Tepkimenin derecesi kactir?"}
    sec = {h: str(i) for i, h in enumerate("ABCDE")}
    assert "ortak_oncul_kirpimda_yok" in ithal._bayraklar(r, sec, ("X-T001_02",))
    assert "ortak_oncul_kirpimda_yok" not in ithal._bayraklar(r, sec, ("X-T001_03",))
    assert "ortak_oncul_kirpimda_yok" in beta_olc.SERVIS_DISI
    sablon = (
        Path(__file__).resolve().parents[2] / "scripts/kitap/kitap_hat/sablon/beta.tmpl"
    ).read_text("ascii")
    assert "? 'ortak_oncul_kirpimda_yok')" in " ".join(sablon.split())


def test_sus_bolgeleri_yalniz_doygun_pikseli_beyazlar() -> None:
    a = np.full((50, 50, 3), 255, np.uint8)
    a[10:14, 10:14] = (160, 30, 70)  # koyu kirmizi kivrim (doygun)
    a[20:24, 10:14] = (20, 20, 20)  # siyah metin
    a[40:44, 40:44] = (160, 30, 70)  # pencere disi
    p = SimpleNamespace(LEKE=None, SUS_BOLGELERI=((5, 30, 5, 30),))
    m = kirp.sayfa_no_lekesi(p, a)
    assert m[10:14, 10:14].all()
    assert not m[20:24, 10:14].any()
    assert not m[40:44, 40:44].any()
    assert not kirp.sayfa_no_lekesi(SimpleNamespace(LEKE=None), a).any()


def test_parite_ters_kumesi_yerlesim_paritesini_cevirir() -> None:
    """Yakalama boslugundan sonra dosya ile basili sayfa paritesi kayan kitap
    (AKT24BY s251-253): PARITE_TERS'teki dosyada SIMGE_X / SUTUNLAR anahtari ters."""
    from scripts.kitap.kitap_hat import ortak

    p = SimpleNamespace(PARITE_TERS=frozenset({251, 252}))
    assert ortak.parite(p, 250) == 0
    assert ortak.parite(p, 251) == 0
    assert ortak.parite(p, 252) == 1
    assert ortak.parite(SimpleNamespace(), 251) == 1


def test_profil_boslugu_dar_bantta_ust_siniri_numaraya_yakin_tutar() -> None:
    """AKT25FZ: sorular arasi bos bant sik satirlari arasindan dar. Varsayilan
    BOSLUK onceki sorunun sik satirlarinin ustune cikar; profil BOSLUK=5 bandi yakalar."""
    m = np.zeros(40, bool)
    m[5:10] = True  # onceki sorunun son sik satiri
    m[16:18] = True  # ayni sorunun bir onceki sik satiri
    # 18-23 bos (6 satir), numara y=24; 10-15 bos (6 satir)
    assert kutu._ust(24, 0, m, 5) == 19 + 5 - kutu.UST_PAY
    assert kutu._ust(24, 0, m, 7) == 0  # 6 satirlik bantlar yetmez -> tavan
    assert kutu._ust(24, 0, m) == kutu._ust(24, 0, m, kutu.BOSLUK)


def test_kutu_ust_kesin_asagi_da_iner_kutu_ust_yalniz_yukari() -> None:
    p = SimpleNamespace(
        KUTU_UST={(7, "R", 0): 90, (7, "R", 1): 400},
        KUTU_UST_KESIN={(7, "R", 2): 623, (8, "R", 2): 1},
    )
    assert kutu._kutu_ust(p, 7, "R", [100, 300, 600]) == [90, 300, 623]
    assert kutu._kutu_ust(SimpleNamespace(), 7, "R", [100, 300]) == [100, 300]


def test_kesik_goz_onayi_kapidan_ayirir_ve_bayat_onayi_bildirir() -> None:
    kesik = [
        {"birim": "X-T063", "soru": 10, "alt": 9},
        {"birim": "X-T065", "soru": 4, "alt": 45},
    ]
    p = SimpleNamespace(KESIK_GOZ_ONAY=("X-T063_10", "X-T001_01"))
    kalan, onayli, bayat = kirp.goz_onayi_ayir(p, kesik)
    assert [x["soru"] for x in kalan] == [4]
    assert [x["soru"] for x in onayli] == [10]
    assert bayat == ["X-T001_01"]
    assert kirp.goz_onayi_ayir(SimpleNamespace(), kesik) == (kesik, [], [])


def test_sus_parite_yalniz_kendi_paritesinde_beyazlatir() -> None:
    """AKT25PR: orta ayrac cift / tek sayfada farkli x'te; tek pencere diger
    paritenin kirmizi numarasini da silerdi -> SUS_PARITE yerlesim paritesine gore."""
    a = np.full((50, 60, 3), 255, np.uint8)
    a[10:20, 10:14] = (0, 130, 150)  # cift ayrac yazisi (camgobegi)
    a[10:20, 30:34] = (220, 30, 40)  # kirmizi numara (tek ayrac penceresinde)
    p = SimpleNamespace(
        LEKE=None, SUS_PARITE={0: ((0, 50, 5, 20),), 1: ((0, 50, 25, 40),)}
    )
    cift = kirp.sayfa_no_lekesi(p, a, 18)
    assert cift[10:20, 10:14].all() and not cift[10:20, 30:34].any()
    tek = kirp.sayfa_no_lekesi(p, a, 19)
    assert tek[10:20, 30:34].all() and not tek[10:20, 10:14].any()
    assert not kirp.sayfa_no_lekesi(p, a).any()  # n verilmezse parite penceresi yok


# --- Apotemi duzeni (APO19MT): anahtar kitap sonunda tablo, seritsiz sayfa ---


def test_anahtar_harici_tablo_satirlarini_sayfa_seridine_tercih_eder() -> None:
    tar = {"sayfalar": {"10": {"anahtar": [800, 830, 400, 700]}}}
    t = {"test": 3, "sayfalar": [10]}
    p = SimpleNamespace(ANAHTAR_HARICI={3: [(316, (100, 118, 40, 700))]})
    assert anahtar.anahtar_parcalari(p, tar, t) == [(316, [100, 118, 40, 700])]
    assert anahtar.anahtar_parcalari(SimpleNamespace(), tar, t) == [
        (10, [800, 830, 400, 700])
    ]


def test_yakalanmayan_soru_anahtar_hucrelerinden_duser() -> None:
    from scripts.kitap.kitap_hat import ortak

    h = [[n, "A"] for n in range(1, 11)]
    p = SimpleNamespace(YAKALANMAYAN_SORU={81: (5, 6, 7, 8)})
    assert [x[0] for x in ortak.yakalanan(p, 81, h)] == [1, 2, 3, 4, 9, 10]
    assert ortak.yakalanan(p, 80, h) == h
    assert ortak.yakalanan(SimpleNamespace(), 81, h) == h


def test_harf_bloblari_profil_kancasina_devredilir() -> None:
    ozel = [(slice(0, 5), slice(3, 8))]
    p = SimpleNamespace(harf_bloblari=lambda _s: ozel)
    assert anahtar._harf_bloblari(p, np.zeros((5, 5, 3), np.uint8)) is ozel


def test_testleri_bul_harici_anahtarda_serit_aramaz() -> None:
    from scripts.kitap.kitap_hat import tarama

    s = {
        1: {"tur": "test", "anahtar": None},
        2: {"tur": "test", "anahtar": None},
        3: {"tur": "test", "anahtar": None},
        4: {"tur": "kapak", "anahtar": None},
    }
    with pytest.raises(SystemExit):
        tarama.testleri_bul(s, {1, 3})
    assert tarama.testleri_bul(s, {1, 3}, serit_sart=False) == [[1, 2], [3]]


def test_sayfa_altligi_alt_sinir_taramasini_durdurur() -> None:
    a = np.full((120, 100, 3), 255, np.uint8)
    a[100:104, 10:40] = 0  # sayfa altligi (sayfa no kutusu, 30 px -- cizgi degil)
    assert kutu.alt_sinir_alti(a, 0, 100, 80, serit=None, serit_pay=0) is not None
    assert (
        kutu.alt_sinir_alti(a, 0, 100, 80, serit=None, serit_pay=0, altlik_y=98) is None
    )
    a[90:92, 10:40] = 0  # altligin USTUNDE gercek kesik yine yakalanir
    assert kutu.alt_sinir_alti(a, 0, 100, 80, serit=None, serit_pay=0, altlik_y=98)


# --- Apotemi konu testi duzeni (APO19FZ) ---


def test_serit_altlikta_alt_siniri_sayfa_altinda_tutar() -> None:
    sayfa = {"anahtar": [892, 904, 240, 640]}
    p = SimpleNamespace(SAYFA_ALTI=876, SERIT_PAY=4)
    assert kutu._alt_sinir(p, sayfa, 28, 361) == (888, None)
    p.SERIT_ALTLIKTA = True
    assert kutu._alt_sinir(p, sayfa, 28, 361) == (876, None)
    p.SAYFA_ALTI = 900  # serit ustu daha yukarida: serit siniri kalir
    assert kutu._alt_sinir(p, sayfa, 28, 361) == (888, None)


def test_kenar_goz_onayi_ayri_listeden_okunur() -> None:
    kenar = [{"birim": "X-T039", "soru": 5, "sag": 7}]
    p = SimpleNamespace(KENAR_GOZ_ONAY=("X-T039_05",), KESIK_GOZ_ONAY=())
    assert kirp.goz_onayi_ayir(p, kenar, "KENAR_GOZ_ONAY") == ([], kenar, [])
    assert kirp.goz_onayi_ayir(p, kenar) == (kenar, [], [])


def test_sinav_sinif_konu_duzeyinde() -> None:
    from scripts.kitap.kitap_hat import ithal

    p = SimpleNamespace(SINAV="TYT", SINIF=9)
    assert ithal.sinav_sinif(p, "FIZ-X-B01-K01") == ("TYT", 9)
    p.SINAV_KONU = {"FIZ-X-B01-K01": ("TYT", 9), "FIZ-X-B01-K02": ("AYT", 11)}
    assert ithal.sinav_sinif(p, "FIZ-X-B01-K02") == ("AYT", 11)
    with pytest.raises(KeyError):
        ithal.sinav_sinif(p, "FIZ-X-B09-K01")


# --- hiz: pencere renk, surec havuzu, tek okuma, sekil satiri (29 Eyl 2026) ---


def test_okuyucu_maskesi_pencere_tam_sayfa_hesabiyla_ayni() -> None:
    """Renk siniflamasi yalniz disk penceresinde hesaplanir; tam sayfa hesabiyla
    (eski yol) bit bit ayni olmali (gercek veride 14 kitap / 3590 sayfa: fark 0)."""
    rng = np.random.default_rng(3)
    a = rng.integers(0, 256, (120, 140, 3)).astype(np.uint8)
    a[40:70, 50:80] = (69, 39, 160)  # glif rengi
    p = SimpleNamespace(
        BEYAZ_YARICAP=17,
        numara_maskesi=lambda x: (x[..., 0] > 200) & (x[..., 1] < 80),
    )
    merkez = [[55, 65], [10, 10], [115, 135]]
    yeni = kirp.okuyucu_maskesi(p, a, merkez)
    renk = kirp._okuyucu_rengi(a) & ~p.numara_maskesi(a.astype(int))
    ai = a.astype(np.int16)
    notr = (ai.max(axis=2) - ai.min(axis=2) < kirp.GOLGE_FARK) & (
        ai.max(axis=2) >= kirp.SOL_GRI
    )
    eski = np.zeros(a.shape[:2], bool)
    for gy, gx in merkez:
        sl, r, _, dx = kirp._pencere(a.shape, gy, gx, p.BEYAZ_YARICAP + 2)
        eski[sl] |= (r <= p.BEYAZ_YARICAP) & (renk[sl] | ((dx < -5) & notr[sl]))
    assert np.array_equal(yeni, eski)


def test_paralel_sirayi_korur() -> None:
    from scripts.kitap.kitap_hat import ortak

    girdi = list(range(-40, 0))
    assert ortak.paralel(abs, girdi) == [abs(x) for x in girdi]
    assert ortak.paralel(abs, [-3, -1]) == [3, 1]  # az is: sirali yol


def test_tek_okuma_etiket_gozu_olmadan_durur() -> None:
    ham = {
        "okuma_a": {"testler": [{"test": 1, "hucreler": [[1, "A"], [2, "C"]]}]},
        "okuma_b": None,
        "glif": {
            "kapsam_disi_test": [],
            "goz_teyit": {},
            "uyumsuz": [],
            "hucre": 2,
            "uyum": 2,
        },
        "goz_c": {"testler": {}},
    }
    assert any("etiket" in h for h in anahtar.dogrula(SimpleNamespace(), ham))
    ham["glif"]["etiket_goz"] = True
    assert anahtar.dogrula(SimpleNamespace(), ham) == []
    from scripts.kitap.kitap_hat import ithal

    assert ithal.okuma_on(ham) == "tek_okuma"
    assert "tek_okuma+glif" in ithal.CEVAP_KANALLARI
    assert "iki_okuma+glif" in ithal.CEVAP_KANALLARI


def test_sekil_satiri_sirasiz_karsilastirilir() -> None:
    import importlib.util

    yol = Path(__file__).resolve().parents[2] / "scripts/kitap/metin_iki_okuma.py"
    spec = importlib.util.spec_from_file_location("metin_iki_okuma_s", yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules["metin_iki_okuma_s"] = m
    spec.loader.exec_module(m)
    sekil = "\u015eekil"
    a = f"Soru kok\u00fc\n{sekil}: 30\u00b0; 2 m; 10 N"
    assert m.norm(a) == m.norm(f"Soru kok\u00fc\n{sekil}: 10 N;2m; 30\u00b0")
    assert m.norm(a) != m.norm(f"Soru kok\u00fc\n{sekil}: 30\u00b0; 3 m; 10 N")
    assert m.norm("K; L") == "K; L"  # Sekil satiri disina dokunmaz


def _metin_iki_okuma():  # type: ignore[no-untyped-def]
    import importlib.util

    yol = Path(__file__).resolve().parents[2] / "scripts/kitap/metin_iki_okuma.py"
    spec = importlib.util.spec_from_file_location("metin_iki_okuma_g", yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules["metin_iki_okuma_g"] = m
    spec.loader.exec_module(m)
    return m


def test_grup_fark_yalniz_farkli_sorulari_hakeme_yazar(tmp_path: Path) -> None:
    import json

    m = _metin_iki_okuma()
    k = SimpleNamespace(
        parca1=tmp_path / "p1", parca2=tmp_path / "p2", hakem=tmp_path / "h"
    )
    k.parca1.mkdir()
    k.parca2.mkdir()
    (k.parca1 / "liste_03.txt").write_text("X-T001_01\nX-T001_02\n", "ascii")

    def s(ad: str, govde: str) -> dict:
        return {
            "dosya": ad,
            "basili_no": 1,
            "govde": govde,
            "sikler": {h: h for h in "ABCDE"},
            "sekil_var": False,
            "sikler_gorsel": False,
            "etiket": None,
            "kaynak_kusuru": None,
        }

    for d, g2 in ((k.parca1, "H_2O"), (k.parca2, "H_2O_2")):
        (d / "grup_03.json").write_text(
            json.dumps({"sorular": [s("X-T001_01", "ayni"), s("X-T001_02", g2)]}),
            "utf-8",
        )
    assert m.grup_fark(k, "03") == 1
    out = json.loads((k.hakem / "hakem_g03.json").read_text("utf-8"))
    assert [x["dosya"] for x in out] == ["X-T001_02"]
    assert out[0]["okuma_2"]["govde"] == "H_2O_2"
    # Kapsam listeyle uyusmazsa durur (eksik okuma hakeme gitmez).
    (k.parca1 / "liste_03.txt").write_text("X-T001_01\n", "ascii")
    with pytest.raises(SystemExit):
        m.grup_fark(k, "03")


def test_bolum_bant_adi_etiket_onekini_atar() -> None:
    from scripts.kitap.kitap_hat import harita

    p = SimpleNamespace(
        BOLUMLER=(
            (1, "1. \u00dcN\u0130TE K\u0130MYA B\u0130L\u0130M\u0130"),
            (2, "Genel"),
        )
    )
    assert harita.bolum_bant_adi(p, "KIM-X-B01") == "K\u0130MYA B\u0130L\u0130M\u0130"
    assert harita.bolum_bant_adi(p, "KIM-X-B02") == "Genel"


def test_anahtar_numara_baskisi_sira_numarasina_cevrilir() -> None:
    p = SimpleNamespace(ANAHTAR_NUMARA_BASKI={(7, 3): 2})
    h = [[1, "A"], [2, "B"], [2, "C"], [4, "D"]]
    assert anahtar.baski_numara(p, 7, h) == [[1, "A"], [2, "B"], [3, "C"], [4, "D"]]
    assert anahtar.baski_numara(p, 8, h) == h  # baska test: dokunmaz
    # Profildeki basili deger okumayla uyusmazsa (bayat kayit) durur.
    with pytest.raises(SystemExit):
        anahtar.baski_numara(p, 7, [[1, "A"], [2, "B"], [3, "C"]])


def test_aromat_harf_bloku_ilk_tireden_sonra_baslar() -> None:
    from scripts.kitap.kitap_hat.profiller import aro23af

    # 6 satirlik '1-D': rakam acik gri (maskeye girmez), tire orta satirda koyu,
    # D'nin sag kenari yalniz orta satirlarda murekkepli (tireye benzer).
    s = np.full((10, 30, 3), 255, np.uint8)
    s[2:8, 2] = 190  # '1' acik gri
    s[5, 5:7] = 60  # tire (orta satir)
    s[2:8, 9] = 60  # D govdesi
    s[2, 10:12] = 60
    s[7, 10:12] = 60
    s[4:6, 12] = 60  # D sag kenari: yalniz orta satirlar
    bl = aro23af.harf_bloblari(s)
    assert len(bl) == 1
    assert (bl[0][1].start, bl[0][1].stop) == (9, 13)


def test_bas_listesi_tek_okumada_b_yerine_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    from scripts.kitap.kitap_hat import ortak

    monkeypatch.setattr(ortak, "VERAFILM", tmp_path)
    p = SimpleNamespace(VERAF="zz")
    d = tmp_path / "zz_serit"
    d.mkdir()
    a = {"testler": [{"test": 1, "konu": "K", "test_no": "1", "hucreler": [[1, "A"]]}]}
    (d / "okuma_A.json").write_text(json.dumps(a), "utf-8")
    assert not bas_listesi.tek_okuma_degil(p)
    assert bas_listesi.okuma(p, "B") == bas_listesi.okuma(p, "A")
    (d / "okuma_B.json").write_text(json.dumps({"testler": []}), "utf-8")
    assert bas_listesi.tek_okuma_degil(p)
    assert bas_listesi.okuma(p, "B") == []


def test_bant_esleri_demet_ve_tekil() -> None:
    from scripts.kitap.kitap_hat import harita

    p = SimpleNamespace(BANT_ESLER={"ELEKTRIK": ("A", "B"), "X": "Y"})
    assert harita.bant_esleri(p, "ELEKTRIK") == ("A", "B")
    assert harita.bant_esleri(p, "X") == ("Y",)
    assert harita.bant_esleri(p, "YOK") == ()
    assert harita.norm("NEWTON\u2019IN") == harita.norm("NEWTON'IN")
