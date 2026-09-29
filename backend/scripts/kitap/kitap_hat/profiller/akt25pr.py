"""AKTIF 2025 TYT Paragraf Soru Bankasi ('Pro AKTIF Paragraf', Aktif Ogrenme
duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 144 PNG (+ goruntu PDF'i, metin
katmani yok); kart (589,43)-(1331,1022). Basili sayfa = dosya - 5 (gozle:
dosya 10 = s5, 16 = s11). Icindekiler dosya 9: 5 unite + Deneme Testi.

SAYFA DUZENI: AKT25FZ ile ayni seri (iki kutulu serit, ust_bant, test =
turuncu >= 1500 VE pembe >= 600 VE iki kutulu serit). Olculdu
(_a21_gecici/ak_genel.py, c3_glif.py, c3_sutun.py; 29 Eyl 2026):
* 111 test sayfasi, 5 blok: 17-21, 24-27, 30-35, 39-45, 56-144 (56-61
  5. unite konu testleri, 62-144 Deneme Testi 1-17). Dosya 2-6 art arda
  benzer on sayfalar (kapak), test disi.
* Okuyucu simgesi (mor buyutec, 15x16) numaranin ~23 px ustu / 25 px solu:
  cift L 28 / R 355, tek L 46 / R 371. Numara kirmizi (h 10-11); altinda
  mor '?' (11x7, glif boyu disi).
* Orta ayrac turuncu cizgi cift x 361-363 / tek 378-380; ustunde dikey
  camgobegi 'aktif ogrenme yayinlari' yazisi ve buyutec -> sutunlar ayracin
  iki yanindan (R numara cift 379 / tek 396).
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.profiller.akt20ay import ust_bant  # noqa: F401
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
    TEST_SINIRI,
    UST_BANT,
    _renkler,
    serit_kutusu,
)
from scripts.kitap.kitap_hat.profiller.akt20k0 import SUS_BOLGELERI as _SUS_K0
from scripts.kitap.kitap_hat.profiller.akt24by import (  # noqa: F401
    ANAHTAR_DISLA_X,
    ANAHTAR_NEREDEN,
    SERIT_Y,
)

KOD = "AKT25PR"
KAYNAK_ADI = "AKTIF 2025 TYT Paragraf Soru Bankasi"
CIKTI_ONEK = "aktif_2025_tyt_paragraf"
KLASOR = "Aktif Ogrenme Tyt Paragraf Soru Bankas\u0131 2025"
VERAF = "c3"
BEKLENEN_SAYFA = 144
BEKLENEN_TEST = 30
TEST_SAYFALARI = (
    (17, 21),
    (24, 27),
    (30, 35),
    (39, 45),
    (56, 144),
)
BAS_SAYFALARI: tuple[int, ...] = (
    17,
    19,
    24,
    26,
    30,
    32,
    34,
    39,
    41,
    43,
    56,
    58,
    60,
    62,
    67,
    72,
    77,
    82,
    87,
    92,
    97,
    102,
    107,
    112,
    117,
    122,
    127,
    132,
    137,
    142,
)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    kutu: list[int] | None = serit_kutusu(a, SERIT_Y)
    return kutu


def sayfa_turu(a: np.ndarray, n: int) -> str:
    turuncu, pembe = _renkler(a)
    s = serit_kutusu(a, SERIT_Y)
    if turuncu >= 1500 and pembe >= 600 and s is not None and s[2] < 100:
        return "test"
    return "konu" if ortak.glifler(sys.modules[__name__], a) else "kapak"


# --- capa ---
SIMGE_X = {0: {"L": 28, "R": 355}, 1: {"L": 46, "R": 371}}
SIMGE_TOLERANS = 12
PENCERE = (-10, 42, 4, 64)
NUMARA_H = (6, 14)  # numara h 10-11 (c3_glif.py s60/61/100)
NUMARA_W_EN_COK = 22
NUMARA_DX = (14, 48)  # olculdu dx 25 (tek ve iki basamak)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Ortak oncul ('13 - 14. sorulari asagidaki parcaya gore cevaplayiniz.'
# cerceveli kutu + parca): okuyucu simgesi kutunun basinda, ilk sorunun
# numarasi parcanin ALTINDA (pencere disi -> tarama blob_yok 20). Serit
# hucresi capadan 20 fazla (bas_listesi gecis1) -> capa numaradan
# (_a21_gecici/c3_oncul.py: blob_yok glifin altindaki ilk capasiz numara).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    (34, "R", 445, 379),
    (66, "R", 442, 379),
    (76, "R", 529, 379),
    (86, "R", 463, 379),
    (90, "L", 451, 53),
    (95, "L", 436, 70),
    (96, "L", 522, 53),
    (100, "R", 478, 379),
    (101, "L", 443, 70),
    (106, "R", 430, 379),
    (110, "R", 340, 379),
    (110, "L", 341, 53),
    (116, "R", 433, 379),
    (121, "L", 412, 70),
    (123, "R", 462, 396),
    (123, "L", 455, 70),
    (125, "R", 419, 396),
    (131, "R", 348, 396),
    (134, "R", 457, 379),
    (136, "R", 544, 379),
)
# Ayni 20 ortak oncul sutun basinda: ilk sorunun kutusu oncul kutusunun
# pembe cerceve ust cizgisinin 3 px ustunden (c3_cerceve.py: cizgi y 101, s34 112) -> parca ilk sorunun kirpiminda; ikinci soruya
# metin olarak govde basina eklenir (yama).
KUTU_UST: dict[tuple[int, str, int], int] = {
    (34, "R", 0): 109,
    (66, "R", 0): 98,
    (76, "R", 0): 98,
    (86, "R", 0): 98,
    (90, "L", 0): 98,
    (95, "L", 0): 98,
    (96, "L", 0): 98,
    (100, "R", 0): 98,
    (101, "L", 0): 98,
    (106, "R", 0): 98,
    (110, "R", 0): 98,
    (110, "L", 0): 98,
    (116, "R", 0): 98,
    (121, "L", 0): 98,
    (123, "R", 0): 98,
    (123, "L", 0): 98,
    (125, "R", 0): 98,
    (131, "R", 0): 98,
    (134, "R", 0): 98,
    (136, "R", 0): 98,
}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    """Kirmizi basili numara (~220, 30, 40). Pembe sekme / bant (b >= 120),
    turuncu ve Deneme bandinin kahve bayragi (~190, 100, 80; c3_renk.py s83/96)
    disarida: g < 90 ve r - g > 80."""
    ai = a.astype(np.int16)
    r, g, b = ai[..., 0], ai[..., 1], ai[..., 2]
    m: np.ndarray = (r > 170) & (g < 90) & (b < 120) & (r - g > 80)
    return m


# --- harita (icindekiler dosya 9; dosya = basili + 5) ---
KOK_KOD = "TUR"
KOD_ONEKI = "TUR-AKT25PR"
ALAN = "TURKCE"
SINAV = "TYT"
SINIF = 12
HARITA_NEREDEN = (
    "icindekiler (dosya 9) 5 unite + Deneme Testi; unite baslangici acilis sayfasi "
    "(dosya = basili + 5: 10, 22, 28, 36, 46); Deneme Testi 1 dosya 62 (gozle; "
    "icindekilerdeki basili 79 yakalamayla tutmuyor); konu = test bandindaki unite "
    "adi (iki bagimsiz okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "PARAGRAFTA ANLATIM B\u0130\u00c7\u0130MLER\u0130"),
    (2, "PARAGRAFTA KONU"),
    (3, "PARAGRAFTA ANA D\u00dc\u015e\u00dcNCE"),
    (4, "PARAGRAFTA YARDIMCI D\u00dc\u015e\u00dcNCE"),
    (5, "PARAGRAFTA YAPI"),
    (6, "DENEME TEST\u0130"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Paragrafta Anlat\u0131m Bi\u00e7imleri", 10),
    (2, "Paragrafta Konu", 22),
    (3, "Paragrafta Ana D\u00fc\u015f\u00fcnce", 28),
    (4, "Paragrafta Yard\u0131mc\u0131 D\u00fc\u015f\u00fcnce", 36),
    (5, "Paragrafta Yap\u0131", 46),
    (6, "Deneme Testi", 62),
)
SON_SAYFA = 144
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim ---
# c3_sutun.py (s18-144): turuncu ayrac cift x 361-363 / tek 378-380 (ustunde
# dikey camgobegi yazi); L metni cift <= 358 / tek <= 375, R numara cift 379 /
# tek 396, R metin sonu cift 670 / tek 687. Sutunlar ayraci disarida birakir.
SUTUNLAR = {0: {"L": (20, 354), "R": (371, 712)}, 1: {"L": (38, 371), "R": (388, 712)}}
# Pembe 'KONU TESTI' sekmesinin koyu kivrimi (AKT25FZ ile ayni pencere).
SUS_BOLGELERI = (*_SUS_K0, (62, 114, 600, 712))
# Orta ayrac + dikey camgobegi yazi + ayractaki buyutec (c3_ayrac.py doygun x:
# cift 356-367, tek 373-384). Tek pencere cift sayfanin R numarasini (379)
# beyazlatirdi -> parite basina.
SUS_PARITE = {0: ((100, 906, 352, 371),), 1: ((100, 906, 369, 388),)}
SAYFA_ALTI = 906
BOSLUK = 5
BEKLENEN_SORU = 451

# --- metin ---
KITAP_BASLIGI = "AKT\u0130F 2025 TYT Paragraf Soru Bankas\u0131"
GRUP_SORU = 30
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi kirmizi basilidir; testler sayfalar boyunca surer. Paragraf "
    "metni TAM yazilir: numarali cumleler `(I)`, `(II)` ... basildigi yerde, "
    "alt\u0131 cizili ifade `<u>...</u>`, koyu ifade ayrica isaretlenmez. Iki "
    "konusmaci / madde basliklari (`Gazeteci:`) kendi satirinda.\n"
    "ORTAK PARCA: kirpim pembe cerceveli '13 - 14. sorulari asagidaki parcaya "
    "gore cevaplayiniz.' cumlesiyle basliyorsa bu soru ICIN parcadir: govde = "
    "cerceve cumlesi (ilk satir) + parcanin tamami + soru koku. Bu durumda "
    "komsu_not YAZMA. Baska bir sorunun parcasi / siklari kirpimin ust ya da "
    "altinda yarim kalmissa (cerceve yok) Komsu icerik kurali gecerli.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("TURKCE",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme Tyt Paragraf Soru Bankas\u0131 2025",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aktif Ogrenme Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "TUR_AKTIF_2025_PARAGRAF_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 9, "konu": 24, "test": 111},
    "harf": {"A": 64, "B": 87, "C": 127, "D": 109, "E": 64},
    "glif_hucre": 451,
    "glif_uyum": 451,
    "goz_teyit": {},
    "glif_disi": [],
    "metin_parca": 12,
    "farkli_soru": 43,
    "okunamaz": 0,
    "ithal": 451,
    "beta": "451/451",
    "eski_modern": 13,
    "migration_no": 113,
    "onceki": "0112_akt25fz_beta_onay",
}
