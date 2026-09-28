"""ACIL 2025 Matematigin Ilaci Sayilar-2 -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 192 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi.

SAYFA DUZENI: Matematigin Ilaci serisi (acl25pl / acl25s1). Bu ciltte
(olculdu, s8-10): cevap seridi acl25pl gibi DUZ METIN ('1. B  2. C ...',
y 913-921, sayfa cizgisi y 927), soru numarasi acl25s1 gibi SIYAH kalin.
Kancalar: serit / sayfa turu acl25pl'den, numara / capa acl25s1'den. Test
siniri 1. gecis (sayfa basina) serit okumasindan (BAS_SAYFALARI).
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat.profiller.acl25pl import (  # noqa: F401
    ANAHTAR_KAPSAMI,
    ARTIK_ILK_KUTUDAN,
    AYRAC_TAVAN,
    BANT_KONU_KAPISI,
    BANT_KONU_TARIFI,
    BANT_TARIFI,
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
    NUMARA_W_EN_COK,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
    SIMGE_TOLERANS,
    TEST_SINIRI,
    anahtar_bolgesi,
)
from scripts.kitap.kitap_hat.profiller.acl25pl import sayfa_turu as _sayfa_turu_pl
from scripts.kitap.kitap_hat.profiller.acl25s1 import (  # noqa: F401
    NUMARA_DX,
    NUMARA_H,
    PENCERE,
    capa_gecerli,
    numara_maskesi,
)

KOD = "ACL25S2"
KAYNAK_ADI = "ACIL 2025 Matematigin Ilaci Sayilar-2"
CIKTI_ONEK = "acil_2025_ilac_sayilar2"
KLASOR = "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-2"
VERAF = "b6"
BEKLENEN_SAYFA = 192
BEKLENEN_TEST = 110
TEST_SAYFALARI = ((7, 18), (20, 44), (46, 80), (82, 118), (120, 153), (156, 191))
BAS_SAYFALARI: tuple[int, ...] = (
    7,
    8,
    10,
    11,
    13,
    14,
    16,
    17,
    20,
    21,
    23,
    25,
    27,
    29,
    31,
    33,
    35,
    37,
    39,
    41,
    43,
    46,
    47,
    49,
    50,
    52,
    53,
    55,
    56,
    57,
    58,
    60,
    61,
    62,
    63,
    64,
    65,
    67,
    69,
    71,
    73,
    75,
    77,
    79,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    91,
    92,
    94,
    95,
    96,
    97,
    99,
    101,
    103,
    105,
    107,
    109,
    111,
    113,
    115,
    117,
    120,
    121,
    123,
    124,
    126,
    127,
    129,
    130,
    132,
    133,
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
    156,
    157,
    159,
    160,
    162,
    163,
    165,
    166,
    168,
    169,
    171,
    172,
    174,
    175,
    177,
    178,
    180,
    182,
    184,
    186,
    188,
    190,
)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    # Okuyucu simgesi KONMAMIS sorular (gozle; capa siyah numaradan, numara_ara.py):
    (49, "L", 502, 49),
    (49, "R", 503, 379),
    (112, "L", 499, 66),
    (113, "L", 325, 49),
    (171, "L", 532, 49),
    (171, "R", 527, 379),
)
SIMGE_X = {1: {"L": 24, "R": 355}, 0: {"L": 40, "R": 371}}
HARF_NOKTA_SONRASI = True
HARF_NOKTA_ARALIK = 10
ANAHTAR_NEREDEN = (
    "her sayfanin sag altindaki duz metin cevap seridi (1. B  2. C ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)

# s1 kapak: alt kenardaki arka kapak metni serit bolgesine dusuyor (gozle).
KAPAK_SAYFALARI = (1,)


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in KAPAK_SAYFALARI:
        return "kapak"
    return str(_sayfa_turu_pl(a, n))


# --- harita (bolum acilis sayfalari 'BUNLARI OGREN' basligi; gozle) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ACL25S2"
ALAN = "MATEMATIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "bolum acilis sayfalari (s7, 46, 82, 120, 156; 'BUNLARI OGREN' bandinda bolum "
    "adi, gozle) + bolum kapak sayfalari (s45, 81, 119, 154-155); test bandi konu "
    "adi TASIMIYOR -> konu yalniz sayfa araligindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "DENKLEMLER"),
    (2, "E\u015e\u0130TS\u0130ZL\u0130KLER"),
    (3, "MUTLAK DE\u011eER"),
    (4, "\u00dcSL\u00dc SAYILAR"),
    (5, "K\u00d6KL\u00dc SAYILAR"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Denklemler", 7),
    (2, "E\u015fitsizlikler", 46),
    (3, "Mutlak De\u011fer", 82),
    (4, "\u00dcsl\u00fc Say\u0131lar", 120),
    (5, "K\u00f6kl\u00fc Say\u0131lar", 156),
)
SON_SAYFA = 191
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (acl25s1 ile ayni duzen) ---
SUTUNLAR = {0: {"L": (10, 371), "R": (390, 715)}, 1: {"L": (8, 354), "R": (373, 700)}}
UST_BANT = 70
SAYFA_ALTI = 922
SERIT_ORTUSME_EN_AZ = 60
BEKLENEN_SORU = 938
LEKE = None

# --- metin ---
KITAP_BASLIGI = "AC\u0130L 2025 Matemati\u011fin \u0130lac\u0131 Say\u0131lar-2"
GRUP_SORU = 51
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Bu kitapta soru numarasi KIRMIZI DEGIL, SIYAH kalin basilidir ('1.', '2.' ...); "
    "`basili_no` icin sorunun solundaki bu numarayi oku. Numara iki sayfalik "
    "testlerde 7-12 diye surebilir; gordugun numarayi yaz. Bazi sorular ortak bir "
    "bilgi kutusuna dayanir ('5. ve 6. sorulari asagidaki bilgilere gore "
    "cevaplayiniz'): kutu kirpimda gorunuyorsa govdeye yaz, gorunmuyorsa "
    "kaynak_kusuru'na 'ortak bilgi kutusu kirpimda yok' yaz.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-2",
)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
# T064_11 altinda 'AYT / 2023' cikmis soru etiketi (gozle, kirpimda basili).
BEKLENEN_ETIKET = 1
YONTEM_BELGESI = "MAT_ACIL_2025_ILAC_SAYILAR2_YONTEM.md"

# Ayrac cizgisinin ortasindaki 'ACIL MATEMATIK' logosu cizginin ~5 px altina
# iniyor (s49 T024_01 kenar): tavan = cizgi + 7.
AYRAC_PAY = 7

SONUC = {
    "sayfa_turu": {"kapak": 4, "konu": 9, "test": 179},
    "harf": {"A": 151, "B": 176, "C": 253, "D": 207, "E": 151},
    "glif_hucre": 938,
    "glif_uyum": 926,
    "goz_teyit": {
        "T010#12": "B",
        "T011#6": "E",
        "T012#6": "B",
        "T015#6": "B",
        "T030#4": "B",
        "T037#6": "E",
        "T040#4": "B",
        "T054#12": "B",
        "T072#6": "B",
        "T076#6": "E",
        "T083#6": "B",
        "T106#6": "B",
    },
    "glif_disi": [],
    "metin_parca": 17,
    "farkli_soru": 70,
    "okunamaz": 5,
    "ithal": 938,
    "beta": "933/938",
    "eski_modern": 43,
    "migration_no": 93,
    "onceki": "0092_acl25s1_beta_onay",
}
