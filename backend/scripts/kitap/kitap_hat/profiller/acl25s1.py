"""ACIL 2025 Matematigin Ilaci Sayilar-1 -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 176 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi.

SAYFA DUZENI: acl25pl (Matematigin Ilaci Polinom) serisi, ama bu ciltte
(olculdu, s7-11, s43):
* soru numarasi SIYAH kalin ('1.'); 'N. Soru Tipi' basligi kirmizi;
* cevap seridi sag altta CERCEVELI tablo ('1. E | 2. D ...'): ust cizgi
  y 884, alt cizgi y 902 (s7'de alt cizgi soluk -> alt = ust + 18);
* 'BUNLARI OGREN' konu sayfalarinda ORNEK / COZUM kutulari (renkli zemin,
  kapsam DISI; kutu basindaki okuyucu simgesi capa DEGIL -> capa_gecerli:
  numara zemini beyaz olmali) + numarali coktan secmeli sorular;
* 'PEKISTIRME TESTI' / 'KARMA TEST - N': numara iki sayfa boyunca surer.
Test siniri 1. gecis (sayfa basina) serit okumasindan (BAS_SAYFALARI).
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
)

KOD = "ACL25S1"
KAYNAK_ADI = "ACIL 2025 Matematigin Ilaci Sayilar-1"
CIKTI_ONEK = "acil_2025_ilac_sayilar1"
KLASOR = "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-1"
VERAF = "b5"
BEKLENEN_SAYFA = 176
BEKLENEN_TEST = 97
TEST_SAYFALARI = ((7, 40), (43, 80), (83, 106), (109, 138), (141, 176))
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
    43,
    44,
    46,
    47,
    49,
    50,
    52,
    53,
    55,
    56,
    58,
    59,
    61,
    62,
    64,
    65,
    67,
    69,
    71,
    73,
    75,
    77,
    79,
    83,
    84,
    86,
    87,
    89,
    90,
    92,
    93,
    95,
    97,
    99,
    101,
    103,
    105,
    109,
    110,
    112,
    113,
    115,
    116,
    118,
    119,
    121,
    122,
    124,
    125,
    127,
    129,
    131,
    133,
    135,
    137,
    141,
    142,
    143,
    144,
    146,
    147,
    149,
    150,
    152,
    153,
    155,
    156,
    157,
    158,
    160,
    161,
    163,
    165,
    167,
    169,
    171,
    173,
    175,
)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    # s146 konu sayfasi 1. ve 2. soru: okuyucu simgesi YOK (gozle); capa numaradan.
    (146, "L", 645, 66),
    (146, "R", 642, 396),
)
SIMGE_X = {1: {"L": 24, "R": 355}, 0: {"L": 42, "R": 373}}
# Bu ciltte numara SIYAH: pencere orta ayracin siyah dikey harflerini (tek
# sayfa x 356-368) almamali -> x0 = +14; numara simgeden 22-36 px sagda (s160
# 1. soru dx 36); 'N. Soru Tipi' basligindaki siyah kelime blobu (h 7) numara
# degil -> yukseklik >= 9 (numara '1.' h 10-11; olculdu s7-12, 89, 160, 171).
PENCERE = (-6, 64, 14, 52)
NUMARA_H = (9, 16)
NUMARA_DX = (14, 40)
HARF_NOKTA_SONRASI = True
ANAHTAR_NEREDEN = (
    "her sayfanin sag altindaki cerceveli cevap seridi (1. E | 2. D ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)

SERIT_YUKSEKLIK = 18


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    k = a[:, 300:].max(axis=2) < 190
    ys = [y for y in range(876, 912) if 280 <= int(k[y].sum()) <= 330]
    if not ys:
        return None
    y0 = ys[0] if ys[0] < 893 else ys[0] - SERIT_YUKSEKLIK
    # x araligi = satirdaki EN UZUN kesintisiz kosu (cerceve cizgisi); ayni
    # satira inen sekil pikselleri disarida (s76: sekil x 300'den seride iniyor).
    x0, x1 = _en_uzun_kosu(k[ys[0]])
    return [y0, y0 + SERIT_YUKSEKLIK, x0 + 300, x1 + 300]


def _en_uzun_kosu(v: np.ndarray, bosluk: int = 30) -> tuple[int, int]:
    """<= bosluk px araliklarla birlesen kosularin en uzunu (cerceve cizgisi
    hucre sinirlarinda kisa kesintili; sekil pikselleri uzakta)."""
    kosu: list[list[int]] = []
    bas = None
    for i, x in enumerate([*v.tolist(), False]):
        if x and bas is None:
            bas = i
        elif not x and bas is not None:
            if kosu and bas - kosu[-1][1] <= bosluk:
                kosu[-1][1] = i - 1
            else:
                kosu.append([bas, i - 1])
            bas = None
    en = max(kosu, key=lambda k: k[1] - k[0])
    return en[0], en[1]


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if anahtar_bolgesi(a, n) is not None:
        return "test"
    koyu = a[60:860].max(axis=2) < 120
    return "konu" if int(koyu.sum()) > 2000 else "kapak"


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    """Siyah kalin basili numara."""
    m: np.ndarray = (a.max(axis=2) < 100) & (a.max(axis=2) - a.min(axis=2) < 40)
    return m


def capa_gecerli(a: np.ndarray, ny: int, nx: int) -> bool:
    """ORNEK / COZUM kutusu: numaranin zemini renkli (acik sari / pembe)."""
    w = a[max(0, ny - 3) : ny + 14, max(0, nx - 6) : nx + 40]
    renkli = ((w.max(axis=2) - w.min(axis=2)) > 12) & (w.min(axis=2) > 150)
    return float(renkli.mean()) < 0.3


# Seritte nokta ile harf arasinda bosluk var ('1. E'): harf noktadan <= 10 px sagda.
HARF_NOKTA_ARALIK = 10

# --- harita (bolum acilis sayfalari 'BUNLARI OGREN' basligi; gozle) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ACL25S1"
ALAN = "MATEMATIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "bolum acilis sayfalari (s7, 43, 83, 109, 141; 'BUNLARI OGREN' bandinda bolum "
    "adi, gozle) + bolum kapak sayfalari (s41-42, 81-82, 107-108, 139-140); test "
    "bandi konu adi TASIMIYOR -> konu yalniz sayfa araligindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "SAYILAR"),
    (2, "ASAL SAYILAR"),
    (3, "SAYI BASAMAKLARI"),
    (4, "B\u00d6LME \u0130\u015eLEM\u0130"),
    (5, "RASYONEL SAYILAR"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Say\u0131lar", 7),
    (2, "Asal Say\u0131lar", 43),
    (3, "Say\u0131 Basamaklar\u0131", 83),
    (4, "B\u00f6lme \u0130\u015flemi", 109),
    (5, "Rasyonel Say\u0131lar", 141),
)
SON_SAYFA = 176
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (m3_sutun; acl25pl ile ayni duzen) ---
SUTUNLAR = {0: {"L": (10, 371), "R": (390, 715)}, 1: {"L": (8, 354), "R": (373, 700)}}
UST_BANT = 70
# Sol sutun seritle ortusmez: alt sinir sayfa cizgisi (y 927) ustu. Ilk
# denemede 878 alindi, 10 sayfada sol sutun son sorusu kesildi (alt_tara).
SAYFA_ALTI = 922
BEKLENEN_SORU = 915
LEKE = None

# --- metin ---
KITAP_BASLIGI = "AC\u0130L 2025 Matemati\u011fin \u0130lac\u0131 Say\u0131lar-1"
GRUP_SORU = 51
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Bu kitapta soru numarasi KIRMIZI DEGIL, SIYAH kalin basilidir ('1.', '2.' ...); "
    "`basili_no` icin sorunun solundaki bu numarayi oku. Numara iki sayfalik "
    "testlerde 7-12 diye surebilir; gordugun numarayi yaz.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "AC\u0130L-2025-Matemati\u011fin \u0130lac\u0131 Say\u0131lar-1",
)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_ACIL_2025_ILAC_SAYILAR1_YONTEM.md"

# Serit sol sutuna yalniz kenarindan (<= 60 px) girerse sol sutun alt siniri
# SAYFA_ALTI (s80: serit x 351'den basliyor, sol sutun sekilli sorusu seridin
# yaninda y 920'ye iniyor; ilk kirpimda D/E siklari kesildi).
SERIT_ORTUSME_EN_AZ = 60

SONUC = {
    "sayfa_turu": {"kapak": 5, "konu": 9, "test": 162},
    "harf": {"A": 149, "B": 171, "C": 175, "D": 236, "E": 184},
    "glif_hucre": 911,
    "glif_uyum": 911,
    "goz_teyit": {},
    "glif_disi": [3],
    "metin_parca": 17,
    "farkli_soru": 50,
    "okunamaz": 0,
    "ithal": 915,
    "beta": "915/915",
    "eski_modern": 19,
    "migration_no": 90,
    "onceki": "0089_acl24mg_kesik_duzeltme",
}
