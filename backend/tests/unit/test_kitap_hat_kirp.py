"""kitap_hat kirpim kesik kapisi: kirp.kenar_olc / kutu.alt_sinir_alti / metin.kirpim_kapisi.

Sentetik kart (ekran goruntusu istemez). Sayilar-1'de SAYFA_ALTI yanlis olculunce
sol sutunun son sorusu 10 sayfada kesilmis, ancak metin okumasinda fark
edilmisti; bu kapilar kesigi kutu ve kirpim asamasinda durdurur.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kitap_hat import kirp, kutu, metin


def _kart(h: int = 120, w: int = 100) -> np.ndarray:
    return np.full((h, w, 3), 255, np.uint8)


def test_kenar_olc_temiz_kutu_sifir() -> None:
    a = _kart()
    a[30:60, 20:70] = 0  # icerik kutunun ortasinda
    o = kirp.kenar_olc(a.min(axis=2), [10, 10, 90, 100])
    assert o == {"sol": 0, "sag": 0, "ust": 0, "alt": 0}
    assert not kirp.kenar_ihlali(o)


def test_kenar_olc_alt_kesik_yakalanir() -> None:
    a = _kart()
    a[98:100, 30:35] = 0  # alt 2 satirda 5 px murekkep = sik kesilmis
    o = kirp.kenar_olc(a.min(axis=2), [10, 10, 90, 100])
    assert o["alt"] == 10 and o["ust"] == 0
    assert kirp.kenar_ihlali(o)


def test_kenar_olc_ust_ve_yan_kenarlar() -> None:
    a = _kart()
    a[10:12, 40:44] = 0  # ust
    a[50:56, 10:11] = 0  # sol 6 px
    a[50:52, 89:90] = 0  # sag 2 px (esik alti)
    a[98:100, 84:88] = 0  # alt seridin KOSE_PAY icindeki kose: sayfa susu, sayilmaz
    o = kirp.kenar_olc(a.min(axis=2), [10, 10, 90, 100])
    assert (o["ust"], o["sol"], o["sag"], o["alt"]) == (8, 6, 2, 0)
    assert kirp.kenar_ihlali(o)
    assert not kirp.kenar_ihlali({"sol": 3, "sag": 3, "ust": 3, "alt": 3})


def test_alt_sinir_alti_kesik_icerik() -> None:
    a = _kart(200, 300)
    a[150:160, 20:60] = 0  # alt sinir 140'in altinda soru metni (40 px)
    a[190, 0:300] = 0  # sayfa cizgisi (tam genislik)
    assert kutu.alt_sinir_alti(a, 0, 300, 140, serit=None, serit_pay=4) == (150, 40)


def test_alt_sinir_alti_altlik_ve_serit_sayilmaz() -> None:
    a = _kart(200, 300)
    a[190, 0:300] = 0  # sayfa cizgisi: burada durur
    a[195:198, 10:30] = 0  # cizginin altindaki sayfa numarasi sayilmaz
    assert kutu.alt_sinir_alti(a, 0, 300, 140, serit=None, serit_pay=4) is None
    a[170:180, 100:250] = 0  # cevap seridi metni: serit satirlari atlanir
    assert (
        kutu.alt_sinir_alti(a, 0, 300, 140, serit=[172, 178, 100, 250], serit_pay=4)
        is None
    )
    # serit disinda, altlik ustunde murekkep yine yakalanir
    a[150:152, 20:40] = 0
    assert kutu.alt_sinir_alti(
        a, 0, 300, 140, serit=[172, 178, 100, 250], serit_pay=4
    ) == (150, 20)


def test_alt_sinir_alti_serit_sutunla_ortusmuyorsa_serit_hizasi_da_taranir() -> None:
    """acl24mg s29: sol sutun metni sag sutundaki seridin hizasina (y 885-889)
    iniyor; serit sol sutunla ortusmedigi icin o satirlar atlanmaz, kesik yakalanir."""
    a = _kart(200, 700)
    a[172:178, 400:650] = 0  # serit (sag sutun hizasinda)
    a[174:178, 30:120] = 0  # sol sutunun seride hizali son satiri
    assert kutu.alt_sinir_alti(
        a, 0, 300, 170, serit=[172, 178, 400, 650], serit_pay=4
    ) == (174, 90)
    # sag sutun: serit ortusuyor, satirlari atlanir, seridin alti taranmaz
    a[190:195, 400:420] = 0  # sayfa numarasi seridin altinda
    assert (
        kutu.alt_sinir_alti(a, 350, 700, 168, serit=[172, 178, 400, 650], serit_pay=4)
        is None
    )


def test_alt_sinir_serit_kismi_ortusme_uyarisi() -> None:
    class P:
        SAYFA_ALTI = 900
        SERIT_PAY = 4
        SERIT_ORTUSME_EN_AZ = 60

    sayfa = {"anahtar": [880, 898, 351, 700]}
    assert kutu._alt_sinir(P, sayfa, 8, 354) == (
        900,
        "serit sutunla 3 px ortusuyor, sinir SAYFA_ALTI",
    )
    assert kutu._alt_sinir(P, sayfa, 373, 700) == (876, None)
    assert kutu._alt_sinir(P, {"anahtar": None}, 8, 354) == (900, None)


def test_kirpim_kapisi() -> None:
    assert (
        metin.kirpim_kapisi({"kenar_kapisi_ihlali": 0, "kesik_kapisi_ihlali": 0}) == []
    )
    assert metin.kirpim_kapisi({"kenar_kapisi_ihlali": 0}) == []  # eski olcum dosyasi
    h = metin.kirpim_kapisi({"kenar_kapisi_ihlali": 1, "kesik_kapisi_ihlali": 10})
    assert len(h) == 2 and h[1].startswith("kesik_kapisi_ihlali 10")
