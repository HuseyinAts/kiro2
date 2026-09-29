"""2023-2024 AROMAT AYT Fizik Soru Bankasi (Aromat 'Gercek OSYM Deneyimi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 320 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya (icindekiler s6: 'Vektorler' 8 = dosya 8). Yeni seri;
kesif: kitap_hat/kesif.py (_kesif_aro23af).

SAYFA DUZENI (olculdu; 29 Eyl 2026):
* 12 bolum; bolum acilis sayfasi (7, 43, 75, 109, 141, 167, 201, 231, 247,
  267, 289, 309) glifsiz, 'BOLUM NN' + konu listesi -> kapak. Arada test
  sayfalari; sayfa basina 2 sutun x 2 soru (sol sutun 1-2, sag 3-4).
* Ust bantta lacivert zeminde beyaz BUYUK HARFLE konu adi (icindekiler konu
  basligi) ve bordo 'TEST NN' rozeti (testin HER sayfasinda).
* Cevap anahtari HER sayfanin sag altinda: ince soluk kirmizi cerceveli beyaz
  kutuda gri '1-D 2-B 3-E 4-A' (tek satir), sagda bordo ok sekmesi (x ~662).
  Numara sayfalar boyunca surer (1-4, 5-8): test siniri iki gecisli
  (bas_listesi: seridi '1-' ile baslayan sayfa).
* Okuyucu simgesi numaranin solunda ayni satirda L 34 / R 360, numara siyah.
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.harita import norm as _norm
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

KOD = "ARO23AF"
KAYNAK_ADI = "2023-2024 AROMAT AYT Fizik Soru Bankasi"
CIKTI_ONEK = "aromat_2024_ayt_fizik"
KLASOR = "Aromat Ayt 2023 2024 Fizik Soru Bankas\u0131"
VERAF = "c7"
BEKLENEN_SAYFA = 320
BEKLENEN_TEST = 145
TEST_SAYFALARI = (
    (8, 42),
    (44, 74),
    (76, 108),
    (110, 140),
    (142, 166),
    (168, 200),
    (202, 230),
    (232, 246),
    (248, 266),
    (268, 288),
    (290, 308),
    (310, 320),
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
    98,
    100,
    102,
    104,
    106,
    110,
    112,
    114,
    116,
    118,
    120,
    122,
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
    232,
    234,
    236,
    238,
    240,
    242,
    244,
    248,
    250,
    252,
    254,
    256,
    258,
    260,
    262,
    264,
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
    290,
    292,
    294,
    296,
    298,
    300,
    302,
    304,
    306,
    310,
    312,
    314,
    316,
    318,
)


def sayfa_turu(a: np.ndarray, n: int) -> str:
    return "test" if n in _TEST else "kapak"


# --- cevap anahtari (sag alt kutu) ---
SERIT_Y = (900, 936)


def _sekme(z: np.ndarray) -> np.ndarray:
    r, g, b = (z[..., i].astype(int) for i in range(3))
    m: np.ndarray = (r > 140) & (g < 110) & (b < 120) & (r - g > 60)
    return m


def _cerceve(z: np.ndarray) -> np.ndarray:
    r, g, b = (z[..., i].astype(int) for i in range(3))
    m: np.ndarray = (r > 185) & (r - g > 30) & (r - b > 25) & (g > 120)
    return m


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Sag alt kutu: bordo ok sekmesi (>= 10 px genis, >= 12 satir) bulunur;
    kutunun sol kenari sekmenin solunda, sekme ortasi satirinda soluk kirmizi
    cerceve pikseli. Bolge cerceve ici (kenarlar haric)."""
    y0, y1 = SERIT_Y
    z = a[y0:y1]
    s = _sekme(z)
    kol = np.where(s.sum(axis=0) >= 12)[0]
    kol = kol[kol > 450]
    # sekme: en az 10 sutunluk bitisik kosu (kutunun koyu sol kenari tekil
    # sutun olarak maskeye girebilir).
    kosu = np.split(kol, np.where(np.diff(kol) > 2)[0] + 1) if len(kol) else []
    genis = [k for k in kosu if len(k) >= 10]
    if not genis:
        return None
    sx0 = int(genis[-1].min())
    c = _cerceve(z)
    # alt kenar: sekmenin solunda >= 20 px cerceve pikseli olan en alt satir
    # (ust kenar cok soluk, esigi gecmez: kutu yuksekligi sabit 18).
    alt = np.where(c[:, sx0 - 120 : sx0 - 3].sum(axis=1) >= 20)[0]
    if not len(alt):
        return None
    ya = int(alt.max())
    # sol kenar: alt kenar cizgisinin sekmeye uzanan kosusunun basi (arada
    # <= 3 px bosluga izin).
    xs = np.where(c[ya, :sx0])[0]
    x = int(xs.max())
    for v in xs[::-1]:
        if x - int(v) > 4:
            break
        x = int(v)
    return [y0 + ya - 17, y0 + ya, x + 2, sx0 - 1]


SERIT_HUCRE_TARIFI = (
    "Goruntu sayfanin sag altindaki cevap kutusudur: gri '1-D', '2-B' ... "
    "(numara, tire, harf), tek satir. Sagdaki bordo ok sekmesi hucre degildir."
)
ANAHTAR_NEREDEN = (
    "her test sayfasinin sag altindaki kutu ('1-D 2-B ...'; test iki sayfaysa "
    "iki kutu sayfa sirasiyla) + testin ilk sayfasinin ust bandi"
)
ANAHTAR_DISLA_X = None
GLIF_HARF_ESIK = 200
GLIF_HARF_H = (5, 10)
GLIF_HARF_W_EN_COK = 9
HUCRE_BOSLUK = 5


def harf_bloblari(s: np.ndarray) -> list[tuple[slice, slice]]:
    """Kucuk yazili '1-D' hucreleri (5-6 satir). Hucre = bos sutunla (>=
    HUCRE_BOSLUK) ayrilan kosu; harf = hucredeki SON sutun kosusu (en az bir bos
    sutunla ayrilan). Murekkep esigi 200 (notr gri): ARO23AF'de rakam acik gri /
    tire koyu, ARO23TF'de rakam koyu / tire acik (min 174) -- ikisinde de rakam,
    tire ve harf ayri kosulardir. (APO19MT 'ust ucte birde murekkep' kurali bu
    yazida B / E'yi tek sutuna indiriyordu; ilk tire kurali TF'de tireyi
    bulamiyordu.)"""
    mx, mn = s.max(axis=2).astype(int), s.min(axis=2).astype(int)
    koyu = (mn < GLIF_HARF_ESIK) & (mx - mn < 45)
    satir = koyu.any(axis=1)
    out: list[tuple[slice, slice]] = []
    y = 0
    while y < len(satir):
        if not satir[y]:
            y += 1
            continue
        y0 = y
        while y < len(satir) and satir[y]:
            y += 1
        if y - y0 < 4:
            continue
        kol = koyu[y0:y].any(axis=0)
        x = 0
        while x < len(kol):
            if not kol[x]:
                x += 1
                continue
            xa, bos = x, 0
            while x < len(kol) and bos < HUCRE_BOSLUK:
                bos = 0 if kol[x] else bos + 1
                x += 1
            xb = x - bos
            ha = xb - 1
            while ha > xa and kol[ha - 1]:
                ha -= 1
            if ha > xa:  # hucrede birden cok kosu: son kosu harf
                out.append((slice(y0, y), slice(ha, xb)))
    return out


BANT_Y_ALT = 112
BANT_TARIFI = (
    "Ust bantta lacivert zeminde beyaz BUYUK HARFLE konu adi; altinda bordo "
    "'TEST NN' rozeti."
)
BANT_KONU_TARIFI = "lacivert zemindeki BUYUK HARFLI konu adini"
BANT_TEST_NO_TARIFI = "bordo 'TEST NN' rozetindeki sayiyi"
BANT_KONU_KAPISI = True

# --- capa ---
SIMGE_X = {0: {"L": 34, "R": 360}, 1: {"L": 34, "R": 360}}
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
KOD_ONEKI = "FIZ-ARO23AF"
ALAN = "FIZIK"
SINAV = "AYT"
SINIF = 11
HARITA_NEREDEN = (
    "icindekiler (s6): 12 bolum, 22 konu basligi (dosya = basili); konu = test "
    "bandindaki BUYUK HARFLI konu adi (icindekiler adiyla kapidan gecer), sayfa "
    "araligi icindekiler sayfa numarasindan"
)
BOLUMLER: tuple[tuple[int, str], ...] = tuple(
    (i, f"B\u00d6L\u00dcM - {i}") for i in range(1, 13)
)
# (bolum, icindekiler adi, baslangic, sinif). Kitap AYT; sinif kitapta basili
# DEGIL: MEB 2018 fizik programi unite sinifi (11 / 12).
_KONULAR: tuple[tuple[int, str, int, int], ...] = (
    (1, "Vekt\u00f6rler", 8, 11),
    (1, "Ba\u011f\u0131l Hareket", 18, 11),
    (1, "Newton'\u0131n Hareket Yasalar\u0131", 28, 11),
    (2, "Bir Boyutta Sabit \u0130vmeli Hareket", 44, 11),
    (2, "Yery\u00fcz\u00fcnde Hareket", 54, 11),
    (3, "Enerji", 76, 11),
    (3, "\u0130tme ve \u00c7izgisel Momentum", 92, 11),
    (4, "Tork, Denge ve K\u00fctle Merkezi", 110, 11),
    (4, "Basit Makineler", 128, 11),
    (5, "Elektriksel Kuvvet, Alan, Potansiyel ve Enerji", 142, 11),
    (5, "D\u00fczg\u00fcn Elektrik Alan ve S\u0131\u011fa", 156, 11),
    (6, "Manyetizma", 168, 11),
    (6, "Elektromanyetik \u0130nd\u00fcklenme", 180, 11),
    (6, "Alternatif Ak\u0131m ve Transformat\u00f6rler", 190, 11),
    (7, "\u00c7embersel Hareket", 202, 12),
    (
        7,
        "D\u00f6nerek \u00d6teleme Hareketi, A\u00e7\u0131sal Momentum ve K\u00fctle \u00c7ekim Kuvveti",
        216,
        12,
    ),
    (8, "Basit Harmonik Hareket", 232, 12),
    (9, "Dalga Mekani\u011fi", 248, 12),
    (10, "Atom Kavram\u0131n\u0131n Tarihsel Geli\u015fimi", 268, 12),
    (10, "Atom Alt\u0131 Par\u00e7ac\u0131klar ve Radyoaktivite", 278, 12),
    (11, "Modern Fizik", 290, 12),
    (12, "Modern Fizi\u011fin Teknolojideki Uygulamalar\u0131", 310, 12),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s) for b, ad, s, _ in _KONULAR
)


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = ("AYT", sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 320
# Bolum 5-7 ve 10'da lacivert bant ust basligi tasir (alt baslik acik zeminde):
# bir bant birden cok konuyu kapsar; konu sayfa araligindan (serit okumasi A == B).
BANT_ESLER: dict[str, str | tuple[str, ...]] = {
    _norm(b): tuple(_norm(h) for h in hs)
    for b, hs in (
        (
            "ELEKTR\u0130K",
            (
                "Elektriksel Kuvvet, Alan, Potansiyel ve Enerji",
                "D\u00fczg\u00fcn Elektrik Alan ve S\u0131\u011fa",
            ),
        ),
        (
            "MANYET\u0130ZMA",
            (
                "Elektromanyetik \u0130nd\u00fcklenme",
                "Alternatif Ak\u0131m ve Transformat\u00f6rler",
            ),
        ),
        (
            "\u00c7EMBERSEL HAREKET",
            (
                "D\u00f6nerek \u00d6teleme Hareketi, A\u00e7\u0131sal Momentum ve K\u00fctle \u00c7ekim Kuvveti",
            ),
        ),
        (
            "ATOM F\u0130Z\u0130\u011e\u0130NE G\u0130R\u0130\u015e",
            (
                "Atom Kavram\u0131n\u0131n Tarihsel Geli\u015fimi",
                "Atom Alt\u0131 Par\u00e7ac\u0131klar ve Radyoaktivite",
            ),
        ),
    )
}

# --- kutu / kirpim ---
SUTUNLAR = {0: {"L": (32, 363), "R": (381, 709)}, 1: {"L": (32, 363), "R": (381, 709)}}
# Ust bant (lacivert serit + TEST rozeti) y 110da biter (s16 sutun olcumu); ilk
# numara y 131. Altlik: sayfa no dairesi y ~911, renkli cizgi y 917-921.
UST_BANT = 112
SAYFA_ALTI = 900
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1167

# --- metin ---
KITAP_BASLIGI = "2023-2024 AROMAT AYT Fizik Soru Bankas\u0131"
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
YONTEM_BELGESI = "FIZ_AROMAT_2024_AYT_YONTEM.md"

SONUC: dict = {}

SONUC = {
    "sayfa_turu": {"kapak": 18, "test": 302},
    "harf": {"A": 188, "B": 250, "C": 268, "D": 224, "E": 237},
    "glif_hucre": 1167,
    "glif_uyum": 1167,
    "goz_teyit": {},
    "glif_disi": [],
    "metin_parca": 19,
    "farkli_soru": 152,
    "okunamaz": 26,
    "ithal": 1167,
    "beta": "1141/1167",
    "eski_modern": 0,
    "migration_no": 125,
    "onceki": "0124_apo19km_beta_onay",
}
