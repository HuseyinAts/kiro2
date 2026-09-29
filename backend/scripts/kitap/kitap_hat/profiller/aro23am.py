"""2023 AROMAT AYT Matematik Soru Bankasi (Aromat 'Gercek OSYM Deneyimi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 336 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya. ARO23MT ile ayni seri (profil ondan);
kesif: kitap_hat/kesif.py (_kesif_aro23am).

SAYFA DUZENI (olculdu; 30 Eyl 2026):
* 13 bolum, 64 konu (icindekiler s4); bolum acilis sayfalari glifsiz -> kapak.
* Ust bantta lacivert zeminde beyaz BUYUK HARFLE BOLUM adi, altinda acik mavi
  zeminde konu adi (icindekiler konu basligi); bordo 'TEST NN' rozeti.
* Cevap anahtari HER test sayfasinin sag altinda (ARO23MT ile ayni kutu):
  gri '1-D 2-B ...', numara sayfalar boyunca surer: iki gecisli test siniri.
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

KOD = "ARO23AM"
KAYNAK_ADI = "AROMAT 2023 AYT Matematik Soru Bankasi"
CIKTI_ONEK = "aromat_2023_ayt_matematik"
KLASOR = "Aromat-2023-Ayt-Matematik Soru Bankas\u0131"
VERAF = "c10"
BEKLENEN_SAYFA = 336
BEKLENEN_TEST = 153
TEST_SAYFALARI = (
    (6, 18),
    (20, 36),
    (38, 58),
    (60, 76),
    (78, 106),
    (108, 122),
    (124, 168),
    (170, 196),
    (198, 214),
    (216, 242),
    (244, 260),
    (262, 304),
    (306, 336),
)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
# Iki gecis (bas_listesi gecis1/yaz): seridi '1-' ile baslayan sayfalar; bolum
# sonu testleri uc sayfa (12 soru), digerleri iki.
BAS_SAYFALARI: tuple[int, ...] = (
    6,
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
    60,
    62,
    64,
    66,
    68,
    70,
    72,
    74,
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
    244,
    246,
    248,
    250,
    252,
    254,
    256,
    258,
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
    "Ust bantta lacivert zeminde beyaz BUYUK HARFLE bolum adi; altinda acik mavi "
    "zeminde konu adi (kucuk harf); sagda / solda bordo 'TEST NN' rozeti."
)
BANT_KONU_TARIFI = "acik mavi zemindeki (alt satir) konu adini, basildigi gibi"
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
KENAR_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["siyah"](a)
    return m


# --- harita (icindekiler s6; dosya = basili) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ARO23AM"
ALAN = "MATEMATIK"
SINAV = "AYT"
SINIF = 11
HARITA_NEREDEN = (
    "icindekiler (s4): 13 bolum, 64 konu basligi (dosya = basili); konu = test "
    "bandindaki alt satir konu adi (icindekiler adiyla kapidan gecer), sayfa "
    "araligi icindekiler sayfa numarasindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "1. B\u00d6L\u00dcM B\u00d6LME B\u00d6L\u00dcNEB\u0130LME"),
    (2, "2. B\u00d6L\u00dcM POL\u0130NOMLAR"),
    (3, "3. B\u00d6L\u00dcM \u0130K\u0130NC\u0130 DERECE DENKLEMLER"),
    (4, "4. B\u00d6L\u00dcM PARABOL"),
    (5, "5. B\u00d6L\u00dcM FONKS\u0130YONLARDA UYGULAMALAR"),
    (6, "6. B\u00d6L\u00dcM E\u015e\u0130TS\u0130ZL\u0130KLER"),
    (7, "7. B\u00d6L\u00dcM TR\u0130GONOMETR\u0130"),
    (8, "8. B\u00d6L\u00dcM LOGAR\u0130TMA"),
    (9, "9. B\u00d6L\u00dcM D\u0130Z\u0130LER"),
    (10, "10. B\u00d6L\u00dcM OLASILIK"),
    (11, "11. B\u00d6L\u00dcM L\u0130M\u0130T VE S\u00dcREKL\u0130L\u0130K"),
    (12, "12. B\u00d6L\u00dcM T\u00dcREV"),
    (13, "13. B\u00d6L\u00dcM \u0130NTEGRAL"),
)
# (bolum, icindekiler adi, baslangic, sinav, sinif). Sinif kitapta basili DEGIL:
# Sinif alani yer tutucu; gercek sinif _SINIF_BOLUM / _SINIF_KONU'dan.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "Asal \u00c7arpanlara Ay\u0131rma", 6, "AYT", 11),
    (1, "B\u00f6lme - B\u00f6l\u00fcnebilme", 10, "AYT", 11),
    (1, "EBOB - EKOK", 12, "AYT", 11),
    (1, "Periyodik Durumlar", 16, "AYT", 11),
    (2, "Polinom Kavram\u0131 ve Polinomlarla \u0130\u015flemler", 20, "AYT", 11),
    (2, "Polinomlar\u0131n \u00c7arpanlara Ayr\u0131lmas\u0131", 32, "AYT", 11),
    (3, "K\u00f6klerini Bulma - Diskriminant", 38, "AYT", 11),
    (
        3,
        "K\u00f6kleri ile Katsay\u0131lar\u0131 Aras\u0131ndaki \u0130li\u015fki",
        42,
        "AYT",
        11,
    ),
    (3, "De\u011fi\u015fken De\u011fi\u015ftirme", 48, "AYT", 11),
    (
        3,
        "\u0130kinci Dereceden \u0130ki Bilinmeyenli Denklem Sistemleri",
        50,
        "AYT",
        11,
    ),
    (
        3,
        "Karma\u015f\u0131k Say\u0131lar ve Karma\u015f\u0131k K\u00f6kler",
        54,
        "AYT",
        11,
    ),
    (4, "Parabol\u00fcn \u00c7izimi ve Uygulamalar\u0131", 60, "AYT", 11),
    (4, "Parabol\u00fcn Denklemini Bulma", 70, "AYT", 11),
    (5, "Fonksiyonlarda \u0130\u015flemler", 78, "AYT", 11),
    (5, "Par\u00e7al\u0131 Fonksiyon", 84, "AYT", 11),
    (5, "Bile\u015fke Fonksiyon ve Ters Fonksiyon", 86, "AYT", 11),
    (5, "Do\u011frusal Fonksiyon Uygulamalar\u0131", 90, "AYT", 11),
    (5, "Tek-\u00c7ift Fonksiyonlar ve Simetri \u00d6zellikleri", 92, "AYT", 11),
    (
        5,
        "Fonksiyonun Eksenleri Kesti\u011fi Noktalar, Pozitif ve Negatif De\u011ferler",
        94,
        "AYT",
        11,
    ),
    (
        5,
        "Ortalama De\u011fi\u015fim H\u0131z\u0131, Artan-Azalan Oldu\u011fu Aral\u0131klar, Maksimum Minimum Noktalar",
        96,
        "AYT",
        11,
    ),
    (5, "D\u00f6n\u00fc\u015f\u00fcmler", 102, "AYT", 11),
    (6, "\u0130kinci Dereceden Bir Bilinmeyenli E\u015fitsizlikler", 108, "AYT", 11),
    (
        6,
        "\u0130kinci Dereceden Bir Bilinmeyenli E\u015fitsizlik Sistemleri",
        120,
        "AYT",
        11,
    ),
    (
        7,
        "A\u00e7\u0131 \u00d6l\u00e7me Birimleri - Y\u00f6nl\u00fc A\u00e7\u0131 - Esas \u00d6l\u00e7\u00fc",
        124,
        "AYT",
        11,
    ),
    (
        7,
        "Dik \u00dc\u00e7gende Trigonometrik Ba\u011f\u0131nt\u0131lar",
        126,
        "AYT",
        11,
    ),
    (
        7,
        "Birim \u00c7ember - Trigonometrik Fonksiyonlar ve \u0130\u015faretleri",
        132,
        "AYT",
        11,
    ),
    (
        7,
        "Bir A\u00e7\u0131n\u0131n Trigonometrik De\u011ferinin Dar A\u00e7\u0131 Cinsinden Yaz\u0131lmas\u0131-S\u0131ralama",
        136,
        "AYT",
        11,
    ),
    (7, "Cosin\u00fcs ve Sin\u00fcs Teoremi", 142, "AYT", 11),
    (
        7,
        "Trigonometrik Fonksiyonlar\u0131n Grafikleri ve Periyotlar\u0131 - Ters Trigonometrik Fonksiyonlar",
        148,
        "AYT",
        11,
    ),
    (7, "Toplam - Fark ve \u0130ki Kat A\u00e7\u0131 Form\u00fclleri", 154, "AYT", 11),
    (7, "Trigonometrik Denklemler", 164, "AYT", 11),
    (8, "\u00dcsl\u00fc \u0130fadeler ve Denklemler", 170, "AYT", 11),
    (8, "K\u00f6kl\u00fc \u0130fadeler ve Denklemler", 174, "AYT", 11),
    (8, "\u00dcstel Fonksiyon ve Logaritma Fonksiyonu", 178, "AYT", 11),
    (8, "Logaritma \u00d6zellikleri", 184, "AYT", 11),
    (8, "\u00dcstel ve Logaritmik Denklemler", 192, "AYT", 11),
    (8, "\u00dcstel ve Logaritmik E\u015fitsizlikler", 194, "AYT", 11),
    (
        9,
        "Genel Terimi veya \u0130ndirgenme Ba\u011f\u0131nt\u0131s\u0131 Verilen Dizilerde \u0130\u015flemler",
        198,
        "AYT",
        11,
    ),
    (9, "Toplam Sembol\u00fc", 204, "AYT", 11),
    (9, "Aritmetik Dizi - Geometrik Dizi", 206, "AYT", 11),
    (10, "Perm\u00fctasyon", 216, "AYT", 11),
    (10, "Kombinasyon", 220, "AYT", 11),
    (10, "Olas\u0131l\u0131k", 224, "AYT", 11),
    (10, "Binom A\u00e7\u0131l\u0131m\u0131", 228, "AYT", 11),
    (10, "Ko\u015fullu Olas\u0131l\u0131k", 230, "AYT", 11),
    (10, "Ba\u011f\u0131ml\u0131 ve Ba\u011f\u0131ms\u0131z Olaylar", 234, "AYT", 11),
    (
        10,
        "Bile\u015fik Olaylar - Deneysel ve Teorik Olas\u0131l\u0131k",
        238,
        "AYT",
        11,
    ),
    (11, "Limitin \u00d6zellikleri ve Uygulamalar\u0131", 244, "AYT", 11),
    (11, "S\u00fcreklilik", 252, "AYT", 11),
    (11, "Limitte Belirsizlik Durumu", 256, "AYT", 11),
    (12, "Anl\u0131k De\u011fi\u015fim Oran\u0131 ve T\u00fcrev", 262, "AYT", 11),
    (
        12,
        "Bir Fonksiyonun Bir Noktada ve Aral\u0131kta T\u00fcrevlenebilirli\u011fi",
        270,
        "AYT",
        11,
    ),
    (
        12,
        "\u0130ki Fonksiyonun Toplam\u0131n\u0131n, Fark\u0131n\u0131n, \u00c7arp\u0131m\u0131n\u0131n ve B\u00f6l\u00fcm\u00fcn\u00fcn T\u00fcrevi",
        272,
        "AYT",
        11,
    ),
    (12, "\u0130ki Fonksiyonun Bile\u015fkesinin T\u00fcrevi", 278, "AYT", 11),
    (12, "Te\u011fet Denklemleri", 282, "AYT", 11),
    (
        12,
        "Bir Fonksiyonun Artan veya Azalan Oldu\u011fu Aral\u0131klar",
        288,  # icindekiler 286; s286-287 bandi Teget (TEST 03)
        "AYT",
        11,
    ),
    (12, "Ekstremum Noktalar", 292, "AYT", 11),
    (12, "Polinom Fonksiyonlar\u0131n\u0131n Grafikleri", 296, "AYT", 11),
    (12, "Maksimum ve Minimum Problemleri", 300, "AYT", 11),
    (13, "Belirsiz \u0130ntegral ve \u0130ntegral Alma Kurallar\u0131", 306, "AYT", 11),
    (13, "De\u011fi\u015fken De\u011fi\u015ftirme Y\u00f6ntemi", 312, "AYT", 11),
    (13, "Belirli \u0130ntegral", 316, "AYT", 11),
    (
        13,
        "Riemann Toplam\u0131 Yard\u0131m\u0131yla Yakla\u015f\u0131k Alan Hesab\u0131",
        324,
        "AYT",
        11,
    ),
    (13, "Belirli \u0130ntegral ile Alan Hesab\u0131", 328, "AYT", 11),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s) for b, ad, s, _, _ in _KONULAR
)


# MEB 2018 ortaogretim matematik programi unite sinifi (kitapta basili DEGIL):
# bolum varsayilani + konu istisnasi (bolum, konu sirasi).
_SINIF_BOLUM = {1: 9, 2: 10, 3: 10, 4: 11, 5: 11, 6: 11, 7: 11, 8: 12, 9: 12, 10: 10}
_SINIF_BOLUM.update({11: 12, 12: 12, 13: 12})
_SINIF_KONU = {(7, 7): 12, (7, 8): 12, (10, 5): 11, (10, 6): 11, (10, 7): 11}


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinav, _sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        sinif = _SINIF_KONU.get((b, say[b]), _SINIF_BOLUM[b])
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = (sinav, sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 336
BANT_ESLER: dict[str, str | tuple[str, ...]] = {
    "ORTALAMA DEGISIM HIZI, ARTAN-AZALAN OLDUGU ARALIKLAR, MAKSIMUM-MINIMUM NOKTALAR": (
        "ORTALAMA DEGISIM HIZI, ARTAN-AZALAN OLDUGU ARALIKLAR, MAKSIMUM MINIMUM NOKTALAR"
    ),
    "TRIGONOMETRIK FONKSIYONLARIN GRAFIKLERI VE PERIYOTLARI TERS TRIGONOMETRIK "
    "FONKSIYONLAR": (
        "TRIGONOMETRIK FONKSIYONLARIN GRAFIKLERI VE PERIYOTLARI-TERS TRIGONOMETRIK "
        "FONKSIYONLAR"
    ),
}

# --- kutu / kirpim ---
SUTUNLAR = {0: {"L": (33, 363), "R": (381, 709)}, 1: {"L": (33, 363), "R": (381, 709)}}
# Ust bant (lacivert serit + TEST rozeti) y 110da biter (s16 sutun olcumu); ilk
# numara y 131. Altlik: sayfa no dairesi y ~911, renkli cizgi y 917-921.
UST_BANT = 112
SAYFA_ALTI = 900
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1588

# --- metin ---
KITAP_BASLIGI = "AROMAT 2023 AYT Matematik Soru Bankas\u0131"
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
YONTEM_BELGESI = "MAT_AROMAT_2023_AYT_YONTEM.md"

SONUC: dict = {}
