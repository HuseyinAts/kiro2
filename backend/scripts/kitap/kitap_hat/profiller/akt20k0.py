"""2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya (Aktif Ogrenme duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 368 PNG; kart (589,43)-(1331,1022).
Icindekiler s6: 9 unite (Kimya Bilimi .. Kimya Her Yerde).

SAYFA DUZENI (kontak sayfasi + olcum, 28 Eyl 2026; _a21_gecici/ak_*.py)
----------------------------------------------------------------------
* Unite acilis sayfasi (mavi bant + turuncu 'N.' etiketi), konu anlatimi
  sayfalari ('KAVRAMA BOLUMU' / 'UYGULAMA BOLUMU' camgobegi sekmeleri):
  cozumlu 'Ornek N' (kapsam DISI) ve 'Soru : Na' alistirmalari -- numara
  '6a' bicimi anahtar 1..N kapisina uymaz, kapsam DISI.
* Test sayfalari: ust bantta turuncu unite adi + camgobegi serit + pembe
  'KONU TESTI (N)' sekmesi. Konu Testi N cogu zaman iki sayfa; soru numarasi
  sayfalar boyunca surer (1-7, 8-12). 122 test sayfasi, 13 blok (olculdu:
  turuncu >= 1500 px ve pembe >= 300 px).
* HER sayfanin altinda iki acik mavi kutu (x 20-325 / 415-715, y 907-963),
  aralarinda sayfa numarasi dairesi; kutularda 'Soru 1/ B' (numara acik
  mavi, harf siyah kalin, y 909-916).
* Soru numarasi PEMBE (220,0,130); okuyucu simgesi x 60-63 (L) / 352-363
  (R), iki paritede ayni.
* Test siniri iki gecisli (acl25pl deseni): seridi 'Soru 1/' ile baslayan
  sayfalar.
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak

KOD = "AKT20K0"
KAYNAK_ADI = "2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya"
CIKTI_ONEK = "aktif_2020_0dan_kimya"
KLASOR = "Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020"
VERAF = "b8"
KART = (589, 43, 1331, 1022)
BEKLENEN_SAYFA = 368
BEKLENEN_TEST = 61
TEST_SAYFALARI = (
    (25, 36),
    (64, 77),
    (103, 112),
    (149, 164),
    (185, 196),
    (206, 209),
    (222, 227),
    (239, 246),
    (255, 258),
    (271, 278),
    (299, 308),
    (333, 344),
    (363, 368),
)
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
BAS_SAYFALARI: tuple[int, ...] = (
    25,
    27,
    29,
    31,
    33,
    35,
    64,
    66,
    68,
    70,
    72,
    74,
    76,
    103,
    105,
    107,
    109,
    111,
    149,
    151,
    153,
    155,
    157,
    159,
    161,
    163,
    185,
    187,
    189,
    191,
    193,
    195,
    206,
    208,
    222,
    224,
    226,
    239,
    241,
    243,
    245,
    255,
    257,
    271,
    273,
    275,
    277,
    299,
    301,
    303,
    305,
    307,
    333,
    335,
    337,
    339,
    341,
    343,
    363,
    365,
    367,
)


# --- sayfa turu ---
def _renkler(a: np.ndarray) -> tuple[int, int]:
    t = a[55:115, 520:720]
    r, g, b = t[..., 0], t[..., 1], t[..., 2]
    pembe = int(((r > 200) & (g > 30) & (g < 100) & (b > 100) & (b < 170)).sum())
    o = a[50:125, 40:360]
    turuncu = int(
        (
            (o[..., 0] > 225) & (o[..., 1] > 120) & (o[..., 1] < 185) & (o[..., 2] < 90)
        ).sum()
    )
    return turuncu, pembe


def sayfa_turu(a: np.ndarray, n: int) -> str:
    turuncu, pembe = _renkler(a)
    if turuncu >= 1500 and pembe >= 300:
        return "test"
    return "konu" if ortak.glifler(sys.modules[__name__], a) else "kapak"


def _acik_mavi(z: np.ndarray) -> np.ndarray:
    m: np.ndarray = (
        (z[..., 2] > 235) & (z[..., 0] > 200) & (z[..., 0] < 235) & (z[..., 1] > 225)
    )
    return m


SERIT_Y = (860, 979)
SERIT_YUKSEKLIK = 20


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Sayfa alti iki acik mavi kutu: ust kenar = acik mavi pikseli > 200 olan
    ilk satir (122 test sayfasinda 907), x = kutularin kapsami (20-715).
    Bolge kutu ustunden SERIT_YUKSEKLIK px (metin y 909-921); aradaki sayfa
    numarasi ANAHTAR_DISLA_X ile glif kanalindan disarida."""
    return serit_kutusu(a, SERIT_Y)


def serit_kutusu(a: np.ndarray, serit_y: tuple[int, int]) -> list[int] | None:
    """anahtar_bolgesi govdesi; serit_y arama penceresi (seri kitaplari ortak)."""
    z = a[serit_y[0] : serit_y[1]]
    lb = _acik_mavi(z)
    satir = np.where(lb.sum(axis=1) > 200)[0]
    if len(satir) < 20:  # kutu ~56 satir; tekil acik mavi satir serit degil
        return None
    xs = np.where(lb[satir[0] : satir[0] + 40].sum(axis=0) > 10)[0]
    if not len(xs):
        return None
    y0 = int(satir[0]) + serit_y[0] - 1
    x0, x1 = int(xs.min()), int(xs.max())
    # Iki satirli serit (cok sorulu sayfa; 2. satir y ~925-932): alt sinir
    # kutudaki son koyu satir + 3 (tek satirda metin 909-921 -> y0 + 20).
    koyu = np.where((a[y0 : y0 + 56, x0:x1].max(axis=2) < 120).sum(axis=1) > 0)[0]
    y1 = y0 + max(SERIT_YUKSEKLIK, int(koyu.max()) + 3 if len(koyu) else 0)
    return [y0, y1, x0, x1]


ANAHTAR_DISLA_X = (330, 412)  # sayfa numarasi dairesi (kutular arasi 326-416)


def ust_bant(a: np.ndarray) -> int:
    """Test sayfasi ust bandinin alti: doygun (max-min > 60) pikseli > 150 olan
    son satir + 2 (ilk sayfa 99, devam sayfasi 85; olculdu)."""
    z = a[20:140, 20:720]
    doy = (z.max(axis=2) - z.min(axis=2)) > 60
    ys = np.where(doy.sum(axis=1) > 150)[0]
    return int(ys.max()) + 20 + 2 if len(ys) else UST_BANT


# Pembe sekmenin koyu kivrimi bandin 9 satir altina iner (s65: bant 82, kivrim
# 83-91 x 631-655; s241: bant 99, kivrim 100-108 x 657-676) ve hemen altinda
# metin baslayabilir (s241 R ust indis y 109); sutun sonlarinda mavi ucgen
# isaretler (s241 x 101-103 / 388-390, y ~890-900). Kirpimda bu pencerelerin
# DOYGUN pikselleri beyazlatilir (siyah metin doygun degil).
SUS_BOLGELERI = ((80, 115, 620, 700), (880, 906, 90, 115), (880, 906, 375, 400))


# --- capa (ak_capa.py: 122 test sayfasi, 868 glif) ---
GLIF_GENISLET = True
GLIF_BOY = (12, 17, 12, 17)
SIMGE_X = {1: {"L": 61, "R": 355}, 0: {"L": 61, "R": 355}}
SIMGE_TOLERANS = 12
PENCERE = (-10, 42, 4, 64)
NUMARA_H = (8, 15)
NUMARA_W_EN_COK = 22
NUMARA_DX = (25, 44)
SERIT_SIMGE_PAY = 10
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Okuyucu simgesi KONMAMIS sorular (gozle; capa pembe numaradan, ak_numara.py):
# s108 sag sutun '13.'; s196 sag sutun '8.' (numara y 358): okuyucu simgesi
# ustteki ORTAK TABLONUN basinda (8-11 bu tabloya gore) -> capa tablo basindan
# (y 99), 8. sorunun kutusu tabloyu da kapsar (yoksa artik murekkep kapisi).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    (108, "R", 645, 389),
    (196, "R", 99, 388),
)
# Kitapta YANLIS basilmis soru numaralari (gozle, s341-342, Asitler Konu
# Testi 5): s341 1-6, s342 sorulari ve seridi '6, 7, 8, 10, 11, 12' (6 iki
# kez, 9 yok). Serit okumasi basili numarayi yazar; test ici SIRA konumdan
# (7-12) alinir, basili numara bayrakla korunur.
SERIT_NUMARA_BASKI_HATASI: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {
    342: ((6, 7, 8, 10, 11, 12), (7, 8, 9, 10, 11, 12)),
}
# Ayni hata soru duzeyinde (T057 = s341-342): sira -> basili numara. Ayrica
# serit dogru, soru numarasi yanlis basilmis iki soru (gozle, metin kapisi):
# s222 sol sutun 4. soru '5.' (T035_04), s340 sag sutun 10. soru '5.' (T056_10).
BASKI_NUMARA_HATASI = {
    "AKT20K0-T035_04": 5,
    "AKT20K0-T056_10": 5,
    "AKT20K0-T057_07": 6,
    "AKT20K0-T057_08": 7,
    "AKT20K0-T057_09": 8,
}


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    """Pembe basili soru numarasi (220,0,130); okuyucu glifi mor (b > r)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (r > 170) & (g < 90) & (b > 80) & (b < 190) & (r - g > 120)
    return m


# --- cevap anahtari ---
ANAHTAR_NEREDEN = (
    "her test sayfasinin altindaki iki acik mavi kutu ('Soru 1/ B' ...; test iki "
    "sayfaysa iki serit sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)
BANT_Y_ALT = 112
BANT_TARIFI = (
    "Turuncu bantta UNITE ADI (ornek 'K\u0130MYA B\u0130L\u0130M\u0130'), sagda "
    "pembe sekmede 'KONU TEST\u0130' ve daire icinde test numarasi."
)
BANT_KONU_TARIFI = "turuncu banttaki UNITE ADINI"
BANT_TEST_NO_TARIFI = "pembe 'KONU TEST\u0130' sekmesindeki DAIRE ICINDEKI sayiyi"
SERIT_HUCRE_TARIFI = (
    "Seritte iki acik mavi kutu vardir; hucreler 'Soru 1/ B' bicimindedir "
    "(numara acik mavi, harf siyah kalin). Sol kutuyu sonra sag kutuyu oku. "
    "Iki kutunun ARASINDAKI dairedeki sayi SAYFA NUMARASIDIR, hucre DEGILDIR."
)
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (6, 8)
GLIF_HARF_W_EN_COK = 8

# --- harita (icindekiler s6 + unite acilis sayfalari, dosya no; gozle) ---
KOK_KOD = "KIM"
KOD_ONEKI = "KIM-AKT20K0"
ALAN = "KIMYA"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s6) 9 unite; unite baslangici acilis sayfasinin dosya no'su "
    "(gozle: 7, 37, 113, 165, 197, 211, 279, 309, 345); konu = unite (test bandi "
    "unite adini tasir; iki bagimsiz okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "K\u0130MYA B\u0130L\u0130M\u0130"),
    (2, "ATOM VE PER\u0130YOD\u0130K S\u0130STEM"),
    (3, "T\u00dcRLER ARASI ETK\u0130LE\u015e\u0130MLER"),
    (4, "MADDEN\u0130N HALLER\u0130"),
    (5, "DO\u011eA VE K\u0130MYA"),
    (6, "K\u0130MYANIN TEMEL KANUNLARI VE K\u0130MYASAL HESAPLAMALAR"),
    (7, "KARI\u015eIMLAR"),
    (8, "AS\u0130TLER, BAZLAR VE TUZLAR"),
    (9, "K\u0130MYA HER YERDE"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Kimya Bilimi", 7),
    (2, "Atom ve Periyodik Sistem", 37),
    (3, "T\u00fcrler Aras\u0131 Etkile\u015fimler", 113),
    (4, "Maddenin Halleri", 165),
    (5, "Do\u011fa ve Kimya", 197),
    (6, "Kimyan\u0131n Temel Kanunlar\u0131 ve Kimyasal Hesaplamalar", 211),
    (7, "Kar\u0131\u015f\u0131mlar", 279),
    (8, "Asitler, Bazlar ve Tuzlar", 309),
    (9, "Kimya Her Yerde", 345),
)
SON_SAYFA = 368
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (kesif: test sayfalari x murekkep; orta ayrac x 371) ---
# Kart kenar golgesi x 22 / 719 ve orta ayrac x 371 her satirda koyu (s25
# kolon olcumu): sutunlar bunlarin icinde.
# Sol sutun metni ayraca kadar uzayabilir (s341 T057_2 '(suda)' x 367).
SUTUNLAR = {0: {"L": (28, 370), "R": (381, 712)}, 1: {"L": (28, 370), "R": (381, 712)}}
UST_BANT = 86
SAYFA_ALTI = 902
SERIT_PAY = 4
BEKLENEN_SORU = 868
DISK_MERKEZ = (10, 8)
BEYAZ_YARICAP = 17
HALKA = (19, 23)
LEKE = None

# --- metin ---
KITAP_BASLIGI = "2019-2020 Aktif 0'dan Ba\u015flayanlara Aktif Kimya"
GRUP_SORU = 45
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Bu kitapta soru numarasi KIRMIZI DEGIL, PEMBE basilidir ('1.', '2.' ...); "
    "`basili_no` icin sorunun solundaki pembe numarayi oku. Numara iki sayfalik "
    "testlerde 8-12 diye surebilir; gordugun numarayi yaz. Kimyasal formullerde "
    "alt indis `_` ile, iyon yuku / ust simge `^` ile yazilir (DB'deki kimya "
    "kitaplariyla ayni sozlesme): `H_2O`, `Na_2CO_3`, `NH_4Cl`, `Na^+`, "
    "`SO_4^(2\u2212)`, `^(12)C`, `5 \u00b7 10^(\u221223)`; hal simgeleri "
    "basildigi gibi `(suda)`, `(g)`, `(k)`. Okun yonu `\u2192` / `\u21cc`.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("KIMYA",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Aktif Ogrenme Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "KIM_AKTIF_2020_0DAN_YONTEM.md"
# s196 sag sutun ortak tabloya dayanan 9-11 (tablo yalniz 8. sorunun
# kirpiminda): 'ortak_oncul_kirpimda_yok', servis disi (0105).
ORTAK_ONCUL_YOK: tuple[str, ...] = (
    "AKT20K0-T032_09",
    "AKT20K0-T032_10",
    "AKT20K0-T032_11",
)

SONUC = {
    "sayfa_turu": {"kapak": 6, "konu": 240, "test": 122},
    "harf": {"A": 92, "B": 171, "C": 206, "D": 196, "E": 203},
    "glif_hucre": 856,
    "glif_uyum": 856,
    "goz_teyit": {},
    "glif_disi": [5],
    "metin_parca": 17,
    "farkli_soru": 115,
    "okunamaz": 115,
    "ithal": 868,
    "beta": "753/868",
    "eski_modern": 187,
    "migration_no": 99,
    "onceki": "0098_acl24am_beta_onay",
    # AKT20AY'de bulunan hata sinifi (ortak tabloya dayanan sorular): s196
    # T032_09..11 0105 ile servis disi (ORTAK_ONCUL_YOK), aktif 750/868.
    "ortak_oncul_duzeltme": {
        "migration_no": 105,
        "servis_disi": 3,
        "beta_sonrasi": "750/868",
    },
}
