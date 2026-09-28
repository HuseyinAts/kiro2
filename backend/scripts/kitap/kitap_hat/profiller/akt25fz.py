"""AKTIF 2025 TYT Fizik Soru Bankasi (Aktif Ogrenme duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 352 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya (gozle). Icindekiler s6: 13 unite (Fizik Bilimine
Giris .. Dalgalar).

SAYFA DUZENI: AKT24BY (2023-2024 Aktif Biyoloji) ile ayni seri; kancalar
oradan (iki kutulu serit, ust_bant, SUS_BOLGELERI). Farklar (olculdu,
_a21_gecici/ak_genel.py, ak_simge.py; 29 Eyl 2026):
* Testin devam sayfasinin bandi ince (turuncu ~1900-3600, pembe ~640-720
  px) -> test = turuncu >= 1500 VE pembe >= 600 VE iki kutulu serit.
  Konu sayfalarinin 'Ornek / Soru' seridi de iki kutulu olabilir ama bant
  rengi yok (s91, 131 ...).
* 132 test sayfasi, 13 blok (her unitede bir blok); kopya sayfa yok.
* Okuyucu simgesi cift L 73 / R 368, tek L 63 / R 358; s57-68 ve s103-108
  iki paritede L 62 / R 365 (tolerans 12 hepsini kapsar).
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.profiller.akt20ay import ust_bant  # noqa: F401
from scripts.kitap.kitap_hat.profiller.akt20k0 import (  # noqa: F401
    ANAHTAR_KAPSAMI,
    BANT_KONU_TARIFI,
    BANT_TARIFI,
    BANT_TEST_NO_TARIFI,
    BANT_Y_ALT,
    BEYAZ_YARICAP,
    DISK_MERKEZ,
    GLIF_BOY,
    GLIF_GENISLET,
    GLIF_HARF_ESIK,
    GLIF_HARF_H,
    GLIF_HARF_W_EN_COK,
    HALKA,
    KART,
    LEKE,
    SERIT_HUCRE_TARIFI,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
    TEST_SINIRI,
    UST_BANT,
    _renkler,
    serit_kutusu,
)
from scripts.kitap.kitap_hat.profiller.akt24by import (  # noqa: F401
    ANAHTAR_DISLA_X,
    ANAHTAR_NEREDEN,
    SERIT_Y,
    SUS_BOLGELERI,
)

KOD = "AKT25FZ"
KAYNAK_ADI = "AKTIF 2025 TYT Fizik Soru Bankasi"
CIKTI_ONEK = "aktif_2025_tyt_fizik"
KLASOR = "Aktif Ogrenme 2025 Tyt Fizik Soru Bankas\u0131"
VERAF = "c2"
BEKLENEN_SAYFA = 352
BEKLENEN_TEST = 66
TEST_SAYFALARI = (
    (13, 18),
    (33, 40),
    (57, 68),
    (79, 88),
    (103, 108),
    (121, 126),
    (141, 146),
    (161, 172),
    (189, 200),
    (219, 232),
    (243, 246),
    (303, 326),
    (341, 352),
)
BAS_SAYFALARI: tuple[int, ...] = (
    13,
    15,
    17,
    33,
    35,
    37,
    39,
    57,
    59,
    61,
    63,
    65,
    67,
    79,
    81,
    83,
    85,
    87,
    103,
    105,
    107,
    121,
    123,
    125,
    141,
    143,
    145,
    161,
    163,
    165,
    167,
    169,
    171,
    189,
    191,
    193,
    195,
    197,
    199,
    219,
    221,
    223,
    225,
    227,
    229,
    231,
    243,
    245,
    303,
    305,
    307,
    309,
    311,
    313,
    315,
    317,
    319,
    321,
    323,
    325,
    341,
    343,
    345,
    347,
    349,
    351,
)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    kutu: list[int] | None = serit_kutusu(a, SERIT_Y)
    return kutu


def sayfa_turu(a: np.ndarray, n: int) -> str:
    turuncu, pembe = _renkler(a)
    s = serit_kutusu(a, SERIT_Y)
    if turuncu >= 1500 and pembe >= 600 and s is not None and s[2] < 100:
        return "test"
    return "konu" if ortak.glifler(sys.modules[__name__], a) else "kapak"


# --- capa ---
SIMGE_X = {0: {"L": 73, "R": 368}, 1: {"L": 63, "R": 358}}
SIMGE_TOLERANS = 14  # PARITE_TERS tek dosyalarda simge L 60 (cift duzen 73)
PENCERE = (-10, 42, 4, 64)
NUMARA_H = (5, 12)  # numara ~8 px (s14 y 97-104)
NUMARA_W_EN_COK = 22
NUMARA_DX = (14, 48)  # olculdu dx 15-46 (s145, s347-352 dar)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Capa numaradan (gozle; ak numara_bul.py): s68 L '4.' ve s106 L '6.' sutun
# basinda, simge bandin hemen altinda (y 62) ve penceredeki ilk blob bant
# kenari -> dx_disi; s192 R '9.' ve s197 R '5.' okuyucu simgesi konmamis.
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    (68, "L", 88, 85),
    (106, "L", 87, 85),
    (192, "R", 606, 393),
    (197, "R", 725, 382),
)
# s346 R: 9. sorunun tablosu ile '10.' arasinda yalniz 7 bos satir (< BOSLUK
# 10) -> 10. sorunun ustu elle (kutu 'cok kisa' kapisi; gozle).
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {
    (346, "R", 1): 372,
    # onceki sorunun E sikki ile numara arasi 1-3 bos satir (BOSLUK 5'ten dar):
    # ust, numaranin hemen ustundeki bos kosunun basi (ust_artik.py olcumu)
    (346, "R", 2): 623,
    (349, "R", 1): 316,
    (349, "R", 2): 576,
}
# Yukaridaki dar bantlar yuzunden bu kutularin alt 2 satiri E sikkinin kuyruguna
# degiyor (kirp 'kesik'); kirpimlar gozle tam (E sikki eksiksiz).
KESIK_GOZ_ONAY: tuple[str, ...] = (
    "AKT25FZ-T063_10",
    "AKT25FZ-T065_04",
    "AKT25FZ-T065_05",
)
# s57-68 ve s103-108 iki paritede de 'cift' duzen (simge L 62 / R 365, R
# numara 388; ak_simge.py): tek dosyalari cift yerlesimle (R sutunu 386'dan;
# 376'dan baslayinca simge halkasi sol kenar ihlali verdi: s67/103/105).
PARITE_TERS = frozenset(range(57, 68, 2)) | frozenset(range(103, 108, 2))
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    """Pembe (~230, 85, 130; s14-15) ya da kirmizi (~230, 30, 30; s86) basili numara; simge numaranin
    ~28 px ustunde; kenar yumusatmasi acik pembe. Turuncu (b << g) ve mor simge (r < 180) disarida."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (r > 180) & (r - g > 50) & (b >= g - 10) & (b < 200)
    return m


# --- harita (icindekiler s6; dosya = basili) ---
KOK_KOD = "FIZ"
KOD_ONEKI = "FIZ-AKT25FZ"
ALAN = "FIZIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s6) 13 unite; unite baslangici icindekiler sayfa no (dosya = basili: "
    "7, 19, 41, 69, 89, 109, 127, 147, 173, 201, 233, 247, 327); konu = test bandindaki "
    "unite adi (iki bagimsiz okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "F\u0130Z\u0130K B\u0130L\u0130M\u0130NE G\u0130R\u0130\u015e"),
    (2, "MADDE VE \u00d6ZELL\u0130KLER\u0130"),
    (3, "BASIN\u00c7"),
    (4, "KALDIRMA KUVVET\u0130"),
    (5, "ISI - SICAKLIK VE GENLE\u015eME"),
    (6, "HAREKET"),
    (7, "KUVVET VE NEWTON'UN HAREKET KANUNLARI"),
    (8, "\u0130\u015e - G\u00dc\u00c7 - ENERJ\u0130"),
    (9, "ELEKTROSTAT\u0130K"),
    (10, "ELEKTR\u0130K AKIMI"),
    (11, "MANYET\u0130ZMA"),
    (12, "OPT\u0130K"),
    (13, "DALGALAR"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Fizik Bilimine Giri\u015f", 7),
    (2, "Madde ve \u00d6zellikleri", 19),
    (3, "Bas\u0131n\u00e7", 41),
    (4, "Kald\u0131rma Kuvveti", 69),
    (5, "Is\u0131 - S\u0131cakl\u0131k ve Genle\u015fme", 89),
    (6, "Hareket", 109),
    (7, "Kuvvet ve Newton'un Hareket Kanunlar\u0131", 127),
    (8, "\u0130\u015f - G\u00fc\u00e7 - Enerji", 147),
    (9, "Elektrostatik", 173),
    (10, "Elektrik Ak\u0131m\u0131", 201),
    (11, "Manyetizma", 233),
    (12, "Optik", 247),
    (13, "Dalgalar", 327),
)
SON_SAYFA = 352
# Test bandi icindekilerden farkli yazili (iki okuma ayni, gozle).
BANT_ESLER: dict[str, str] = {
    "ISI-SICAKLIK-GENLESME": "ISI-SICAKLIK VE GENLESME",
    "KUVVET VE NEWTON\u2019UN HAREKET KANUNLARI": "KUVVET VE NEWTON'UN HAREKET KANUNLARI",
    "IS GUC ENERJI": "IS-GUC-ENERJI",
}

# --- kutu / kirpim (ilk olcum AKT24BY; kirp kenar kapisiyla duzeltilir) ---
# Dikey 'aktif ogrenme yayinlari' yazisi tek sayfa x 362-370 / cift 375-380
# (gri kenarlari doygun degil, SUS'tan kalir; s79 kolon olcumu); R numara
# tek 382 / cift 393. R sutunu simgenin (cift 368-384, tek 358-374) sagindan
# baslar: beyazlatilmis diskin gri halkasi sutuna girince sorular arasi bos
# bandi kapatiyordu (s346 R T063_09 kutusu 14 px).
SUTUNLAR = {0: {"L": (30, 366), "R": (386, 712)}, 1: {"L": (30, 361), "R": (376, 712)}}
# Pembe 'KONU TESTI' sekmesinin koyu kivrimi devam sayfasinda y ~73 (s60-68,
# s104-108 R; kutu artik kapisi): doygun pikseli beyazlatilir.
SUS_BOLGELERI = (*SUS_BOLGELERI, (62, 95, 600, 712))
SAYFA_ALTI = 906
# Sikisik dizgi: onceki sorunun son sik satiri ile sonraki numara arasi bos
# bant 5-9 satir, sik satirlari arasi >= 10 -> BOSLUK 10 ile ust sinir onceki
# sorunun D/E satirinin ustune cikiyordu (metin okumasi: T006_04, T027_03 ...
# siklari sonraki kirpimda). Kutu ustu 5 satirlik bosluktan.
BOSLUK = 5
BEKLENEN_SORU = 655

# --- metin ---
KITAP_BASLIGI = "AKT\u0130F 2025 TYT Fizik Soru Bankas\u0131"
GRUP_SORU = 45
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi kirmizi basilidir; iki sayfalik testlerde numara surer. "
    "Fizik birimleri ve indisler basildigi gibi: `m/s^2`, `F_1`, `v_0`, "
    "`10 N`; harfin ustunde vektor oku basiliysa harfi yaz ve `kaynak_kusuru` "
    "degil, oldugu gibi birak. Sekil icindeki olcu ve etiketler soru ona "
    "dayaniyorsa kisa satirlar halinde govdeye girer.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("FIZIK",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme 2025 Tyt Fizik Soru Bankasi",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aktif Ogrenme Yayinlari"
# Test sonlarinda cikmis sorular '(TYT 2022)' / '(YGS 2017)' etiketli: 33
# (TYT 2018-2023: 28, YGS 2011/2015/2017: 5); hepsi etiket_ayristir'dan gecer.
BEKLENEN_ETIKET = 33
YONTEM_BELGESI = "FIZ_AKTIF_2025_TYT_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 4, "konu": 216, "test": 132},
    "harf": {"A": 117, "B": 115, "C": 146, "D": 124, "E": 153},
    "glif_hucre": 655,
    "glif_uyum": 655,
    "goz_teyit": {},
    "glif_disi": [],
    "metin_parca": 14,
    "farkli_soru": 136,
    "okunamaz": 0,
    "ithal": 648,
    "beta": "648/648",
    "eski_modern": 0,
    "migration_no": 110,
    "onceki": "0109_akt24by_beta_onay",
}
