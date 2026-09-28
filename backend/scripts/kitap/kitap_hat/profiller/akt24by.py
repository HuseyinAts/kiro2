"""2023-2024 Aktif Ogrenme Biyoloji (Aktif Ogrenme duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 272 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya - 1 (s8 = basili 7, unite 1 acilisi; gozle).
Icindekiler s7: 6 unite (Yasam Bilimi Biyoloji .. Ekoloji).

YAKALAMA KUSURU (olculdu, _a21_gecici/c1_ayni.py; gozle): dosya 218-250
dosya 217'nin (basili 216), 254-272 dosya 253'un (basili 219) birebir
kopyasi (kart farki < %0,05). Yani yakalama basili 1-219'u kapsar; basili
220-266 (5. unitenin sonu, 6. unite Ekoloji) YOK. Kopya dosyalar sayfa turu
'kapak' (disarida); yeniden yakalama olmadan eksik sayfalar islenemez.

SAYFA DUZENI: AKT20K0 / AKT20AY ile ayni seri (Aktif Ogrenme); farklar
(olculdu, _a21_gecici/c1_olc.py, c1_sinif.py; 28 Eyl 2026):
* 'ETKINLIKLER & HATIRLATMALAR' / 'ESLENECEKLER' sayfalari test bandinin
  renklerini tasir (turuncu + pembe) ama cevap seridi yok -> test = renk VE
  iki kutulu serit (x0 < 100). Konu sayfalarinin 'Soru N' seridi yalniz sag
  kutu (x0 ~411) -> konu.
* 83 test sayfasi, 6 blok: 44-63, 88-105, 134-151, 174-189, 210-217, 251-253.
* Okuyucu simgesi cift sayfa L 51 / R 350, tek sayfa L 62 / R 361.
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

KOD = "AKT24BY"
KAYNAK_ADI = "2023-2024 Aktif Ogrenme Biyoloji"
CIKTI_ONEK = "aktif_2024_biyoloji"
KLASOR = "Aktif Ogrenme 2023 2024 Biyoloji"
VERAF = "c1"
BEKLENEN_SAYFA = 272
BEKLENEN_TEST = 42
TEST_SAYFALARI = (
    (44, 63),
    (88, 105),
    (134, 151),
    (174, 189),
    (210, 217),
    (251, 253),
)
BAS_SAYFALARI: tuple[int, ...] = (
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
    88,
    90,
    92,
    94,
    96,
    98,
    100,
    102,
    104,
    134,
    136,
    138,
    140,
    142,
    144,
    146,
    148,
    150,
    174,
    176,
    178,
    180,
    182,
    184,
    186,
    188,
    210,
    212,
    214,
    216,
    251,
    253,
)

# Yakalama kusuru: art arda ayni dosyalar (ilk ornek 217 / 253 islenir).
KOPYA_SAYFALAR = frozenset(range(218, 251)) | frozenset(range(254, 273))

SERIT_Y = (900, 979)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """AKT20K0 iki kutulu serit olcumu; arama y 900'den."""
    if n in KOPYA_SAYFALAR:
        return None
    kutu: list[int] | None = serit_kutusu(a, SERIT_Y)
    return kutu


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in KOPYA_SAYFALAR:
        return "kapak"
    turuncu, pembe = _renkler(a)
    s = serit_kutusu(a, SERIT_Y)
    if turuncu >= 2500 and pembe >= 700 and s is not None and s[2] < 100:
        return "test"
    return "konu" if ortak.glifler(sys.modules[__name__], a) else "kapak"


ANAHTAR_DISLA_X = (335, 405)

# --- capa ---
# s251-253 (basili 217-219) kopya bosluktan sonra dosya paritesi basili
# sayfanin tersi (s252 cift dosya, simge L 68 = tek duzen): PARITE_TERS.
PARITE_TERS = frozenset({251, 252, 253})
SIMGE_X = {0: {"L": 51, "R": 350}, 1: {"L": 62, "R": 361}}
SIMGE_TOLERANS = 14  # s53 '11.' simgesi x 49 (tek sayfa L 62'den 13 px sola)
PENCERE = (-10, 42, 4, 64)
NUMARA_H = (8, 15)
NUMARA_W_EN_COK = 22
NUMARA_DX = (22, 48)  # s63 iki basamakli numara dx 46
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Okuyucu simgesi KONMAMIS soru (gozle; capa kirmizi numaradan): s179 sol
# '8.' -- simge ustteki ortak oncul yonergesinin ('8, 9 ve 10. sorulari
# asagidaki sekle gore') basinda.
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ((179, "L", 237, 98),)
# Sutun basinda numarasiz ORTAK oncul (gozle; okuyucu simgesi yonergede,
# numara yok -> tarama 'blob_yok'): sutunun ilk sorusunun kutusuna katilir.
# s53 R '12, 13 ve 14. sorulari asagida verilen bilgilere gore' (metin +
# madde listesi); s175 L '9 ve 10. sorulari asagidaki grafige gore' (grafik);
# s179 L '8, 9 ve 10. sorulari asagidaki sekle gore' (sekil).
# Simgesi de olmayan uc oncul (kutu artik kapisi): s91 L zar molekulleri
# sekli (10-12), s188 R hucre sekli (4-5), s213 L kromozom / gen sekli (8-10).
KUTU_UST = {
    (53, "R", 0): 89,
    (91, "L", 0): 92,
    (175, "L", 0): 93,
    (179, "L", 0): 93,
    (188, "R", 0): 104,
    (213, "L", 0): 93,
    # Sutun ORTASINDA oncul (metin okumasi komsu_not ile buldu): s176 L '2 ve
    # 3. sorulari asagidaki gorsele gore' + eseysiz ureme gorseli, 1. sorunun
    # siklarinin altinda (y 265) -> 2. sorunun kutusuna.
    (176, "L", 1): 258,
}
# Kirpimi DISINDA kalan SEKIL / GRAFIK ortak oncule dayanan sorular (oncul
# yalniz grubun ilk sorusunun kutusunda): 'ortak_oncul_kirpimda_yok', beta
# disi. METIN oncul (s53 R, T005_13-14) govdeye eklenir (c1_ortak_yama.py).
ORTAK_ONCUL_YOK: tuple[str, ...] = (
    "AKT24BY-T012_11",
    "AKT24BY-T012_12",
    "AKT24BY-T029_10",
    "AKT24BY-T030_03",
    "AKT24BY-T031_09",
    "AKT24BY-T031_10",
    "AKT24BY-T036_05",
    "AKT24BY-T038_09",
    "AKT24BY-T038_10",
)
numara_maskesi = ortak.kirmizi

ANAHTAR_NEREDEN = (
    "her test sayfasinin altindaki iki acik mavi kutu ('Soru 1/ B' ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)

# --- harita (icindekiler s7 + unite acilis sayfalari, dosya no; gozle) ---
KOK_KOD = "BIO"
KOD_ONEKI = "BIO-AKT24BY"
ALAN = "BIYOLOJI"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s7) 6 unite; unite baslangici acilis sayfasi (dosya = basili + 1: "
    "8, 64, 106, 152, 190; 6. unite Ekoloji yakalamada yok); konu = test bandindaki "
    "unite adi (iki bagimsiz okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "YA\u015eAM B\u0130L\u0130M\u0130 B\u0130YOLOJ\u0130"),
    (2, "H\u00dcCRE"),
    (3, "CANLILAR D\u00dcNYASI"),
    (4, "H\u00dcCRE B\u00d6L\u00dcNMELER\u0130"),
    (5, "KALITIMIN GENEL \u0130LKELER\u0130"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Ya\u015fam Bilimi Biyoloji", 8),
    (2, "H\u00fccre", 64),
    (3, "Canl\u0131lar D\u00fcnyas\u0131", 106),
    (4, "H\u00fccre B\u00f6l\u00fcnmeleri", 152),
    (5, "Kal\u0131t\u0131m\u0131n Genel \u0130lkeleri", 190),
)
SON_SAYFA = 272
# Test 35 (s186, Hucre Bolunmeleri Konu Testi 7) bandi baskida 'HUCE
# BOLUNMELERI' (R eksik; iki okuma ayni, gozle).
BANT_ESLER: dict[str, str] = {"HUCE BOLUNMELERI": "HUCRE BOLUNMELERI"}

# --- kutu / kirpim ---
# Olculdu (gozle 2x + piksel, s44/45/52/53/90/91/176/177/252/253): turuncu
# orta ayrac cift x 366 / tek 376 (min kanali koyu); L metni simgenin altina kadar
# (cift <= 362, tek <= 357); R numara cift 382 / tek 393; kart kenari 29 / 712.
# Dikey camgobegi 'aktif ogrenme yayinlari' yazisi y 452-545, cift x 362-372 /
# tek 372-383. Turuncu ayrac (min kanal < KOYU) ve yazi doygun: x 360-381
# penceresi SUS_BOLGELERI ile beyazlatilir (cift R numara 382'den).
SUTUNLAR = {0: {"L": (30, 361), "R": (374, 712)}, 1: {"L": (30, 370), "R": (384, 712)}}
SUS_BOLGELERI = (*_SUS_K0, (95, 905, 360, 382))
SAYFA_ALTI = 906
BEKLENEN_SORU = 528
# Serit dogru (ardisik 1..N), soru numarasi yanlis basilmis (gozle, metin
# kapisi): s59-60 Konu Testi 9'da '6.' yok, sorular 1-5, 7-13 (serit 1-12);
# s91 R ust '12.' (13. yerine; 12 iki kez); s182 R ust '3.' (4. yerine).
# Sira konumdan, basili numara bayrakla korunur.
BASKI_NUMARA_HATASI = {f"AKT24BY-T009_{s:02d}": s + 1 for s in range(6, 13)} | {
    "AKT24BY-T012_13": 12,
    "AKT24BY-T033_04": 3,
}

# --- metin ---
KITAP_BASLIGI = "2023-2024 Aktif \u00d6\u011frenme Biyoloji"
GRUP_SORU = 45
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi turuncu-kirmizi basilidir; iki sayfalik testlerde numara "
    "surer. Soy agaci, punnet karesi, tablo gibi sekiller govdede yalniz "
    "metin olarak (tablo hucreleri `|` ile) yazilir; sekil icindeki etiketleri "
    "uydurma. Genotip / alel yazimi basildigi gibi: `AaBb`, `X^R X^r`, `I^A i`.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("BIYOLOJI",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme 2023 2024 Biyoloji",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aktif Ogrenme Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "BIO_AKTIF_2024_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 57, "konu": 132, "test": 83},
    "harf": {"A": 91, "B": 89, "C": 93, "D": 121, "E": 134},
    "glif_hucre": 528,
    "glif_uyum": 527,
    "goz_teyit": {"T002#17": "E"},
    "glif_disi": [],
    "metin_parca": 11,
    "farkli_soru": 68,
    "okunamaz": 39,
    "ithal": 528,
    "beta": "480/528",
    "eski_modern": 0,
    "migration_no": 107,
    "onceki": "0106_acl25s2_ortak_oncul",
}
