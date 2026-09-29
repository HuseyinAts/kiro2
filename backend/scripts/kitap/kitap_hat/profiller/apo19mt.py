"""2019-2020 APOTEMI TYT Matematik Soru Bankasi (Apotemi 'deneme konseptli' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 324 PNG (+ goruntu PDF'i); kart
(589,43)-(1331,1022). Yeni seri; kesif: kitap_hat/kesif.py (_kesif_apo19mt).

SAYFA DUZENI (olculdu, _a21_gecici/c4_*.py; 29 Eyl 2026):
* 11 bolum; bolum acilisi cift sayfa (8, 40, 58, 88, 120, 140, 156, 226, 246,
  266, 296: 'BOLUM N' + konu listesi), arkasindaki sayfa ilerleme tablosu.
* Her bolum 'Deneme - N' testlerinden olusur; testin ilk sayfasinda sag ya da
  sol ustte siyah kronometre kutusu (c4_saat.py: 122 test). Ust bantta
  'Deneme - N' ve 'BOLUM - M' (lacivert).
* Sayfada cevap seridi YOK: anahtar kitabin sonunda tablo (dosya 316-321,
  'DENEME - N  1-D 2-A ...' satirlari; 322-324 dosya 321'in kopyasi). Satir
  kutulari c4_anahtar_satir.py (bolum basliklari ve 'DENEME' etiketleri);
  sira == test sirasi (bolum basina satir sayisi kronometre sayisiyla ayni).
* Okuyucu simgesi numaranin solunda ayni satirda: L 72 / R 362 (iki parite),
  numara dx ~25-31, kirmizi.
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.profiller.akt20k0 import (  # noqa: F401
    ANAHTAR_KAPSAMI,
    BEYAZ_YARICAP,
    DISK_MERKEZ,
    GLIF_BOY,
    GLIF_GENISLET,
    HALKA,
    KART,
    LEKE,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
    TEST_SINIRI,
)

KOD = "APO19MT"
KAYNAK_ADI = "2019-2020 APOTEMI TYT Matematik Soru Bankasi"
CIKTI_ONEK = "apotemi_2019_tyt_matematik"
KLASOR = "2019-2020-Apotemi-Tyt Matematik Soru Bankas\u0131"
VERAF = "c4"
BEKLENEN_SAYFA = 324
BEKLENEN_TEST = 122
TEST_SAYFALARI = (
    (10, 39),
    (42, 57),
    (60, 87),
    (90, 119),
    (122, 139),
    (142, 155),
    (158, 175),
    (177, 225),
    (228, 245),
    (248, 265),
    (268, 295),
    (298, 313),
)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
# Kronometreli ilk sayfalar (c4_saat.py; bolum basina sayi anahtar tablosuyla ayni).
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
    42,
    45,
    48,
    51,
    54,
    56,
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
    90,
    93,
    96,
    99,
    102,
    105,
    108,
    111,
    114,
    117,
    122,
    125,
    128,
    131,
    134,
    137,
    142,
    144,
    146,
    148,
    150,
    152,
    154,
    158,
    160,
    162,
    164,
    167,
    170,
    173,
    177,
    180,
    183,
    186,
    189,
    192,
    195,
    198,
    201,
    204,
    207,
    210,
    213,
    216,
    219,
    222,
    224,
    228,
    230,
    232,
    234,
    236,
    238,
    240,
    242,
    244,
    248,
    250,
    252,
    254,
    256,
    258,
    260,
    262,
    264,
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
    298,
    300,
    302,
    304,
    306,
    308,
    310,
    312,
)
# Yakalama kusuru (gozle + piksel farki 0): dosya 176 = 175'in kopyasi (Bolum 7
# Deneme 7 s174 iki kez); 322-324 = 321 (anahtar son sayfasi). Bolum 7 Deneme 23'un
# 5-8. sorularinin sayfasi setin hicbir yerinde yok (dosya 222: 1-4, 223: 9-12).
KOPYA_SAYFALAR = frozenset({176, 322, 323, 324})
YAKALANMAYAN_SORU: dict[int, tuple[int, ...]] = {81: (5, 6, 7, 8)}


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    return None


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in _TEST:
        return "test"
    return "konu" if n < 314 and ortak.glifler(sys.modules[__name__], a) else "kapak"


# --- cevap anahtari: kitap sonu tablo ---
# test -> ((dosya, (y0, y1, x0, x1)),): 'DENEME - N' satiri, etiket dahil (okuyucu
# icin); glif kanalinda etiket ANAHTAR_DISLA_X ile beyazlatilir.
ANAHTAR_HARICI: dict[int, tuple[tuple[int, tuple[int, int, int, int]], ...]] = {
    1: ((316, (139, 164, 112, 632)),),
    2: ((316, (164, 189, 112, 632)),),
    3: ((316, (189, 214, 112, 632)),),
    4: ((316, (214, 239, 112, 632)),),
    5: ((316, (239, 266, 112, 632)),),
    6: ((316, (266, 291, 112, 632)),),
    7: ((316, (291, 316, 112, 632)),),
    8: ((316, (316, 341, 112, 632)),),
    9: ((316, (341, 365, 112, 632)),),
    10: ((316, (365, 390, 112, 632)),),
    11: ((316, (390, 415, 112, 632)),),
    12: ((316, (415, 440, 112, 632)),),
    13: ((316, (440, 464, 112, 632)),),
    14: ((316, (464, 489, 112, 632)),),
    15: ((316, (489, 515, 112, 632)),),
    16: ((316, (582, 629, 112, 632)),),
    17: ((316, (629, 676, 112, 632)),),
    18: ((316, (676, 722, 112, 632)),),
    19: ((316, (722, 768, 112, 632)),),
    20: ((316, (768, 813, 112, 632)),),
    21: ((316, (813, 859, 112, 632)),),
    22: ((317, (139, 164, 112, 632)),),
    23: ((317, (164, 189, 112, 632)),),
    24: ((317, (189, 214, 112, 632)),),
    25: ((317, (214, 239, 112, 632)),),
    26: ((317, (239, 263, 112, 632)),),
    27: ((317, (263, 288, 112, 632)),),
    28: ((317, (288, 313, 112, 632)),),
    29: ((317, (313, 337, 112, 632)),),
    30: ((317, (337, 362, 112, 632)),),
    31: ((317, (362, 387, 112, 632)),),
    32: ((317, (387, 412, 112, 632)),),
    33: ((317, (412, 436, 112, 632)),),
    34: ((317, (436, 461, 112, 632)),),
    35: ((317, (461, 486, 112, 632)),),
    36: ((317, (629, 673, 112, 632)),),
    37: ((317, (673, 717, 112, 632)),),
    38: ((317, (717, 760, 112, 632)),),
    39: ((317, (760, 804, 112, 632)),),
    40: ((317, (804, 847, 112, 632)),),
    41: ((318, (139, 183, 112, 632)),),
    42: ((318, (183, 226, 112, 632)),),
    43: ((318, (226, 270, 112, 632)),),
    44: ((318, (270, 313, 112, 632)),),
    45: ((318, (313, 358, 112, 632)),),
    46: ((318, (519, 563, 112, 632)),),
    47: ((318, (563, 607, 112, 632)),),
    48: ((318, (607, 650, 112, 632)),),
    49: ((318, (650, 693, 112, 632)),),
    50: ((318, (693, 737, 112, 632)),),
    51: ((318, (737, 781, 112, 632)),),
    52: ((319, (139, 164, 112, 632)),),
    53: ((319, (164, 189, 112, 632)),),
    54: ((319, (189, 214, 112, 632)),),
    55: ((319, (214, 239, 112, 632)),),
    56: ((319, (239, 263, 112, 632)),),
    57: ((319, (263, 288, 112, 632)),),
    58: ((319, (288, 313, 112, 632)),),
    59: ((319, (399, 425, 112, 632)),),
    60: ((319, (425, 449, 112, 632)),),
    61: ((319, (449, 474, 112, 632)),),
    62: ((319, (474, 499, 112, 632)),),
    63: ((319, (499, 523, 112, 632)),),
    64: ((319, (523, 548, 112, 632)),),
    65: ((319, (548, 573, 112, 632)),),
    66: ((319, (573, 598, 112, 632)),),
    67: ((319, (598, 622, 112, 632)),),
    68: ((319, (622, 647, 112, 632)),),
    69: ((319, (647, 672, 112, 632)),),
    70: ((319, (672, 697, 112, 632)),),
    71: ((319, (697, 721, 112, 632)),),
    72: ((319, (721, 746, 112, 632)),),
    73: ((319, (746, 771, 112, 632)),),
    74: ((319, (771, 795, 112, 632)),),
    75: ((319, (795, 820, 112, 632)),),
    76: ((319, (820, 846, 112, 632)),),
    77: ((320, (139, 164, 112, 632)),),
    78: ((320, (164, 189, 112, 632)),),
    79: ((320, (189, 214, 112, 632)),),
    80: ((320, (214, 239, 112, 632)),),
    81: ((320, (239, 263, 112, 632)),),
    82: ((320, (263, 289, 112, 632)),),
    83: ((320, (349, 374, 112, 632)),),
    84: ((320, (374, 399, 112, 632)),),
    85: ((320, (399, 424, 112, 632)),),
    86: ((320, (424, 448, 112, 632)),),
    87: ((320, (448, 473, 112, 632)),),
    88: ((320, (473, 498, 112, 632)),),
    89: ((320, (498, 522, 112, 632)),),
    90: ((320, (522, 547, 112, 632)),),
    91: ((320, (547, 573, 112, 632)),),
    92: ((320, (629, 654, 112, 632)),),
    93: ((320, (654, 679, 112, 632)),),
    94: ((320, (679, 704, 112, 632)),),
    95: ((320, (704, 729, 112, 632)),),
    96: ((320, (729, 753, 112, 632)),),
    97: ((320, (753, 778, 112, 632)),),
    98: ((320, (778, 803, 112, 632)),),
    99: ((320, (803, 828, 112, 632)),),
    100: ((320, (828, 853, 112, 632)),),
    101: ((321, (139, 164, 112, 632)),),
    102: ((321, (164, 189, 112, 632)),),
    103: ((321, (189, 214, 112, 632)),),
    104: ((321, (214, 239, 112, 632)),),
    105: ((321, (239, 263, 112, 632)),),
    106: ((321, (263, 288, 112, 632)),),
    107: ((321, (288, 313, 112, 632)),),
    108: ((321, (313, 337, 112, 632)),),
    109: ((321, (337, 362, 112, 632)),),
    110: ((321, (362, 387, 112, 632)),),
    111: ((321, (387, 412, 112, 632)),),
    112: ((321, (412, 436, 112, 632)),),
    113: ((321, (436, 461, 112, 632)),),
    114: ((321, (461, 486, 112, 632)),),
    115: ((321, (629, 654, 112, 632)),),
    116: ((321, (654, 679, 112, 632)),),
    117: ((321, (679, 704, 112, 632)),),
    118: ((321, (704, 729, 112, 632)),),
    119: ((321, (729, 753, 112, 632)),),
    120: ((321, (753, 778, 112, 632)),),
    121: ((321, (778, 803, 112, 632)),),
    122: ((321, (803, 828, 112, 632)),),
}
ANAHTAR_DISLA_X = (100, 194)
ANAHTAR_NEREDEN = (
    "kitap sonu 'CEVAP ANAHTARLARI' tablosu (dosya 316-321): bolum basina 'DENEME - N' "
    "satirlari, hucre 'numara-harf'; satir sirasi == test sirasi"
)
SERIT_HUCRE_TARIFI = (
    "Goruntu tablonun TEK satiridir: soldaki 'DENEME - N' etiketi HUCRE DEGILDIR. "
    'Hucreler "1-D", "2-A" ... bicimindedir (numara, tire, harf), bir ya da iki satir.'
)
BANT_Y_ALT = 100
BANT_TARIFI = (
    "Ust bantta lacivert kutularda 'Deneme - N' ve 'BOLUM - M' yazar (biri solda "
    "biri sagda); ilk sayfada ayrica kronometre resmi."
)
BANT_KONU_TARIFI = "'BOLUM - M' yazisini"
BANT_TEST_NO_TARIFI = "'Deneme - N' yazisindaki N sayisini"
BANT_KONU_KAPISI = False
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (6, 11)
GLIF_HARF_W_EN_COK = 10
HUCRE_BOSLUK = 5  # hucreler ('1-D  2-A') arasi en az bos sutun


def harf_bloblari(s: np.ndarray) -> list[tuple[slice, slice]]:
    """Anahtar satiri '1-D 2-A ...' (8 px yazi): satir bantlari -> bos sutunla
    ayrilan hucreler -> hucrede ust ucte birde murekkebi olan sutun gruplarinin
    SONUNCUSU harf (tire orta yukseklikte, ust ucte birde murekkep yok; tire
    harfe antialias ile yapistigi icin blob komsulugu kullanilmaz)."""
    mx, mn = s.max(axis=2).astype(int), s.min(axis=2).astype(int)
    siyah = (mn < GLIF_HARF_ESIK) & (mx - mn < 45)
    satir = siyah.any(axis=1)
    out: list[tuple[slice, slice]] = []
    y = 0
    while y < len(satir):
        if not satir[y]:
            y += 1
            continue
        y0 = y
        while y < len(satir) and satir[y]:
            y += 1
        if y - y0 < 6:
            continue
        bant = siyah[y0:y]
        ust = bant[: max(2, (y - y0) // 3)].any(axis=0)
        kol = bant.any(axis=0)
        x = 0
        while x < len(kol):
            if not kol[x]:
                x += 1
                continue
            xa, bos = x, 0
            while x < len(kol) and bos < HUCRE_BOSLUK:
                bos = 0 if kol[x] else bos + 1
                x += 1
            xb = x - bos
            grup, g = [], None
            for c in range(xa, xb):
                if ust[c] and g is None:
                    g = c
                elif not ust[c] and g is not None:
                    grup.append((g, c))
                    g = None
            if g is not None:
                grup.append((g, xb))
            if len(grup) >= 2:
                h0, h1 = grup[-1]
                out.append((slice(y0, y), slice(h0, h1)))
    return out


# --- capa ---
SIMGE_X = {0: {"L": 72, "R": 362}, 1: {"L": 72, "R": 362}}
SIMGE_TOLERANS = 12
PENCERE = (-6, 30, 16, 60)
NUMARA_H = (7, 12)
NUMARA_W_EN_COK = 30
NUMARA_DX = (18, 40)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# s216 R '4.': okuyucu simgesi numaranin 24 px ustunde (pencere disi, blob_yok).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ((216, "R", 693, 387),)
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()

# --- harita (bolum acilis sayfalari; konu = bolum, sayfa araligindan) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-APO19MT"
ALAN = "MATEMATIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "bolum acilis sayfalari (dosya 8, 40, 58, 88, 120, 140, 156, 226, 246, 266, 296: "
    "'BOLUM N' + konu listesi); icindekiler sayfasi yok. Bant yalniz 'BOLUM - M' "
    "tasir (BANT_KONU_KAPISI False): konu = bolum, sayfa araligindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "TEMEL KAVRAMLAR - SAYI BASAMAKLARI"),
    (2, "B\u00d6LME - B\u00d6L\u00dcNEB\u0130LME - EBOB - EKOK"),
    (3, "RASYONEL SAYILAR - MUTLAK DE\u011eER"),
    (4, "\u00dcSL\u00dc VE K\u00d6KL\u00dc SAYILAR"),
    (5, "\u00c7ARPANLARA AYIRMA - DENKLEM \u00c7\u00d6ZME"),
    (6, "ORAN - ORANTI - ORTALAMALAR"),
    (7, "PROBLEMLER"),
    (8, "MANTIK - K\u00dcMELER - KARTEZYEN \u00c7ARPIM"),
    (9, "FONKS\u0130YONLAR"),
    (10, "PERM\u00dcTASYON - KOMB\u0130NASYON - OLASILIK - \u0130STAT\u0130ST\u0130K"),
    (
        11,
        "POL\u0130NOMLAR - \u0130K\u0130NC\u0130 DERECEDEN DENKLEMLER - KARMA\u015eIK SAYILAR",
    ),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (
        1,
        "Temel Kavramlar, Tek ve \u00c7ift Say\u0131lar, Pozitif ve Negatif Say\u0131lar, Asal Say\u0131lar, Ard\u0131\u015f\u0131k Say\u0131lar, Fakt\u00f6riyel, Say\u0131 Basamaklar\u0131",
        8,
    ),
    (
        2,
        "B\u00f6lme - B\u00f6l\u00fcnebilme, Asal \u00c7arpanlara Ay\u0131rma, \u00d6zel Say\u0131 Problemleri, EBOB - EKOK",
        40,
    ),
    (
        3,
        "Rasyonel Say\u0131lar, S\u0131ralama, 1. Dereceden Denklem ve E\u015fitsizlikler, Mutlak De\u011fer",
        58,
    ),
    (4, "\u00dcsl\u00fc Say\u0131lar, K\u00f6kl\u00fc Say\u0131lar", 88),
    (5, "\u00c7arpanlara Ay\u0131rma, Denklem \u00c7\u00f6zme", 120),
    (6, "Oran - Orant\u0131, Orant\u0131 Problemleri, Ortalamalar", 140),
    (7, "Problemler", 156),
    (
        8,
        "Mant\u0131k, K\u00fcmeler, K\u00fcme Problemleri, Kartezyen \u00c7arp\u0131m",
        226,
    ),
    (9, "Fonksiyonlar, Fonksiyon \u00c7e\u015fitleri", 246),
    (
        10,
        "Perm\u00fctasyon, Kombinasyon, Binom, Olas\u0131l\u0131k, \u0130statistik",
        266,
    ),
    (
        11,
        "Polinomlar, \u0130kinci Dereceden Denklemler, Karma\u015f\u0131k Say\u0131lar",
        296,
    ),
)
SON_SAYFA = 313
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim ---
# Sayfa kenar cizgileri x 30 / 710 ve orta ayrac x 370 her satirda koyu (y 150-850
# boyunca 600+ piksel; kesif sutunu 28'den baslatinca 'cok kisa' 939) -> disarida.
# Ayracin ustundeki dikey 'APOTEMI' sekmesi x 361-380 (~93 satir; kirp kenar 571).
SUTUNLAR = {0: {"L": (33, 361), "R": (381, 707)}, 1: {"L": (33, 361), "R": (381, 707)}}
# Ust bant (lacivert 'Deneme - N' / 'BOLUM - M' + kirmizi cizgi) y 80-96; ilk
# numara y 113 (c4_kutu_ol.py s10). Altlik (sayfa no kutusu + noktalar, tam
# genislik cizgisi yok) y 887-907 -> sutun alti 884, alt tarama 886'da durur.
UST_BANT = 98
SAYFA_ALTI = 884
SAYFA_ALTLIGI_Y = 886
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1382

# --- metin ---
KITAP_BASLIGI = "2019-2020 APOTEM\u0130 TYT Matematik Soru Bankas\u0131"
GRUP_SORU = 60
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi kirmizi basilidir; her 'Deneme' 1'den baslar. Sekil / "
    "grafik / tablo icindeki sayilar soru onlara dayaniyorsa kisa satirlar "
    "halinde govdeye girer (Matematik yazimi tablosuna uyarak).\n"
    "GORUNMEYEN ISARET: bu kitabin ekran goruntulerinde ince yatay cizgiler "
    "(eksi, kesir cizgisi parcasi) bazen HIC cikmamis: yerinde yalniz bosluk "
    "vardir (ornek sikta 'A)  58' -- sayinin onunde bosluk). Boyle bir yere "
    "isaret TAHMIN ETME, '-' YAZMA: o yere `[??]` yaz ve `kaynak_kusuru`na "
    "'isaret gorunmuyor: <yer>' yaz. Soluk ama pikselde se\u00e7ilebilen isaret "
    "basildigi gibi yazilir.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("2019-2020-Apotemi-Tyt Matematik Soru Bankas\u0131",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Apotemi Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_APOTEMI_2019_TYT_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 40, "konu": 1, "test": 283},
    "harf": {"A": 128, "B": 282, "C": 346, "D": 403, "E": 223},
    "glif_hucre": 1386,
    "glif_uyum": 1380,
    "goz_teyit": {
        "T041#9": "C",
        "T067#10": "D",
        "T068#9": "D",
        "T089#10": "D",
        "T096#4": "D",
        "T101#10": "D",
    },
    "glif_disi": [],
    "metin_parca": 22,
    "farkli_soru": 247,
    "okunamaz": 159,
    "ithal": 1382,
    "beta": "1223/1382",
    "eski_modern": 6,
    "migration_no": 116,
    "onceki": "0115_akt25pr_beta_onay",
}
