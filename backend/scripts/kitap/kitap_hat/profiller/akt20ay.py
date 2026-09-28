"""2019-2020 Aktif AYT Kimya (Aktif Ogrenme duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 416 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya (unite acilislari 7, 57, 87 ... 407; gozle).
Icindekiler s6: 12 unite (Modern Atom Teorisi / Periyodik Sistem .. Enerji
Kaynaklari ve Bilimsel Gelismeler).

SAYFA DUZENI: AKT20K0 (Aktif 0'dan Kimya) ile ayni seri; kancalar oradan
(sayfa turu, iki kutulu serit, ust_bant, SUS_BOLGELERI). Farklar (olculdu,
_a21_gecici/ak_capa.py, ak_serit.py, ak_kolon.py; 28 Eyl 2026):
* Soru numarasi KIRMIZI (ortak.kirmizi; 142 test sayfasinda 936 glifin
  936'si numarali, dx 29-40).
* Yerlesim pariteye gore kayar: okuyucu simgesi cift sayfa L 60 / R 356,
  tek sayfa L 52 / R 344; orta ayrac cift x 376, tek x 366; kart kenar
  golgesi x 29 / 712.
* Serit kutulari y 912-970 (s23), kutular x 30-330 / 410-710; bazi sorularda
  y 860 civarinda acik mavi tablo -> arama penceresi 900'den.
* 142 test sayfasi, 13 blok.
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat import ortak
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
    SUS_BOLGELERI,
    TEST_SINIRI,
    UST_BANT,
    sayfa_turu,
    serit_kutusu,
)


def ust_bant(a: np.ndarray) -> int:
    """Ust bandin alti: doygun pikseli > 150 olan ILK satirdan (bant ustu)
    asagi, doygun pikseli > 100 surdukce (bu ciltte bandin egik alt kenari /
    kahverengi serit 131-160 px: s50 y 77-79, s77 y 89-94; AKT20K0'nun
    'son > 150 satir' olcumu onlari birakip kutu artik kapisina takiliyordu)
    + 2. Bitisik olmayan asagidaki renkli sekiller sayilmaz."""
    z = a[20:140, 20:720]
    say = ((z.max(axis=2).astype(int) - z.min(axis=2)) > 60).sum(axis=1)
    ys = np.where(say > 150)[0]
    if not len(ys):
        return int(UST_BANT)
    y = int(ys[0])
    while y + 1 < len(say) and say[y + 1] > 100:
        y += 1
    return y + 20 + 2


KOD = "AKT20AY"
KAYNAK_ADI = "2019-2020 Aktif AYT Kimya"
CIKTI_ONEK = "aktif_2020_ayt_kimya"
KLASOR = "Aktif Ogrenme Ayt Kimya 2019 2020"
VERAF = "b9"
BEKLENEN_SAYFA = 416
BEKLENEN_TEST = 71
TEST_SAYFALARI = (
    (23, 32),
    (49, 56),
    (77, 86),
    (107, 118),
    (133, 140),
    (161, 170),
    (197, 208),
    (231, 244),
    (277, 294),
    (311, 318),
    (355, 374),
    (399, 406),
    (413, 416),
)
BAS_SAYFALARI: tuple[int, ...] = (
    23,
    25,
    27,
    29,
    31,
    49,
    51,
    53,
    55,
    77,
    79,
    81,
    83,
    85,
    107,
    109,
    111,
    113,
    115,
    117,
    133,
    135,
    137,
    139,
    161,
    163,
    165,
    167,
    169,
    197,
    199,
    201,
    203,
    205,
    207,
    231,
    233,
    235,
    237,
    239,
    241,
    243,
    277,
    279,
    281,
    283,
    285,
    287,
    289,
    291,
    293,
    311,
    313,
    315,
    317,
    355,
    357,
    359,
    361,
    363,
    365,
    367,
    369,
    371,
    373,
    399,
    401,
    403,
    405,
    413,
    415,
)

SERIT_Y = (900, 979)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """AKT20K0 iki kutulu serit olcumu; arama y 900'den (s. modul notu)."""
    kutu: list[int] | None = serit_kutusu(a, SERIT_Y)
    return kutu


# Sayfa numarasi rakamlari tek sayfa x ~355-375, cift ~365-385; sol kutunun
# son harfi cift sayfada x ~326'ya kadar (322 ile basliyan pencere onu da
# siliyordu: her testte 1 glif eksik).
ANAHTAR_DISLA_X = (335, 405)

# --- capa ---
SIMGE_X = {0: {"L": 61, "R": 357}, 1: {"L": 53, "R": 345}}
SIMGE_TOLERANS = 12
PENCERE = (-10, 42, 4, 64)
NUMARA_H = (8, 14)
NUMARA_W_EN_COK = 22
NUMARA_DX = (25, 44)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Okuyucu simgesi KONMAMIS soru (gozle; capa kirmizi numaradan): s134 sag '13.'.
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ((134, "R", 470, 394),)
# Sutun basinda numarasiz ORTAK bilgi ('x, ..., y. sorulari yukaridaki
# grafige / bilgilere gore'; gozle): sutunun ilk sorusunun kutusuna katilir
# (kutu artik kapisi ilk satiri verdi). s162 R grafik -> 14.; s117 R grafik
# -> 5.; s118 L grafik -> 10.; s165 L tepkime -> 1., s165 R mekanizma -> 6.;
# s170 L deney tablosu -> 7.
KUTU_UST = {
    (117, "R", 0): 105,
    (118, "L", 0): 94,
    (162, "R", 0): 96,
    (165, "L", 0): 104,
    (165, "R", 0): 104,
    (170, "L", 0): 93,
}
# Kirpimi DISINDA kalan numarasiz GRAFIK / TABLO ortak oncule dayanan sorular
# (oncul yalniz grubun ilk sorusunun kutusunda): ithalde
# 'ortak_oncul_kirpimda_yok' bayragi, servis disi. s117 R grafik 5-9, s118 L
# grafik 10-14, s162 R grafik (basili 14-19), s170 L deney tablosu 7-10.
# METIN onculler (s165 L/R, s199-200) govdeye eklendi (_a21_gecici/b9_ortak_yama.py).
ORTAK_ONCUL_YOK: tuple[str, ...] = tuple(
    [f"AKT20AY-T020_{s:02d}" for s in (6, 7, 8, 9, 11, 12, 13, 14)]
    + [f"AKT20AY-T025_{s:02d}" for s in range(14, 19)]
    + [f"AKT20AY-T029_{s:02d}" for s in (8, 9, 10)]
)
# Kitapta 13. soru YOK (s161-162, Tepkimelerde Hiz Konu Testi 1): sorular ve
# serit 1-12, 14-19 (gozle). Sira 13-18, basili numara bayrakla korunur.
SERIT_NUMARA_BASKI_HATASI: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {
    162: (
        (9, 10, 11, 12, 14, 15, 16, 17, 18, 19),
        (9, 10, 11, 12, 13, 14, 15, 16, 17, 18),
    ),
}
numara_maskesi = ortak.kirmizi

ANAHTAR_NEREDEN = (
    "her test sayfasinin altindaki iki acik mavi kutu ('Soru 1/ B' ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)

# --- harita (icindekiler s6 + unite acilis sayfalari, dosya no; gozle) ---
KOK_KOD = "KIM"
KOD_ONEKI = "KIM-AKT20AY"
ALAN = "KIMYA"
SINAV = "AYT"
SINIF = 11
HARITA_NEREDEN = (
    "icindekiler (s6) 12 unite; unite baslangici acilis sayfasi (dosya = basili: "
    "7, 57, 87, 119, 141, 171, 209, 245, 295, 319, 375, 407; gozle); konu = test "
    "bandindaki unite / alt unite adi (iki bagimsiz okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "MODERN ATOM TEOR\u0130S\u0130 / PER\u0130YOD\u0130K S\u0130STEM"),
    (2, "GAZLAR"),
    (3, "SIVI \u00c7\u00d6ZELT\u0130LER VE \u00c7\u00d6Z\u00dcN\u00dcRL\u00dcK"),
    (4, "K\u0130MYASAL TEPK\u0130MELERDE ENERJ\u0130"),
    (5, "K\u0130MYASAL TEPK\u0130MELERDE HIZ"),
    (6, "K\u0130MYASAL TEPK\u0130MELERDE DENGE"),
    (7, "SULU \u00c7\u00d6ZELT\u0130LERDE DENGE"),
    (8, "K\u0130MYA VE ELEKTR\u0130K"),
    (9, "KARBON K\u0130MYASINA G\u0130R\u0130\u015e"),
    (10, "H\u0130DROKARBONLAR"),
    (11, "FONKS\u0130YONEL GRUPLAR"),
    (12, "ENERJ\u0130 KAYNAKLARI VE B\u0130L\u0130MSEL GEL\u0130\u015eMELER"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Modern Atom Teorisi", 7),
    (1, "Periyodik Sistem", 33),  # '1-B' acilis sayfasi (gozle)
    (2, "Gazlar", 57),
    (
        3,
        "S\u0131v\u0131 \u00c7\u00f6zeltiler ve \u00c7\u00f6z\u00fcn\u00fcrl\u00fck",
        87,
    ),
    (4, "Kimyasal Tepkimelerde Enerji", 119),
    (5, "Kimyasal Tepkimelerde H\u0131z", 141),
    (6, "Kimyasal Tepkimelerde Denge", 171),
    (7, "Sulu \u00c7\u00f6zeltilerde Denge", 209),
    (8, "Kimya ve Elektrik", 245),
    (9, "Karbon Kimyas\u0131na Giri\u015f", 295),
    (10, "Hidrokarbonlar", 319),
    (11, "Fonksiyonel Gruplar", 375),
    (12, "Enerji Kaynaklar\u0131 ve Bilimsel Geli\u015fmeler", 407),
)
SON_SAYFA = 416
# 10. unite (icindekiler 'Hidrokarbonlar') testlerinin bandi 'ORGANIK
# BILESIKLER' (iki okuma, s355-374); konu sayfa araligindan.
BANT_ESLER: dict[str, str] = {"ORGANIK BILESIKLER": "HIDROKARBONLAR"}

# --- kutu / kirpim (ak_kolon.py: kart kenari x 29 / 712; ayrac cift 376, tek 366) ---
SUTUNLAR = {0: {"L": (35, 374), "R": (384, 706)}, 1: {"L": (35, 364), "R": (372, 706)}}
SAYFA_ALTI = 906
BEKLENEN_SORU = 937
# s162 13-18. siradaki sorular 14-19 basili (yukarida; T025 = s161-162). Ayrica
# serit dogru, numara yanlis basilmis iki soru (gozle, metin kapisi): T047_03
# '4.' (4. soru da '4.'), T060_14 '13.' (13. soru da '13.').
BASKI_NUMARA_HATASI = {f"AKT20AY-T025_{s:02d}": s + 1 for s in range(13, 19)} | {
    "AKT20AY-T047_03": 4,
    "AKT20AY-T060_14": 13,
}


# --- metin ---
KITAP_BASLIGI = "2019-2020 Aktif AYT Kimya"
GRUP_SORU = 45
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi kirmizi basilidir; iki sayfalik testlerde numara surer (8-14). "
    "Kimyasal formullerde alt indis `_` ile, iyon yuku / ust simge `^` ile "
    "yazilir (DB'deki kimya kitaplariyla ayni sozlesme): `H_2O`, `Na_2CO_3`, "
    "`NH_4Cl`, `Na^+`, `SO_4^(2\u2212)`, `^(12)C`, `5 \u00b7 10^(\u221223)`; hal "
    "simgeleri basildigi gibi `(suda)`, `(g)`, `(k)`. Okun yonu `\u2192` / "
    "`\u21cc`. Orbital / elektron dizilimi `1s^2 2s^2 2p^6` bicimindedir.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("KIMYA",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme Ayt Kimya 2019 2020",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aktif Ogrenme Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "KIM_AKTIF_2020_AYT_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 5, "konu": 269, "test": 142},
    "harf": {"A": 101, "B": 164, "C": 223, "D": 210, "E": 239},
    "glif_hucre": 937,
    "glif_uyum": 936,
    "goz_teyit": {"T069#14": "E"},
    "glif_disi": [],
    "metin_parca": 18,
    "farkli_soru": 185,
    "okunamaz": 134,
    "ithal": 937,
    "beta": "788/937",
    "eski_modern": 170,
    "migration_no": 102,
    "onceki": "0101_akt20k0_beta_onay",
}
