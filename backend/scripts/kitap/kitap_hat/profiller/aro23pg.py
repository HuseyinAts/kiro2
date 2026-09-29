"""2023-2024 AROMAT Paragraf Soru Bankasi (Aromat 'Gercek OSYM Deneyimi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 304 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya. ARO23AM ile ayni seri (profil ondan);
kesif: kitap_hat/kesif.py (_kesif_aro23pg).

SAYFA DUZENI (olculdu; 30 Eyl 2026):
* 6 bolum, bolum basina tek konu (icindekiler s4); bolum acilis sayfalari
  (5, 57, 99, 159, 209, 259) glifsiz -> kapak.
* Ust bantta lacivert zeminde beyaz konu adi; yaninda bordo 'TEST NN' rozeti.
  Test iki sayfadir (4 + 4 soru), bazilari uc sayfa.
* CEVAP ANAHTARI KITAP SONUNDA TABLO (s303-304): bolum basliklarinin altinda
  'TEST NN : 1-A 2-B ...' satirlari; test sayfalarinda serit YOKTUR
  (ANAHTAR_HARICI, 142 satir; satir kirpimi etiketten sonra baslar).
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.profiller.akt20k0 import (  # noqa: F401
    BEYAZ_YARICAP,
    DISK_MERKEZ,
    GLIF_BOY,
    GLIF_GENISLET,
    HALKA,
    KART,
    LEKE,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
)
from scripts.kitap.kitap_hat.profiller.aro23af import SERIT_Y  # noqa: F401

KOD = "ARO23PG"
KAYNAK_ADI = "2023-2024 AROMAT Paragraf Soru Bankasi"
CIKTI_ONEK = "aromat_2024_paragraf"
KLASOR = "Aromat Paragraf Soru Bankas\u0131"
VERAF = "c11"
BEKLENEN_SAYFA = 304
BEKLENEN_TEST = 142
TEST_SAYFALARI = (
    (6, 56),
    (58, 98),
    (100, 158),
    (160, 208),
    (210, 258),
    (260, 302),
)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
# Iki gecis (bas_listesi gecis1/yaz): seridi '1-' ile baslayan sayfalar; bolum
# sonu testleri uc sayfa (12 soru), digerleri iki.
# Her bolumde test iki sayfa; bolumun SON testi uc (b6: bes) sayfa.
BAS_SAYFALARI: tuple[int, ...] = (
    6,
    8,
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
    54,
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
    160,
    162,
    164,
    166,
    168,
    170,
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
    210,
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
    254,
    256,
    260,
    262,
    264,
    266,
    268,
    270,
    272,
    274,
    276,
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
)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Anahtar kitap sonunda (ANAHTAR_HARICI): sayfa ici serit yok."""
    return None


def capa_gecerli(a: np.ndarray, ny: int, nx: int) -> bool:
    """Ortak metin kutusunun basligi ('3 - 4. sorulari ...') soru capasi
    degildir: kutu sutunun ustundedir (ny <= 200) ve numaranin 3-20 px
    ustunde sutun genisliginde cerceve cizgisi (>=150 koyu piksel) vardir;
    normal soruda ustte bosluk olur."""
    if ny > 200:
        return True
    sut = SUTUNLAR[0]["L" if nx < 370 else "R"]
    bolge = a[max(0, ny - 20) : max(0, ny - 3), sut[0] : sut[1]]
    if bolge.size == 0:
        return True
    koyu = (bolge.sum(2) < 700).sum(1)
    return bool(koyu.max() < 150)


def sayfa_turu(a: np.ndarray, n: int) -> str:
    return "test" if n in _TEST else "kapak"


# --- cevap anahtari: kitap sonu tablo (satir = test; etiket kirpim disi) ---
ANAHTAR_HARICI: dict[int, tuple[tuple[int, tuple[int, int, int, int]], ...]] = {
    1: ((303, (153, 173, 111, 362)),),
    2: ((303, (173, 193, 111, 362)),),
    3: ((303, (193, 213, 111, 362)),),
    4: ((303, (213, 233, 111, 362)),),
    5: ((303, (233, 253, 111, 362)),),
    6: ((303, (253, 273, 111, 362)),),
    7: ((303, (273, 293, 111, 362)),),
    8: ((303, (293, 313, 111, 362)),),
    9: ((303, (313, 333, 111, 362)),),
    10: ((303, (334, 353, 111, 362)),),
    11: ((303, (354, 373, 111, 362)),),
    12: ((303, (374, 393, 111, 362)),),
    13: ((303, (394, 413, 111, 362)),),
    14: ((303, (414, 433, 111, 362)),),
    15: ((303, (434, 453, 111, 362)),),
    16: ((303, (454, 473, 111, 362)),),
    17: ((303, (474, 493, 111, 362)),),
    18: ((303, (494, 513, 111, 362)),),
    19: ((303, (514, 533, 111, 362)),),
    20: ((303, (534, 553, 111, 362)),),
    21: ((303, (554, 573, 111, 362)),),
    22: ((303, (574, 593, 111, 362)),),
    23: ((303, (594, 613, 111, 362)),),
    24: ((303, (614, 633, 111, 362)),),
    25: ((303, (634, 653, 111, 362)),),
    26: ((303, (692, 711, 111, 362)),),
    27: ((303, (712, 731, 111, 362)),),
    28: ((303, (732, 750, 111, 362)),),
    29: ((303, (752, 770, 111, 362)),),
    30: ((303, (772, 790, 111, 362)),),
    31: ((303, (792, 811, 111, 362)),),
    32: ((303, (812, 831, 111, 362)),),
    33: ((303, (832, 851, 111, 362)),),
    34: ((303, (852, 871, 111, 362)),),
    35: ((303, (872, 891, 111, 362)),),
    36: ((303, (130, 149, 439, 692)),),
    37: ((303, (151, 171, 439, 692)),),
    38: ((303, (173, 192, 439, 692)),),
    39: ((303, (194, 213, 439, 692)),),
    40: ((303, (215, 234, 439, 692)),),
    41: ((303, (236, 256, 439, 692)),),
    42: ((303, (258, 277, 439, 692)),),
    43: ((303, (279, 298, 439, 692)),),
    44: ((303, (300, 319, 439, 692)),),
    45: ((303, (321, 341, 439, 692)),),
    46: ((303, (361, 380, 439, 692)),),
    47: ((303, (379, 399, 439, 692)),),
    48: ((303, (398, 417, 439, 692)),),
    49: ((303, (416, 435, 439, 692)),),
    50: ((303, (434, 453, 439, 692)),),
    51: ((303, (452, 472, 439, 692)),),
    52: ((303, (471, 490, 439, 692)),),
    53: ((303, (489, 508, 439, 692)),),
    54: ((303, (507, 526, 439, 692)),),
    55: ((303, (525, 545, 439, 692)),),
    56: ((303, (544, 563, 439, 692)),),
    57: ((303, (562, 581, 439, 692)),),
    58: ((303, (580, 599, 439, 692)),),
    59: ((303, (598, 618, 439, 692)),),
    60: ((303, (617, 636, 439, 692)),),
    61: ((303, (635, 654, 439, 692)),),
    62: ((303, (653, 672, 439, 692)),),
    63: ((303, (671, 691, 439, 692)),),
    64: ((303, (690, 709, 439, 692)),),
    65: ((303, (708, 727, 439, 692)),),
    66: ((303, (726, 745, 439, 692)),),
    67: ((303, (744, 764, 439, 692)),),
    68: ((303, (763, 782, 439, 692)),),
    69: ((303, (781, 800, 439, 692)),),
    70: ((303, (799, 818, 439, 692)),),
    71: ((303, (817, 837, 439, 692)),),
    72: ((303, (836, 855, 439, 692)),),
    73: ((303, (854, 873, 439, 692)),),
    74: ((303, (872, 891, 439, 692)),),
    75: ((304, (154, 173, 111, 362)),),
    76: ((304, (174, 193, 111, 362)),),
    77: ((304, (195, 214, 111, 362)),),
    78: ((304, (215, 234, 111, 362)),),
    79: ((304, (235, 255, 111, 362)),),
    80: ((304, (256, 274, 111, 362)),),
    81: ((304, (276, 296, 111, 362)),),
    82: ((304, (297, 316, 111, 362)),),
    83: ((304, (317, 336, 111, 362)),),
    84: ((304, (338, 357, 111, 362)),),
    85: ((304, (358, 377, 111, 362)),),
    86: ((304, (378, 398, 111, 362)),),
    87: ((304, (399, 418, 111, 362)),),
    88: ((304, (419, 439, 111, 362)),),
    89: ((304, (440, 459, 111, 362)),),
    90: ((304, (460, 479, 111, 362)),),
    91: ((304, (481, 500, 111, 362)),),
    92: ((304, (501, 520, 111, 362)),),
    93: ((304, (522, 541, 111, 362)),),
    94: ((304, (542, 561, 111, 362)),),
    95: ((304, (562, 582, 111, 362)),),
    96: ((304, (583, 602, 111, 362)),),
    97: ((304, (603, 623, 111, 362)),),
    98: ((304, (624, 643, 111, 362)),),
    99: ((304, (668, 687, 111, 362)),),
    100: ((304, (688, 707, 111, 362)),),
    101: ((304, (709, 728, 111, 362)),),
    102: ((304, (729, 748, 111, 362)),),
    103: ((304, (750, 769, 111, 362)),),
    104: ((304, (770, 788, 111, 362)),),
    105: ((304, (790, 810, 111, 362)),),
    106: ((304, (811, 830, 111, 362)),),
    107: ((304, (831, 851, 111, 362)),),
    108: ((304, (852, 871, 111, 362)),),
    109: ((304, (872, 891, 111, 362)),),
    110: ((304, (130, 149, 439, 692)),),
    111: ((304, (152, 171, 439, 692)),),
    112: ((304, (174, 193, 439, 692)),),
    113: ((304, (196, 215, 439, 692)),),
    114: ((304, (218, 237, 439, 692)),),
    115: ((304, (240, 259, 439, 692)),),
    116: ((304, (262, 281, 439, 692)),),
    117: ((304, (284, 303, 439, 692)),),
    118: ((304, (306, 325, 439, 692)),),
    119: ((304, (328, 347, 439, 692)),),
    120: ((304, (350, 369, 439, 692)),),
    121: ((304, (372, 391, 439, 692)),),
    122: ((304, (394, 413, 439, 692)),),
    123: ((304, (453, 472, 439, 692)),),
    124: ((304, (475, 494, 439, 692)),),
    125: ((304, (497, 516, 439, 692)),),
    126: ((304, (519, 538, 439, 692)),),
    127: ((304, (541, 560, 439, 692)),),
    128: ((304, (563, 582, 439, 692)),),
    129: ((304, (585, 604, 439, 692)),),
    130: ((304, (607, 626, 439, 692)),),
    131: ((304, (629, 648, 439, 692)),),
    132: ((304, (651, 670, 439, 692)),),
    133: ((304, (673, 692, 439, 692)),),
    134: ((304, (695, 714, 439, 692)),),
    135: ((304, (717, 736, 439, 692)),),
    136: ((304, (739, 758, 439, 692)),),
    137: ((304, (761, 780, 439, 692)),),
    138: ((304, (783, 802, 439, 692)),),
    139: ((304, (805, 824, 439, 692)),),
    140: ((304, (827, 846, 439, 692)),),
    141: ((304, (849, 868, 439, 692)),),
    142: ((304, (871, 892, 439, 692)),),
}


SERIT_HUCRE_TARIFI = (
    "Goruntu kitap sonundaki cevap anahtari tablosunun bir satiridir: gri "
    "'1-A 2-B ...' (numara, tire, harf). Soldaki 'TEST NN :' etiketi kirpimda "
    "yoktur."
)
ANAHTAR_NEREDEN = (
    "kitap sonundaki cevap anahtari tablosu (s303-304): bolum basliklari altinda "
    "'TEST NN : 1-A ...' satirlari + testin ilk sayfasinin ust bandi"
)
ANAHTAR_DISLA_X = None
GLIF_HARF_ESIK = 170
GLIF_HARF_H = (5, 10)
GLIF_HARF_W_EN_COK = 9
HUCRE_BOSLUK = 5
# Tablo hucresi '1-A': numara harfle ayni renkte, arada ~6 px tire.
GLIF_KAPISI = False  # kanal 1x 7 px yazida bolutlenemiyor; dogrulama A/B
HARF_NOKTA_SONRASI = True
HARF_NOKTA_W = 6
HARF_NOKTA_ARALIK = 4
HARF_NOKTA_DY = 3


BANT_Y_ALT = 112
BANT_TARIFI = (
    "Ust bantta lacivert zeminde beyaz konu adi; yaninda bordo 'TEST NN' rozeti."
)
BANT_KONU_TARIFI = "lacivert zemindeki konu adini, basildigi gibi"
BANT_TEST_NO_TARIFI = "bordo 'TEST NN' rozetindeki sayiyi"
BANT_KONU_KAPISI = True

# --- capa ---
SIMGE_X = {0: {"L": 25, "R": 359}, 1: {"L": 25, "R": 359}}
SIMGE_TOLERANS = 20
PENCERE = (-6, 40, 8, 60)
NUMARA_H = (6, 14)
NUMARA_W_EN_COK = 30
NUMARA_DX = (12, 54)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Ortak metin kutusu ('3 - 4. sorulari ...') altindaki ILK sorunun kutusuna
# katilir (kutu cercevesinin ust kenari; pg_kutu_ust.py ile olculdu).
KUTU_UST: dict[tuple[int, str, int], int] = {
    (14, "R", 0): 127,
    (22, "R", 0): 127,
    (30, "L", 0): 126,
    (46, "R", 0): 127,
    (54, "R", 0): 127,
    (56, "R", 0): 127,
    (58, "R", 0): 127,
    (60, "R", 0): 126,
    (62, "R", 0): 124,
    (66, "R", 0): 127,
    (68, "R", 0): 122,
    (72, "R", 0): 125,
    (74, "R", 0): 127,
    (86, "R", 0): 127,
    (88, "R", 0): 130,
    (92, "R", 0): 121,
    (94, "R", 0): 115,
    (100, "L", 0): 126,
    (106, "L", 0): 126,
    (124, "L", 0): 126,
    (138, "L", 0): 126,
    (160, "L", 0): 126,
    (168, "L", 0): 126,
    (172, "L", 0): 126,
    (176, "L", 0): 126,
    (198, "L", 0): 126,
    (212, "L", 0): 126,
    (246, "L", 0): 126,
    (247, "R", 0): 126,
    (256, "L", 0): 126,
    (260, "R", 0): 126,
    (262, "R", 0): 120,
    (264, "R", 0): 122,
    (266, "L", 0): 126,
    (266, "R", 0): 130,
    (268, "R", 0): 125,
    (270, "R", 0): 127,
    (271, "L", 0): 125,
    (272, "R", 0): 127,
    (273, "L", 0): 124,
    (274, "R", 0): 130,
    (276, "R", 0): 120,
    (278, "R", 0): 127,
    (279, "L", 0): 130,
    (279, "R", 0): 130,
    (280, "R", 0): 126,
    (282, "R", 0): 124,
    (283, "L", 0): 124,
    (284, "R", 0): 129,
    (285, "L", 0): 119,
    (286, "L", 0): 125,
    (286, "R", 0): 129,
    (288, "R", 0): 130,
    (289, "L", 0): 122,
    (290, "R", 0): 130,
    (292, "R", 0): 125,
    (293, "L", 0): 127,
    (294, "R", 0): 130,
    (295, "L", 0): 122,
    (295, "R", 0): 122,
    (296, "R", 0): 129,
    (297, "L", 0): 116,
    (298, "R", 0): 130,
    (301, "R", 0): 122,
}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
KENAR_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["siyah"](a)
    return m


# --- harita (icindekiler s6; dosya = basili) ---
KOK_KOD = "TUR"
KOD_ONEKI = "TUR-ARO23PG"
ALAN = "TURKCE"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s4): 6 bolum, bolum basina tek konu (dosya = basili); konu = "
    "test bandindaki konu adi (icindekiler adiyla kapidan gecer), sayfa araligi "
    "icindekiler sayfa numarasindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "1. B\u00d6L\u00dcM S\u00d6ZC\u00dcK VE C\u00dcMLE D\u00dcZEY\u0130NDE ANLAM"),
    (
        2,
        "2. B\u00d6L\u00dcM PARAGRAFTA ANLATIM B\u0130\u00c7\u0130MLER\u0130 VE D\u00dc\u015e\u00dcNCEY\u0130 GEL\u0130\u015eT\u0130RME YOLLARI",
    ),
    (3, "3. B\u00d6L\u00dcM ANA D\u00dc\u015e\u00dcNCE - KONU"),
    (4, "4. B\u00d6L\u00dcM PARAGRAFTA YARDIMCI D\u00dc\u015e\u00dcNCE"),
    (5, "5. B\u00d6L\u00dcM PARAGRAFTA YAPI"),
    (6, "6. B\u00d6L\u00dcM PARAGRAFTA YEN\u0130 NES\u0130L VE \u00c7OKLU SORULAR"),
)
# (bolum, icindekiler adi, baslangic, sinav, sinif). Sinif kitapta basili DEGIL:
# Sinif alani yer tutucu; gercek sinif _SINIF_BOLUM / _SINIF_KONU'dan.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "S\u00f6zc\u00fck ve C\u00fcmle D\u00fczeyinde Anlam", 5, "TYT", 9),
    (
        2,
        "Paragrafta Anlat\u0131m Bi\u00e7imleri ve D\u00fc\u015f\u00fcnceyi Geli\u015ftirme Yollar\u0131",
        57,
        "TYT",
        9,
    ),
    (3, "Ana D\u00fc\u015f\u00fcnce - Konu", 99, "TYT", 9),
    (4, "Paragrafta Yard\u0131mc\u0131 D\u00fc\u015f\u00fcnce", 159, "TYT", 9),
    (5, "Paragrafta Yap\u0131", 209, "TYT", 9),
    (6, "Paragrafta Yeni Nesil ve \u00c7oklu Sorular", 259, "TYT", 9),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s) for b, ad, s, _, _ in _KONULAR
)


# MEB 2018 ortaogretim matematik programi unite sinifi (kitapta basili DEGIL):
# bolum varsayilani + konu istisnasi (bolum, konu sirasi).
_SINIF_BOLUM = dict.fromkeys(range(1, 7), 9)
_SINIF_KONU: dict[tuple[int, int], int] = {}


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinav, _sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        sinif = _SINIF_KONU.get((b, say[b]), _SINIF_BOLUM[b])
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = (sinav, sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 302
BANT_ESLER: dict[str, str | tuple[str, ...]] = {}

# --- kutu / kirpim ---
SUTUNLAR = {0: {"L": (33, 363), "R": (381, 709)}, 1: {"L": (33, 363), "R": (381, 709)}}
# Ust bant (lacivert serit + TEST rozeti) y 110da biter (s16 sutun olcumu); ilk
# numara y 131. Altlik: sayfa no dairesi y ~911, renkli cizgi y 917-921.
UST_BANT = 112
SAYFA_ALTI = 900
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1083  # 1144 hucre - 61 capasiz soru (ortak metin kutusu)

# --- metin ---
KITAP_BASLIGI = "2023-2024 AROMAT Paragraf Soru Bankas\u0131"
GRUP_SORU = 60
SEKIL_SATIRI = True
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi SIYAH kalin basilidir; test iki sayfadir ve numara ikinci "
    "sayfada surer (5-8). Us, kok, kesir ve indisler basildigi gibi: `x^2`, "
    "`a_1`, `sqrt(3)`, `3/4`.\n"
    "GORUNMEYEN ISARET: ekran goruntusunde ince yatay cizgiler (eksi, kesir "
    "cizgisi parcasi, arti isaretinin yatay kolu) bazen HIC cikmamis olabilir: "
    "yerinde yalniz bosluk vardir. Boyle bir yere isaret TAHMIN ETME, '-' / '+' "
    "YAZMA: o yere `[??]` yaz ve `kaynak_kusuru`na 'isaret gorunmuyor: <yer>' "
    "yaz. Soluk ama pikselde secilebilen isaret basildigi gibi yazilir.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("TURKCE",)
ESKI_KAYNAKLAR: tuple[str, ...] = ()
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aromat Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "TUR_AROMAT_2024_PARAGRAF_YONTEM.md"

SONUC: dict = {}
