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
