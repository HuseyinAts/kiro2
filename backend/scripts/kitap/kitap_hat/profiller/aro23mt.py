"""2023-2024 AROMAT Matematik Soru Bankasi (Aromat 'Gercek OSYM Deneyimi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 400 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya. ARO23AF ile ayni seri (profil ondan);
kesif: kitap_hat/kesif.py (_kesif_aro23mt).

SAYFA DUZENI (olculdu; 29 Eyl 2026):
* 5 bolum, 19 konu; bolum acilis sayfalari (7, 89, 164-165, 282-283, 346-347)
  glifsiz, 'BOLUM NN' + konu listesi -> kapak. Arada test
  sayfalari; sayfa basina 2 sutun x 2 soru (sol sutun 1-2, sag 3-4).
* Ust bantta lacivert zeminde beyaz BUYUK HARFLE konu adi (icindekiler konu
  basligi) ve bordo 'TEST NN' rozeti (testin HER sayfasinda).
* Cevap anahtari HER sayfanin sag altinda: ince soluk kirmizi cerceveli beyaz
  kutuda gri '1-D 2-B 3-E 4-A' (tek satir), sagda bordo ok sekmesi (x ~662).
  Numara sayfalar boyunca surer (1-4, 5-8): test siniri iki gecisli
  (bas_listesi: seridi '1-' ile baslayan sayfa).
* Okuyucu simgesi numaranin solunda ayni satirda L 25 / R 359, numara siyah.
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
from scripts.kitap.kitap_hat.profiller.aro23af import (  # noqa: F401
    SERIT_Y,
    anahtar_bolgesi,
    harf_bloblari,
)

KOD = "ARO23MT"
KAYNAK_ADI = "2023-2024 AROMAT Matematik Soru Bankasi"
CIKTI_ONEK = "aromat_2024_tyt_matematik"
KLASOR = "Aromat -2023-2024-Matematik Soru Bankas\u0131"
VERAF = "c9"
BEKLENEN_SAYFA = 400
BEKLENEN_TEST = 223
TEST_SAYFALARI = (
    (8, 88),
    (90, 163),
    (166, 281),
    (284, 345),
    (348, 397),
)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
# Iki gecis (bas_listesi gecis1/yaz): seridi '1-' ile baslayan sayfalar; bolum
# sonu testleri uc sayfa (12 soru), digerleri iki.
BAS_SAYFALARI: tuple[int, ...] = (
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
    56,
    58,
    60,
    62,
    64,
    66,
    68,
    70,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    118,
    119,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
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
    208,
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
    258,
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
    306,
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
    332,
    334,
    336,
    338,
    340,
    342,
    344,
    348,
    350,
    352,
    354,
    356,
    358,
    360,
    362,
    364,
    366,
    368,
    370,
    372,
    374,
    376,
    378,
    380,
    382,
    384,
    386,
    388,
    390,
    392,
    394,
    396,
)


def sayfa_turu(a: np.ndarray, n: int) -> str:
    return "test" if n in _TEST else "kapak"


SERIT_HUCRE_TARIFI = (
    "Goruntu sayfanin sag altindaki cevap kutusudur: gri '1-D', '2-B' ... "
    "(numara, tire, harf), tek satir. Sagdaki bordo ok sekmesi hucre degildir."
)
ANAHTAR_NEREDEN = (
    "her test sayfasinin sag altindaki kutu ('1-D 2-B ...'; test iki sayfaysa "
    "iki kutu sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)
ANAHTAR_DISLA_X = None
GLIF_HARF_ESIK = 170
GLIF_HARF_H = (5, 10)
GLIF_HARF_W_EN_COK = 9
HUCRE_BOSLUK = 5


BANT_Y_ALT = 112
BANT_TARIFI = (
    "Ust bantta lacivert zeminde beyaz BUYUK HARFLE konu adi; altinda bordo "
    "'TEST NN' rozeti."
)
BANT_KONU_TARIFI = "lacivert zemindeki BUYUK HARFLI konu adini"
BANT_TEST_NO_TARIFI = "bordo 'TEST NN' rozetindeki sayiyi"
BANT_KONU_KAPISI = True

# --- capa ---
SIMGE_X = {0: {"L": 25, "R": 359}, 1: {"L": 25, "R": 359}}
SIMGE_TOLERANS = 14
PENCERE = (-6, 40, 8, 52)
NUMARA_H = (6, 14)
NUMARA_W_EN_COK = 30
NUMARA_DX = (12, 45)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ()
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
KENAR_GOZ_ONAY: tuple[str, ...] = ("ARO23MT-T138_01",)
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["siyah"](a)
    return m


# --- harita (icindekiler s6; dosya = basili) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ARO23MT"
ALAN = "MATEMATIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s6): 5 bolum, 19 konu basligi (dosya = basili); konu = test "
    "bandindaki BUYUK HARFLI konu adi (icindekiler adiyla kapidan gecer), sayfa "
    "araligi icindekiler sayfa numarasindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = tuple(
    (i, f"B\u00d6L\u00dcM - {i}") for i in range(1, 6)
)
# (bolum, icindekiler adi, baslangic, sinav, sinif). Sinif kitapta basili DEGIL:
# MEB 2018 matematik programi unite sinifi (9 / 10); kitap TYT.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "Yeni Nesil \u0130\u015flemler", 7, "TYT", 9),
    (1, "Temel Kavramlar", 18, "TYT", 9),
    (
        1,
        "Say\u0131 K\u00fcmeleri (Rasyonel Say\u0131lar - \u0130rrasyonel Say\u0131lar)",
        46,
        "TYT",
        9,
    ),
    (1, "B\u00f6lme - B\u00f6l\u00fcnebilme", 58, "TYT", 9),
    (2, "Birinci Derece Denklemler", 89, "TYT", 9),
    (2, "Birinci Derece E\u015fitsizlikler", 102, "TYT", 9),
    (2, "Mutlak De\u011fer", 112, "TYT", 9),
    (2, "\u00dcsl\u00fc Say\u0131lar", 124, "TYT", 9),
    (2, "K\u00f6kl\u00fc Say\u0131lar", 138, "TYT", 9),
    (2, "\u00c7arpanlara Ay\u0131rma", 152, "TYT", 10),
    (3, "Oran ve Orant\u0131", 164, "TYT", 9),
    (3, "Problemler", 180, "TYT", 9),
    (4, "Veri", 282, "TYT", 9),
    (4, "Mant\u0131k", 296, "TYT", 9),
    (4, "K\u00fcmeler", 308, "TYT", 9),
    (4, "Sayma ve Olas\u0131l\u0131k", 322, "TYT", 10),
    (5, "Fonksiyonlar", 346, "TYT", 10),
    (5, "Polinomlar", 372, "TYT", 10),
    (5, "\u0130kinci Derece Denklemler", 384, "TYT", 10),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s) for b, ad, s, _, _ in _KONULAR
)


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinav, sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = (sinav, sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 397
BANT_ESLER: dict[str, str | tuple[str, ...]] = {
    "SAYI KUMELERI": "SAYI KUMELERI (RASYONEL SAYILAR-IRRASYONEL SAYILAR)",
    "ORAN-ORANTI": "ORAN VE ORANTI",
}

# --- kutu / kirpim ---
SUTUNLAR = {0: {"L": (33, 363), "R": (381, 709)}, 1: {"L": (33, 363), "R": (381, 709)}}
# Ust bant (lacivert serit + TEST rozeti) y 110da biter (s16 sutun olcumu); ilk
# numara y 131. Altlik: sayfa no dairesi y ~911, renkli cizgi y 917-921.
UST_BANT = 112
SAYFA_ALTI = 900
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1605

# --- metin ---
KITAP_BASLIGI = "2023-2024 AROMAT TYT Matematik Soru Bankas\u0131"
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
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = ()
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aromat Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_AROMAT_2024_TYT_YONTEM.md"

SONUC: dict = {}
