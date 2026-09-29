"""2023-2024 AROMAT TYT Fizik Soru Bankasi (Aromat 'Gercek OSYM Deneyimi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 320 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya. ARO23AF ile ayni seri (profil ondan);
kesif: kitap_hat/kesif.py (_kesif_aro23tf).

SAYFA DUZENI (olculdu; 29 Eyl 2026):
* 10 bolum, her biri tek konu; bolum acilis sayfasi (7, 19, 39, 75, 99, 123,
  141, 177, 215, 253) glifsiz, 'BOLUM NN' + konu listesi -> kapak. Arada test
  sayfalari; sayfa basina 2 sutun x 2 soru (sol sutun 1-2, sag 3-4).
* Ust bantta lacivert zeminde beyaz BUYUK HARFLE konu adi (icindekiler konu
  basligi) ve bordo 'TEST NN' rozeti (testin HER sayfasinda).
* Cevap anahtari HER sayfanin sag altinda: ince soluk kirmizi cerceveli beyaz
  kutuda gri '1-D 2-B 3-E 4-A' (tek satir), sagda bordo ok sekmesi (x ~662).
  Numara sayfalar boyunca surer (1-4, 5-8): test siniri iki gecisli
  (bas_listesi: seridi '1-' ile baslayan sayfa).
* Okuyucu simgesi numaranin solunda ayni satirda L 25 / R 357, numara siyah.
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

KOD = "ARO23TF"
KAYNAK_ADI = "2023-2024 AROMAT Fizik Soru Bankasi"
CIKTI_ONEK = "aromat_2024_tyt_fizik"
KLASOR = "Aromat Tyt 2023 2024 Fizik Soru Bankas\u0131"
VERAF = "c8"
BEKLENEN_SAYFA = 320
BEKLENEN_TEST = 147
TEST_SAYFALARI = (
    (8, 18),
    (20, 38),
    (40, 74),
    (76, 98),
    (100, 122),
    (124, 140),
    (142, 176),
    (178, 214),
    (216, 252),
    (254, 320),
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
    20,
    22,
    24,
    26,
    28,
    30,
    32,
    34,
    36,
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
    124,
    126,
    128,
    130,
    132,
    134,
    136,
    138,
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
    170,
    172,
    174,
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
    306,
    308,
    310,
    312,
    314,
    316,
    318,
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
SIMGE_X = {0: {"L": 25, "R": 357}, 1: {"L": 25, "R": 357}}
SIMGE_TOLERANS = 14
PENCERE = (-6, 24, 8, 52)
NUMARA_H = (6, 14)
NUMARA_W_EN_COK = 30
NUMARA_DX = (12, 45)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ()
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
KENAR_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["siyah"](a)
    return m


# --- harita (icindekiler s6; dosya = basili) ---
KOK_KOD = "FIZ"
KOD_ONEKI = "FIZ-ARO23TF"
ALAN = "FIZIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s6): 12 bolum, 22 konu basligi (dosya = basili); konu = test "
    "bandindaki BUYUK HARFLI konu adi (icindekiler adiyla kapidan gecer), sayfa "
    "araligi icindekiler sayfa numarasindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = tuple(
    (i, f"B\u00d6L\u00dcM - {i}") for i in range(1, 11)
)
# (bolum, icindekiler adi, baslangic, sinav, sinif). Sinif kitapta basili DEGIL:
# MEB 2018 fizik programi unite sinifi (9 / 10); kitap TYT.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "Fizik Bilimine Giri\u015f", 7, "TYT", 9),
    (2, "Madde ve \u00d6zellikleri", 19, "TYT", 9),
    (3, "Hareket ve Kuvvet", 39, "TYT", 9),
    (4, "Enerji", 75, "TYT", 9),
    (5, "Is\u0131 ve S\u0131cakl\u0131k", 99, "TYT", 9),
    (6, "Elektrostatik", 123, "TYT", 10),
    (7, "Elektrik ve Manyetizma", 141, "TYT", 10),
    (8, "Bas\u0131n\u00e7 ve Kald\u0131rma Kuvveti", 177, "TYT", 10),
    (9, "Dalgalar", 215, "TYT", 10),
    (10, "Optik", 253, "TYT", 10),
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
SON_SAYFA = 320
BANT_ESLER: dict[str, str | tuple[str, ...]] = {}

# --- kutu / kirpim ---
SUTUNLAR = {0: {"L": (33, 363), "R": (381, 709)}, 1: {"L": (33, 363), "R": (381, 709)}}
# Ust bant (lacivert serit + TEST rozeti) y 110da biter (s16 sutun olcumu); ilk
# numara y 131. Altlik: sayfa no dairesi y ~911, renkli cizgi y 917-921.
UST_BANT = 112
SAYFA_ALTI = 900
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1137

# --- metin ---
KITAP_BASLIGI = "2023-2024 AROMAT TYT Fizik Soru Bankas\u0131"
GRUP_SORU = 60
SEKIL_SATIRI = True
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi SIYAH kalin basilidir; test iki sayfadir ve numara ikinci "
    "sayfada surer (5-8). Fizik birimleri ve indisler basildigi gibi: `m/s^2`, "
    "`F_1`, `v_0`, `10 N`; harfin ustunde vektor oku basiliysa harfi yaz, oku "
    "`kaynak_kusuru` sayma.\n"
    "GORUNMEYEN ISARET: ekran goruntusunde ince yatay cizgiler (eksi, kesir "
    "cizgisi parcasi, arti isaretinin yatay kolu) bazen HIC cikmamis olabilir: "
    "yerinde yalniz bosluk vardir. Boyle bir yere isaret TAHMIN ETME, '-' / '+' "
    "YAZMA: o yere `[??]` yaz ve `kaynak_kusuru`na 'isaret gorunmuyor: <yer>' "
    "yaz. Soluk ama pikselde secilebilen isaret basildigi gibi yazilir.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("FIZIK",)
ESKI_KAYNAKLAR: tuple[str, ...] = ()
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aromat Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "FIZ_AROMAT_2024_TYT_YONTEM.md"

SONUC: dict = {}
