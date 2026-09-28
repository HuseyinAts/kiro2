"""ACIL 2025 Matematigin Ilaci Polinom -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 288 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi (s20, s21 ... sayfa altinda basili; gozle).

SAYFA DUZENI (kontak sayfasi + olcum, 28 Eyl 2026)
-------------------------------------------------
* 5 bolum; her bolum 'BUNLARI OGREN' konu sayfalariyla baslar (bolum adi
  bantta). Konu sayfasinda 'N. SORU TIPI' + ORNEK/COZUM kutulari (kapsam
  DISI) ve altinda numarali coktan secmeli sorular (1..4, kapsam ICI).
* 'PEKISTIRME TESTI' ve 'KARMA TEST - N' sayfalari: 6 (ya da 4) soru;
  numara iki sayfa boyunca surer (1-6, 7-12).
* HER sayfanin kendi cevap seridi var: sag altta sayfa cizgisinin hemen
  ustunde duz metin '1.C 2.B 3.E ...' (numara ve harf ayni siyah).
* Test siniri: sayfanin ilk sorusunun numarasi '1' (TEST_SINIRI numara_1);
  anahtar dogrulamasi (numaralar 1..N) siniri ayrica denetler.
* Soru numarasi CAMGOBEGI (0,160,224); okuyucu simgesi 'N. SORU TIPI'
  basligina da konuyor (baslik da camgobegi) -> capa_gecerli: numaranin
  saginda camgobegi metin devam ediyorsa capa degil.
"""

from __future__ import annotations

import numpy as np

KOD = "ACL25PL"
KAYNAK_ADI = "ACIL 2025 Matematigin Ilaci Polinom"
CIKTI_ONEK = "acil_2025_ilac_polinom"
KLASOR = "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Polinom"
VERAF = "b4"
KART = (589, 43, 1331, 1022)
BEKLENEN_SAYFA = 288
BEKLENEN_TEST = 163
TEST_SAYFALARI = ((7, 63), (65, 123), (125, 171), (173, 229), (231, 260), (262, 287))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
BAS_SAYFALARI: tuple[int, ...] = (
    7,
    8,
    10,
    11,
    13,
    14,
    16,
    17,
    19,
    20,
    22,
    23,
    25,
    26,
    28,
    29,
    31,
    32,
    34,
    35,
    37,
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
    65,
    66,
    68,
    69,
    71,
    72,
    74,
    75,
    77,
    78,
    80,
    81,
    83,
    84,
    86,
    87,
    89,
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
    125,
    126,
    128,
    129,
    131,
    132,
    134,
    135,
    137,
    138,
    140,
    141,
    143,
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
    173,
    174,
    176,
    177,
    179,
    180,
    182,
    183,
    185,
    186,
    188,
    189,
    191,
    192,
    194,
    195,
    197,
    198,
    200,
    201,
    203,
    204,
    205,
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
    231,
    232,
    234,
    235,
    237,
    238,
    240,
    241,
    243,
    244,
    246,
    247,
    249,
    250,
    252,
    253,
    255,
    256,
    258,
    259,
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
)


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if anahtar_bolgesi(a, n) is not None:
        return "test"
    koyu = a[60:900].max(axis=2) < 120
    return "konu" if int(koyu.sum()) > 2000 else "kapak"


SERIT_Y = (900, 925)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Sag alt duz metin serit: y 900-925, x >= 400 koyu (max < 120) metin
    (s20-22 olculdu: metin y 913-920, sayfa cizgisi y 927 disarida)."""
    k = a[SERIT_Y[0] : SERIT_Y[1], 400:].max(axis=2) < 120
    if int(k.sum()) < 60:
        return None
    ys, xs = np.where(k)
    if int(ys.max()) - int(ys.min()) > 14:  # kapak (s1): tam yukseklik
        return None
    return [
        int(ys.min()) + SERIT_Y[0] - 2,
        int(ys.max()) + SERIT_Y[0] + 2,
        int(xs.min()) + 400,
        int(xs.max()) + 400,
    ]


# --- capa ---
GLIF_GENISLET = True
GLIF_BOY = (12, 17, 12, 17)
SIMGE_X = {1: {"L": 27, "R": 357}, 0: {"L": 42, "R": 372}}
SIMGE_TOLERANS = 16
PENCERE = (-6, 64, 6, 52)
NUMARA_H = (6, 16)
NUMARA_W_EN_COK = 30
NUMARA_DX = (8, 34)
SERIT_SIMGE_PAY = 10
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (b > 180) & (b - r > 80) & (g > r + 60)
    return m


def capa_gecerli(a: np.ndarray, ny: int, nx: int) -> bool:
    """'N. SORU TIPI' basligi: numaranin saginda AYNI SATIRDA camgobegi metin
    surer (p4_gecerli olcumu: baslik satir ici 208-216 px / 46-49 kolon;
    soru numarasinin sagindaki camgobegi cerceve/sekil <= 28 px / <= 6
    kolon)."""
    ic = numara_maskesi(a[ny + 2 : ny + 9, nx + 14 : nx + 90])
    return not (int(ic.sum()) > 100 and int(ic.any(axis=0).sum()) > 30)


# --- cevap anahtari ---
ANAHTAR_NEREDEN = (
    "her sayfanin sag altindaki duz metin cevap seridi (1.C 2.B ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)
BANT_Y_ALT = 62
BANT_TARIFI = (
    "Sari bantta ortada baslik: '\u2013 PEK\u0130\u015eT\u0130RME TEST\u0130 \u2013', "
    "'KARMA TEST - N' ya da bolum adi (solda 'BUNLARI \u00d6\u011eREN' kutusu varsa)."
)
BANT_KONU_TARIFI = "banttaki ortadaki BASLIGI (tire isaretleri olmadan)"
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (5, 12)
GLIF_HARF_W_EN_COK = 14
HARF_NOKTA_SONRASI = True

EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    # s86 sag sutun 3. soru: okuyucu simgesi YOK (gozle), capa mavi numaradan.
    (86, "R", 540, 397),
)

# --- harita (bolum = 'BUNLARI OGREN' bolum acilis sayfasi basligi; gozle) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ACL25PL"
ALAN = "MATEMATIK"
SINAV = "AYT"
SINIF = 10
HARITA_NEREDEN = (
    "bolum acilis sayfalari (s7, 65, 125, 173, 231; 'BUNLARI OGREN' bandinda bolum "
    "adi, gozle) + bolum kapak sayfalari (s64, 124, 172, 230 bos); test bandi "
    "konu adi TASIMIYOR ('PEKISTIRME TESTI', 'KARMA TEST - N') -> konu yalniz "
    "sayfa araligindan (BANT_KONU_KAPISI False)"
)
BANT_KONU_KAPISI = False
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "POL\u0130NOMLAR"),
    (2, "\u00c7ARPANLARA AYIRMA"),
    (3, "\u0130K\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    (4, "PARABOL"),
    (5, "E\u015e\u0130TS\u0130ZL\u0130KLER"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Polinomlar", 7),
    (2, "\u00c7arpanlara Ay\u0131rma", 65),
    (3, "\u0130kinci Dereceden Denklemler", 125),
    (4, "Parabol", 173),
    (5, "E\u015fitsizlikler", 231),
)
SON_SAYFA = 287
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (m3_sutun: test sayfalari x murekkep projeksiyonu) ---
# Orta ayrac: dikey cizgi (cift x 379, tek 362) + 'ACIL MATEMATIK' dikey yazi.
SUTUNLAR = {0: {"L": (10, 366), "R": (390, 715)}, 1: {"L": (8, 355), "R": (373, 700)}}
UST_BANT = 70
SAYFA_ALTI = 905
SERIT_PAY = 4
# Konu sayfalarinda ORNEK / COZUM kutulari kapsam disi: artik murekkep kapisi
# sutunun ILK kutusundan baslar (eksik soru = serit hucre sayisi kapisi).
ARTIK_ILK_KUTUDAN = True
# Ilk sorunun tavani: ustteki ayrac cizgisi ('ACIL MATEMATIK' yatay cizgi).
AYRAC_TAVAN = True
BEKLENEN_SORU = 1424
DISK_MERKEZ = (10, 8)
BEYAZ_YARICAP = 17
HALKA = (19, 23)
LEKE = None

# --- metin ---
KITAP_BASLIGI = "AC\u0130L 2025 Matemati\u011fin \u0130lac\u0131 Polinom"
GRUP_SORU = 51
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Bu kitapta soru numarasi KIRMIZI DEGIL, CAMGOBEGI (acik mavi) basilidir "
    "('1.', '2.' ...); `basili_no` icin sorunun solundaki bu numarayi oku. "
    "Numara iki sayfalik testlerde 7-12 diye surebilir; gordugun numarayi yaz.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Polinom",
)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_ACIL_2025_ILAC_POLINOM_YONTEM.md"

# Kitapta YANLIS basilmis soru numarasi (gozle, s36): 2. sayfanin sag sutun
# ortadaki sorusu '8.' basilmis (sol sutunda da '8.' var); serit '11.A',
# konum 11. Sira seritten; basili numara oldugu gibi, bayrak numara_baski_hatasi.
BASKI_NUMARA_HATASI = {"ACL25PL-T020_11": 8}

SONUC = {
    "sayfa_turu": {"kapak": 2, "konu": 10, "test": 276},
    "harf": {"A": 234, "B": 294, "C": 337, "D": 307, "E": 252},
    "glif_hucre": 1412,
    "glif_uyum": 1410,
    "goz_teyit": {"T073#4": "B", "T077#2": "B"},
    "glif_disi": [138],
    "metin_parca": 25,
    "farkli_soru": 90,
    "okunamaz": 5,
    "ithal": 1424,
    "beta": "1419/1424",
    "eski_modern": 38,
    "migration_no": 86,
    "onceki": "0085_acl24mg_beta_onay",
}
