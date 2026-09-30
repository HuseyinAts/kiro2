"""BS 2024 AYT Fizik Soru Bankasi -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 352 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya - 1 (kapak ic yuzu yakalanmamis; tum kitapta sabit).

SAYFA DUZENI (olculdu; 30 Eyl 2026): BS24FZ (Bilgi Sarmal 2024 TYT Fizik) ile
AYNI dizgi -- sari/turuncu tema, iki sutun, buyutec simgesi, numara siyah,
cevap seridi duz metin (tek basili sayfada solda, cift basili sayfada sagda),
kaynak rozeti ('2023 / AYT'), 'AKILLI NOT' bilgi kutusu. Olculer BASILI
parite ile BS24FZ'nin olculeridir; bu profil yalniz dosya -> basili kaydirmasi
(n - 1) yapar ve BS24FZ kancalarini kullanir.
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat.profiller import bs24fz as _fz
from scripts.kitap.kitap_hat.profiller.akt20k0 import (  # noqa: F401
    BEYAZ_YARICAP,
    DISK_MERKEZ,
    GLIF_GENISLET,
    HALKA,
    KART,
    LEKE,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
)

KOD = "BS24AF"
KAYNAK_ADI = "BILGI SARMAL 2024 AYT Fizik Soru Bankasi"
CIKTI_ONEK = "bilgi_sarmal_2024_ayt_fizik"
KLASOR = "Bilgi Sarmal\u0131 Ayt 2024 Fizik Soru Bankas\u0131"
VERAF = "c13"
BEKLENEN_SAYFA = 352
# Test disi dosyalar: 1-9 (on kisim), bolum kapaklari 54-55, 170-171, 210-211,
# 254-255, 276-277, 306-307 ve tek sayfa 332 (8. bolum).
TEST_SAYFALARI = (
    (10, 53),
    (56, 169),
    (172, 209),
    (212, 253),
    (256, 275),
    (278, 305),
    (308, 331),
    (333, 352),
)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
# Yerlesim paritesi BASILI sayfaya gore: basili = dosya - 1 -> her dosya ters.
PARITE_TERS = frozenset(range(1, BEKLENEN_SAYFA + 1))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
BAS_SAYFALARI: tuple[int, ...] = (
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    24,
    26,
    28,
    30,
    32,
    34,
    36,
    38,
    40,
    42,
    44,
    46,
    48,
    50,
    52,
    56,
    58,
    60,
    62,
    64,
    66,
    68,
    70,
    72,
    74,
    76,
    78,
    80,
    82,
    84,
    86,
    88,
    90,
    92,
    94,
    96,
    98,
    100,
    102,
    104,
    106,
    108,
    110,
    112,
    114,
    116,
    118,
    120,
    122,
    124,
    126,
    128,
    130,
    132,
    134,
    136,
    138,
    140,
    142,
    144,
    146,
    148,
    150,
    152,
    154,
    156,
    158,
    160,
    162,
    164,
    166,
    168,
    172,
    174,
    176,
    178,
    180,
    182,
    184,
    186,
    188,
    190,
    192,
    194,
    196,
    198,
    200,
    202,
    204,
    206,
    208,
    212,
    214,
    216,
    218,
    220,
    222,
    224,
    226,
    228,
    230,
    232,
    234,
    236,
    238,
    240,
    242,
    244,
    246,
    248,
    250,
    252,
    256,
    258,
    260,
    262,
    264,
    266,
    268,
    270,
    272,
    274,
    278,
    280,
    282,
    284,
    286,
    288,
    290,
    292,
    294,
    296,
    298,
    300,
    302,
    304,
    308,
    310,
    312,
    314,
    316,
    318,
    320,
    322,
    324,
    326,
    328,
    330,
    333,
    335,
    337,
    339,
    341,
    343,
    345,
    347,
    349,
    351,
)
BEKLENEN_TEST = 165


def _b(n: int) -> int:
    """Dosya -> basili sayfa (BS24FZ kancalari basili pariteye gore olculdu;
    BS24FZ'de dosya = basili)."""
    return n - 1


SERIT_Y = _fz.SERIT_Y


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    r: list[int] | None = _fz.anahtar_bolgesi(a, _b(n))
    return r


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in _TEST and anahtar_bolgesi(a, n) is not None:
        return "test"
    koyu = a[60:900].max(axis=2) < 120
    return "konu" if int(koyu.sum()) > 2000 else "kapak"


# GOZLE: 'OSYM Tipi' sayfalarinda ust bandin altinda konu alt basligi var
# ('Itme ve Cizgisel Momentum', 'Modern Fizik') ve 1. sorunun numarasi okuyucu
# '?' diskinin ALTINDA kaliyor (dosya 128, 326) -- basili ama olculemez. Capa
# alt basligin ustune konur: kutu alt basligi ve 1. soruyu birlikte alir.
_EK_CAPA_NUMARA: dict[int, tuple[tuple[str, int, int], ...]] = {
    128: (("L", 143, 67),),
    326: (("L", 140, 67),),
}


_ALT_BASLIK_ESIK = 10  # satirda bu kadardan cok koyu px -> yazi satiri
_ALT_BASLIK_EN_AZ = 5  # alt baslik en az bu kadar yazi satiri


def _alt_baslik_ustu(a: np.ndarray, n: int, capa_y: int) -> int | None:
    """'OSYM Tipi' sayfasinda bant ile sol sutunun ilk numarasi arasindaki
    kalin alt baslik ('Vektor - Kesisen Kuvvet - Tork ve Denge'): ust y'si.
    Baslik bolumun konusudur, ilk sorunun kutusuna katilir (yoksa kutu
    asamasinda 'artik murekkep'; s32, s48, s86 ...)."""
    ub = int(_fz.ust_bant(a))
    if ub == _fz.UST_BANT:
        return None
    x0, x1 = _fz.SUTUNLAR[_b(n) % 2]["L"]
    satir = (a[ub : capa_y - 3, x0 + 20 : x1].max(axis=2) < 150).sum(axis=1)
    yazi = [y for y in range(len(satir)) if satir[y] > _ALT_BASLIK_ESIK]
    if len(yazi) < _ALT_BASLIK_EN_AZ:
        return None
    return ub + yazi[0]


def capa_numaralari(a: np.ndarray, n: int) -> list[dict]:
    c = _fz.capa_numaralari(a, _b(n))
    c += [
        {"sutun": s, "y": y, "x": x, "tur": "goz"}
        for s, y, x in _EK_CAPA_NUMARA.get(n, ())
    ]
    sol = [k for k in c if k["sutun"] == "L"]
    if sol:
        ilk = min(sol, key=lambda k: k["y"])
        ust = _alt_baslik_ustu(a, n, ilk["y"])
        if ust is not None:
            ilk["y"] = ust
    return sorted(c, key=lambda k: (k["sutun"], k["y"]))


dislama_bolgeleri = _fz.dislama_bolgeleri
ust_bant = _fz.ust_bant
numara_maskesi = _fz.numara_maskesi

CAPA_MODU = _fz.CAPA_MODU
# Capa simgenin USTUNE cekilebiliyor: rozet simgenin ustunde (s133: rozet y 462,
# simge 491) ya da OSYM Tipi alt basligi (s190/204/248: baslik y ~132, simge
# ~180) -> simge capanin 60 px altina kadar kabul.
SIMGE_PAY = (60, 200)
SIMGESIZ_CAPA: tuple[tuple[int, str, int], ...] = ()
GLIF_BOY = _fz.GLIF_BOY
SIMGE_X = _fz.SIMGE_X
SIMGE_TOLERANS = _fz.SIMGE_TOLERANS
PENCERE = _fz.PENCERE
NUMARA_H = _fz.NUMARA_H
NUMARA_W_EN_COK = _fz.NUMARA_W_EN_COK
NUMARA_DX = _fz.NUMARA_DX
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ()
KUTU_UST: dict[tuple[int, str, int], int] = {}
# GOZLE (dosya 239 sag sutun): 7. sorunun son sikki (y ~446) ile 8. sorunun
# '2019 / AYT' rozeti (y 456) arasi 9 bos satir, BOSLUK'tan dar -> 8. kutunun
# ustu rozetin 3 px ustune sabitlenir (yoksa 7. kutu 19 px'e coker).
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {(239, "R", 1): 453}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
# GOZLE: T082_07 (dosya 177 sag sutun) sol kenar seridindeki 4 px, SOL
# sutunun 5. sorusundaki sekil duvarinin (x 360-362, y 142-164) ayraca tasan
# ucu; 7. sorunun kirpimi tam.
KENAR_GOZ_ONAY: tuple[str, ...] = ("BS24AF-T082_07",)
ORTAK_ONCUL_YOK: tuple[str, ...] = ()
YAKALANMAYAN_SORU: dict[int, tuple[int, ...]] = {}

SERIT_HUCRE_TARIFI = _fz.SERIT_HUCRE_TARIFI
ANAHTAR_NEREDEN = _fz.ANAHTAR_NEREDEN
ANAHTAR_DISLA_X = None
GLIF_KAPISI = False
GLIF_HARF_ESIK = _fz.GLIF_HARF_ESIK
GLIF_HARF_H = _fz.GLIF_HARF_H
GLIF_HARF_W_EN_COK = _fz.GLIF_HARF_W_EN_COK
HARF_NOKTA_SONRASI = True
HUCRE_BOSLUK = _fz.HUCRE_BOSLUK

BANT_Y_ALT = _fz.BANT_Y_ALT
BANT_TARIFI = _fz.BANT_TARIFI
BANT_KONU_TARIFI = _fz.BANT_KONU_TARIFI
BANT_TEST_NO_TARIFI = _fz.BANT_TEST_NO_TARIFI
BANT_KONU_KAPISI = False

# BS24FZ sutunlari; tek basili sayfada sag sutun 710 -> 698: devam sayfasinda
# sag ust kose susu y 75-83'te x 708'e iniyor (8. bolum, dosya 334-350; kirp
# 'kenar' kapisi). Olcum araligi ayni kalsin diye sag pay 30 -> 18.
SUTUNLAR = {0: {"L": (40, 366), "R": (360, 715)}, 1: {"L": (36, 360), "R": (356, 698)}}
SUTUN_OLCUM_PAY = {0: {"L": (20, 0), "R": (20, 0)}, 1: {"R": (20, 18)}}
UST_BANT = _fz.UST_BANT
SAYFA_ALTI = _fz.SAYFA_ALTI
SAYFA_ALTLIGI_Y = _fz.SAYFA_ALTLIGI_Y
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1426

KOK_KOD = "FIZ"
KOD_ONEKI = "FIZ-BS24AF"
ALAN = "FIZIK"
SINAV = "AYT"
SINIF = 11
HARITA_NEREDEN = "icindekiler: 8 bolum, 88 konu (dosya 5-7)"
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "1. B\u00d6L\u00dcM KUVVET"),
    (2, "2. B\u00d6L\u00dcM HAREKET"),
    (3, "3. B\u00d6L\u00dcM ELEKTR\u0130K"),
    (4, "4. B\u00d6L\u00dcM MANYET\u0130ZMA"),
    (5, "5. B\u00d6L\u00dcM DALGA MEKAN\u0130\u011e\u0130"),
    (
        6,
        "6. B\u00d6L\u00dcM ATOM F\u0130Z\u0130\u011e\u0130NE G\u0130R\u0130\u015e VE RADYOAKT\u0130V\u0130TE",
    ),
    (7, "7. B\u00d6L\u00dcM MODERN F\u0130Z\u0130K"),
    (
        8,
        "8. B\u00d6L\u00dcM MODERN F\u0130Z\u0130\u011e\u0130N TEKNOLOJ\u0130DEK\u0130 UYGULAMALARI",
    ),
)
# Icindekiler dosya 5-7 (gozle okundu), BASILI sayfa numarasiyla; konu = ayni
# ada sahip ardisik test grubu. 'OSYM Tipi', 'Simulasyon Testi', 'Sarmal Test'
# kendi konularidir. Dosya = basili + 1 (kapak ic yuzu yakalanmamis).
_ICINDEKILER_BASILI: tuple[tuple[int, str, int], ...] = (
    (1, "Vekt\u00f6rler", 9),
    (1, "Kesi\u015fen Kuvvetler", 17),
    (1, "Tork ve Denge", 23),
    (1, "\u00d6SYM Tipi-1", 31),
    (1, "A\u011f\u0131rl\u0131k ve K\u00fctle Merkezi", 33),
    (1, "Basit Makineler", 39),
    (1, "\u00d6SYM Tipi-2", 47),
    (1, "Sim\u00fclasyon Testi", 49),
    (1, "Sarmal Test-1", 51),
    (2, "Do\u011frusal Hareket", 55),
    (2, "Ba\u011f\u0131l Hareket", 61),
    (2, "Birle\u015fik Hareket", 65),
    (2, "\u00d6SYM Tipi-1", 69),
    (2, "Sim\u00fclasyon Testi-1", 71),
    (2, "Sarmal Test-2", 73),
    (2, "Newton'un Hareket Yasalar\u0131", 75),
    (2, "\u00d6SYM Tipi-2", 85),
    (2, "\u0130\u015f, G\u00fc\u00e7 ve Enerji", 87),
    (2, "\u00d6SYM Tipi-3", 97),
    (2, "Sim\u00fclasyon Testi-2", 99),
    (2, "Sarmal Test-3", 101),
    (2, "Yery\u00fcz\u00fcnde Hareket", 103),
    (2, "\u00d6SYM Tipi-4", 115),
    (2, "\u0130tme ve \u00c7izgisel Momentum", 117),
    (2, "\u00d6SYM Tipi-5", 127),
    (2, "Sarmal Test-4", 129),
    (2, "\u00c7embersel Hareket", 131),
    (2, "D\u00f6nerek \u00d6teleme Hareketi ve Eylemsizlik Momenti", 141),
    (2, "\u00d6SYM Tipi-6", 143),
    (2, "A\u00e7\u0131sal Momentum", 145),
    (2, "Kepler Yasalar\u0131 ve Genel \u00c7ekim Yasas\u0131", 149),
    (2, "Sarmal Test-5", 153),
    (2, "Basit Harmonik Hareket", 155),
    (2, "\u00d6SYM Tipi-7", 163),
    (2, "Sim\u00fclasyon Testi-3", 165),
    (2, "Sarmal Test-6", 167),
    (3, "Elektriksel Kuvvet", 171),
    (3, "Elektrik Alan", 177),
    (3, "Elektriksel Potansiyel", 183),
    (3, "Elektriksel Potansiyel Enerji", 187),
    (3, "\u00d6SYM Tipi-1", 189),
    (3, "Sarmal Test-7", 191),
    (
        3,
        "Y\u00fckl\u00fc Par\u00e7ac\u0131klar\u0131n D\u00fczg\u00fcn Elektrik Alandaki Hareketi",
        193,
    ),
    (3, "S\u0131\u011fa\u00e7lar", 197),
    (3, "\u00d6SYM Tipi-2", 203),
    (3, "Sim\u00fclasyon Testi", 205),
    (3, "Sarmal Test-8", 207),
    (4, "Manyetik Alan", 211),
    (4, "Manyetik Kuvvet", 217),
    (4, "\u00d6SYM Tipi-1", 227),
    (4, "Sarmal Test-9", 229),
    (4, "Elektromanyetik \u0130nd\u00fcksiyon", 231),
    (4, "Alternatif Ak\u0131m", 239),
    (4, "Transformat\u00f6rler", 245),
    (4, "\u00d6SYM Tipi-2", 247),
    (4, "Sim\u00fclasyon Testi", 249),
    (4, "Sarmal Test-10", 251),
    (5, "Su Dalgalar\u0131nda K\u0131r\u0131n\u0131m - Giri\u015fim", 255),
    (5, "I\u015f\u0131kta K\u0131r\u0131n\u0131m ve Giri\u015fim", 259),
    (5, "Doppler Olay\u0131", 263),
    (5, "Elektromanyetik Dalgalar", 265),
    (5, "\u00d6SYM Tipi", 269),
    (5, "Sim\u00fclasyon Testi", 271),
    (5, "Sarmal Test-11", 273),
    (6, "Atom Modelleri", 277),
    (6, "B\u00fcy\u00fck Patlama ve Evrenin Olu\u015fumu", 287),
    (6, "Atom Alt\u0131 Par\u00e7ac\u0131klar", 289),
    (6, "Radyoaktivite", 295),
    (6, "\u00d6SYM Tipi", 299),
    (6, "Sim\u00fclasyon Testi", 301),
    (6, "Sarmal Test-12", 303),
    (7, "\u00d6zel G\u00f6relilik", 307),
    (7, "Fotoelektrik Olay\u0131", 311),
    (7, "Compton Sa\u00e7\u0131lmas\u0131", 321),
    (
        7,
        "De Broglie Dalga Boyu ve I\u015f\u0131\u011f\u0131n \u0130kili Do\u011fas\u0131",
        323,
    ),
    (7, "\u00d6SYM Tipi", 325),
    (7, "Sim\u00fclasyon Testi", 327),
    (7, "Sarmal Test-13", 329),
    (8, "G\u00f6r\u00fcnt\u00fcleme Teknolojileri", 332),
    (8, "Yar\u0131 \u0130letken Teknolojisi", 334),
    (
        8,
        "S\u00fcper \u0130letkenlik - Nanoteknoloji - Lazer I\u015f\u0131nlar\u0131",
        336,
    ),
    (8, "\u00d6SYM Tipi", 338),
    (8, "Sim\u00fclasyon Testi", 340),
    (8, "Sarmal Test-14", 342),
    (8, "Sarmal Test-15", 344),
    (8, "Sarmal Test-16", 346),
    (8, "Sarmal Test-17", 348),
    (8, "Sarmal Test-18", 350),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s + 1) for b, ad, s in _ICINDEKILER_BASILI
)
SON_SAYFA = 352
BANT_ESLER: dict[str, str | tuple[str, ...]] = {}

KITAP_BASLIGI = "BILGI SARMAL 2024 AYT Fizik Soru Bankas\u0131"
GRUP_SORU = 60
SEKIL_SATIRI = True
TALIMAT_EK = ""

DERSLER = ("FIZIK",)
ESKI_KAYNAKLAR: tuple[str, ...] = ()
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Bilgi Sarmal Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "FIZ_BILGI_SARMAL_2024_AYT_YONTEM.md"

SONUC: dict = {}
