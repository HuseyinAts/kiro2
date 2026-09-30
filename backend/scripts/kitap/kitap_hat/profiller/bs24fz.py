"""2024 BILGI SARMAL TYT Fizik Soru Bankasi -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 336 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya. Yeni yayinevi (Bilgi Sarmal); kesif: _kesif_bs24fz.

SAYFA DUZENI (olculdu; 30 Eyl 2026):
* Ust bantta solda bordo daire icinde 'Test N', ortada gri kutuda konu adi
  ('FIZIK BILIMINE GIRIS - 1').
* Iki sutun, sutun basina 3 soru; her sorunun solunda mor buyutec simgesi
  (12x12) ve altinda acik mor '?' dairesi (simge degil, farkli renk).
* Cevap seridi HER test sayfasinin SOL ALTINDA duz metin: acik gri
  '1. C  2. C  3. C ...' (y 910-915, x 79'dan baslar).
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat.profiller.akt20k0 import (  # noqa: F401
    BEYAZ_YARICAP,
    DISK_MERKEZ,
    GLIF_GENISLET,
    HALKA,
    KART,
    LEKE,
    SERIT_PAY,
    SERIT_SIMGE_PAY,
)

KOD = "BS24FZ"
KAYNAK_ADI = "BILGI SARMAL 2024 TYT Fizik Soru Bankasi"
CIKTI_ONEK = "bilgi_sarmal_2024_tyt_fizik"
KLASOR = "Bilgi Sarmal\u0131 Tyt 2024 Fizik Soru Bankas\u0131"
VERAF = "c12"
BEKLENEN_SAYFA = 336
BEKLENEN_TEST = 161
TEST_SAYFALARI = ((7, 92), (95, 144), (147, 214), (217, 288), (291, 336))
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))
ANAHTAR_KAPSAMI = "sayfa"
TEST_SINIRI = "bas_listesi"
BAS_SAYFALARI: tuple[int, ...] = (
    7,
    9,
    11,
    13,
    15,
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
    41,
    43,
    45,
    47,
    49,
    51,
    53,
    55,
    57,
    59,
    61,
    63,
    65,
    67,
    69,
    71,
    73,
    75,
    77,
    79,
    81,
    83,
    85,
    87,
    89,
    91,
    95,
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
    119,
    121,
    123,
    125,
    127,
    129,
    131,
    133,
    135,
    137,
    139,
    141,
    143,
    147,
    149,
    151,
    153,
    155,
    157,
    159,
    161,
    163,
    165,
    167,
    169,
    171,
    173,
    175,
    177,
    179,
    181,
    183,
    185,
    187,
    189,
    191,
    193,
    195,
    197,
    199,
    201,
    203,
    205,
    207,
    209,
    211,
    213,
    217,
    219,
    221,
    223,
    225,
    227,
    229,
    231,
    233,
    235,
    237,
    239,
    241,
    243,
    245,
    247,
    249,
    251,
    253,
    255,
    257,
    259,
    261,
    263,
    265,
    267,
    269,
    271,
    273,
    275,
    277,
    279,
    281,
    283,
    285,
    287,
    291,
    293,
    295,
    297,
    299,
    301,
    303,
    305,
    307,
    309,
    311,
    313,
    315,
    317,
    319,
    321,
    323,
    325,
    327,
    329,
    331,
    333,
    335,
)

SERIT_Y = (900, 925)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Duz metin serit, sayfa numarasi dairesinin (x ~355-375) disinda:
    TEK sayfada solda (x 40-350), CIFT sayfada sagda (x 400-720).
    Acik gri, notr (max-min < 40), toplam < 560."""
    x0, x1 = (400, 720) if n % 2 == 0 else (40, 350)
    b = a[SERIT_Y[0] : SERIT_Y[1], x0:x1]
    k = (b.max(axis=2) - b.min(axis=2) < 40) & (b.sum(axis=2) < 560)
    if int(k.sum()) < 40:
        return None
    ys, xs = np.where(k)
    if int(ys.max()) - int(ys.min()) > 14:
        return None
    return [
        int(ys.min()) + SERIT_Y[0] - 2,
        int(ys.max()) + SERIT_Y[0] + 2,
        int(xs.min()) + x0,
        int(xs.max()) + x0,
    ]


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in _TEST and anahtar_bolgesi(a, n) is not None:
        return "test"
    koyu = a[60:900].max(axis=2) < 120
    return "konu" if int(koyu.sum()) > 2000 else "kapak"


GLIF_BOY = (10, 16, 10, 16)
SIMGE_X = {0: {"L": 48, "R": 367}, 1: {"L": 44, "R": 362}}
SIMGE_TOLERANS = 14
PENCERE = (-8, 155, 8, 130)
NUMARA_H = (5, 14)
NUMARA_W_EN_COK = 30
NUMARA_DX = (10, 120)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ()
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
KENAR_GOZ_ONAY: tuple[str, ...] = ()
ORTAK_ONCUL_YOK: tuple[str, ...] = ()
YAKALANMAYAN_SORU: dict[int, tuple[int, ...]] = {}


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = a.max(axis=2) < 140
    return m


# NUMARA-ONCE CAPA MODU
# --------------------
# Bu kitapta buyutec simgesi AYIRT EDICI DEGIL: normal soru, kaynak rozetli
# soru ('2023 / MSU' mavi hap) ve 'AKILLI NOT' bilgi kutusu ayni simgeyi ve
# ayni '?' dairesini tasir. Renk, mavi alan, kirmizi baslik ve '?' diski
# denendi; hicbiri ayirmiyor (olcum: _a21_gecici/bs_rozet*.py).
# Capa bu yuzden BASILI NUMARADIR; simge yalniz dogrulamadir (tarama.py
# _capalar_numara). Numarasiz tek durum rozetli sorudur: rozet capa olur.
CAPA_MODU = "numara"
SIMGE_PAY = (20, 200)  # simge capanin 20 px altina / 200 px ustune kadar
SIMGESIZ_CAPA: tuple[tuple[int, str, int], ...] = ()

# Numara seridi: sutun basina sabit x (olculdu, 322 test sayfasinda sapma yok).
NUMARA_X = {1: {"L": (64, 69), "R": (383, 387)}, 0: {"L": (69, 73), "R": (388, 392)}}
NUMARA_UST = {1: 120, 0: 75}  # tek sayfada ust bant daha kalin
NUMARA_BOY = (6, 14)  # grup yuksekligi
_ROZET_X = (35, 135)  # hap, sutun solundan bu aralikta
_ROZET_BOY = (11, 22)
_ROZET_EN_AZ_W = 55
_ROZET_G_EN_COK = 115  # hap (22,101,144); acik mavi tablo basligi (2,128,200)
_ROZET_B_EN_COK = 170
_ROZET_NUMARA_PAY = 45  # rozetin bu kadar altinda numara varsa rozet capa degil


def _numara_capalari(a: np.ndarray, n: int) -> list[dict]:
    """Sutunun sabit x'inde basili soru numarasi (sol komsulugu bos)."""
    from scipy import ndimage

    ust = NUMARA_UST[n % 2]
    out: list[dict] = []
    for sut, (x0, x1) in NUMARA_X[n % 2].items():
        b = a[ust:SAYFA_ALTI, x0 - 12 : x1 + 40]
        koyu = b.max(axis=2) < 150
        lab, _ = ndimage.label(koyu)
        ham = []
        for s in ndimage.find_objects(lab):
            h = s[0].stop - s[0].start
            w = s[1].stop - s[1].start
            gx = s[1].start + x0 - 12
            if not (6 <= h <= 14 and 3 <= w <= 26) or not (x0 <= gx <= x1):
                continue
            if koyu[s[0].start : s[0].stop, max(0, s[1].start - 10) : s[1].start].any():
                continue
            ham.append((s[0].start, s[0].stop, s[1].start, s[1].stop))
        grup: list[tuple[int, int, int, int]] = []
        for y0, y1, xa, xb in sorted(ham):
            if grup and abs(grup[-1][0] - y0) <= 4 and xa - grup[-1][3] <= 4:
                g = grup[-1]
                grup[-1] = (min(g[0], y0), max(g[1], y1), g[2], xb)
            else:
                grup.append((y0, y1, xa, xb))
        for y0, y1, xa, _xb in grup:
            if NUMARA_BOY[0] <= y1 - y0 <= NUMARA_BOY[1]:
                out.append({"sutun": sut, "y": y0 + ust, "x": xa + x0 - 12})
    return out


def _rozet_capalari(a: np.ndarray, n: int) -> list[dict]:
    """Kaynak rozeti: koyu lacivert dolu hap ('2023 / MSU'), sutun solunda."""
    from scipy import ndimage

    ust = NUMARA_UST[n % 2]
    out: list[dict] = []
    for sut in ("L", "R"):
        x0 = SUTUNLAR[n % 2][sut][0]
        b = a[ust:SAYFA_ALTI, x0 + _ROZET_X[0] : x0 + _ROZET_X[1]]
        r, bl = b[..., 0], b[..., 2]
        m = (r < 95) & (bl > 100) & (bl - r > 35)
        lab, _ = ndimage.label(m)
        for i, s in enumerate(ndimage.find_objects(lab), 1):
            h = s[0].stop - s[0].start
            w = s[1].stop - s[1].start
            mk = lab[s] == i
            if not (_ROZET_BOY[0] <= h <= _ROZET_BOY[1] and w >= _ROZET_EN_AZ_W):
                continue
            if mk.mean() < 0.55:
                continue
            if b[s][..., 1][mk].mean() > _ROZET_G_EN_COK:
                continue
            if b[s][..., 2][mk].mean() > _ROZET_B_EN_COK:
                continue
            out.append(
                {
                    "sutun": sut,
                    "y": s[0].start + ust,
                    "x": s[1].start + x0 + _ROZET_X[0],
                    "tur": "rozet",
                }
            )
    return out


def capa_numaralari(a: np.ndarray, n: int) -> list[dict]:
    """Sayfanin capalari: basili numaralar + numarasiz rozetli sorular.

    Rozet ('2023 / MSU') sorunun BASLIGIDIR: numarasi varsa capa numaranindir
    ama capa y'si rozetin ustune cekilir (kutu rozeti icine alsin; yoksa kutu
    asamasinda 'artik murekkep' cikar). Numarasi yoksa rozet tek basina capa."""
    nn = _numara_capalari(a, n)
    tek: list[dict] = []
    for c in _rozet_capalari(a, n):
        es = [
            g
            for g in nn
            if g["sutun"] == c["sutun"] and 0 < g["y"] - c["y"] <= _ROZET_NUMARA_PAY
        ]
        if es:
            min(es, key=lambda g: g["y"])["y"] = c["y"]
        else:
            tek.append(c)
    return sorted(nn + tek, key=lambda c: (c["sutun"], c["y"]))


# 'AKILLI NOT' bilgi kutusu: acik mavi (198,223,234) yuvarlak cerceve, ic zemin
# beyaz. Soru degildir (simgesi vardir ama numarasi / rozeti yoktur): kutulara
# girmemeli, artik murekkep sayilmamali.
_NOT_CERCEVE = ((198, 25), (223, 22), (234, 22))
_NOT_EN_AZ = (60, 200)  # yukseklik, genislik
# Kirmizi 'AKILLI NOT' basligi: blogun ust bandinda, SOLA dayali, tek satir.
# Olculdu (36 gercek kutu): px 411-529, dy 6-25, dx 0-106.
_NOT_BASLIK_PX = 400
_NOT_BASLIK_DY = 30  # baslik bandi: blogun ilk bu kadar satiri
_NOT_BASLIK_DX = (30, 120)  # sol kenardan en cok / saga en cok uzanma


def dislama_bolgeleri(a: np.ndarray, n: int) -> list[tuple[int, int, int, int]]:
    """'AKILLI NOT' kutulari (y0, y1, x0, x1).

    Kutunun ici kimi sayfada beyaz (cerceve halka), kimi sayfada acik mavi
    dolu; ayirt edici olan KIRMIZI BASLIKTIR. Acik mavi zeminli SEKILLER
    (s53 tekne, s98 masa, s106 kirmizi arabali yol) bu baslik bicimini
    tutturamaz: ya kirmizisi yok ya da sola dayali tek satir degil."""
    from scipy import ndimage

    m = np.ones(a.shape[:2], bool)
    for k, (orta, pay) in enumerate(_NOT_CERCEVE):
        # astype(int): beyazlatilmis sayfa uint8 gelir, cikarma tasar.
        m &= abs(a[..., k].astype(int) - orta) < pay
    lab, _ = ndimage.label(
        ndimage.binary_dilation(m, ndimage.generate_binary_structure(2, 2))
    )
    r, g, b = (a[..., i].astype(int) for i in range(3))
    kirmizi = (r > 170) & (g < 110) & (b < 120)
    out = []
    for s in ndimage.find_objects(lab):
        h = s[0].stop - s[0].start
        w = s[1].stop - s[1].start
        if h < _NOT_EN_AZ[0] or w < _NOT_EN_AZ[1]:
            continue
        band = kirmizi[s[0].start : s[0].start + _NOT_BASLIK_DY, s[1]]
        if int(band.sum()) < _NOT_BASLIK_PX:
            continue
        xs = np.where(band)[1]
        if int(xs.min()) > _NOT_BASLIK_DX[0] or int(xs.max()) > _NOT_BASLIK_DX[1]:
            continue
        out.append((s[0].start, s[0].stop, s[1].start, s[1].stop))
    return out


SERIT_HUCRE_TARIFI = (
    "Goruntu sayfanin sol altindaki cevap serididir: acik gri '1. C  2. C ...' "
    "(numara, nokta, harf), tek satir."
)
ANAHTAR_NEREDEN = (
    "her test sayfasinin sol altindaki duz metin serit ('1. C  2. C ...') + "
    "testin ilk sayfasinin ust bandi"
)
ANAHTAR_DISLA_X = None
# Serit acik gri, 1x'te ~7 px duz metin: glif kanali bolutlenemiyor (segment 0).
# ARO23PG'deki gibi dogrulama IKI BAGIMSIZ OKUMA (A / B) ile yapilir.
GLIF_KAPISI = False
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (5, 12)
GLIF_HARF_W_EN_COK = 14
HARF_NOKTA_SONRASI = True
HUCRE_BOSLUK = 5

BANT_Y_ALT = 115
BANT_TARIFI = (
    "Ust bantta solda bordo daire icinde 'Test N', ortada gri kutuda BUYUK "
    "HARFLI konu adi ('FIZIK BILIMINE GIRIS - 1')."
)
BANT_KONU_TARIFI = "ortadaki gri kutudaki konu adini (sondaki '- N' dahil degil)"
BANT_TEST_NO_TARIFI = "soldaki bordo dairedeki sayiyi"
BANT_KONU_KAPISI = False

SUTUNLAR = {0: {"L": (40, 366), "R": (360, 715)}, 1: {"L": (36, 360), "R": (356, 710)}}
# Iki sayfa susu olcume karisir:
#   * sutunlar arasi dikey ayrac + 'BILGI SARMAL' sirt yazisi sag sutunun
#     solunda (x 373 cift / 368 tek, 600 satir koyu);
#   * DIS kenarda dikey 'TYT FIZIK SORU BANKASI' yazisi (tek sayfada sagda
#     x 683-689, cift sayfada solda x 52-58).
# Ikisi de olcum araligindan dusulur; kutunun kendi x sinirlari degismez.
SUTUN_OLCUM_PAY = {0: {"L": (20, 0), "R": (20, 0)}, 1: {"R": (20, 30)}}
UST_BANT = 75  # cift sayfa: ust bant yok, yalniz sayfa ustu payi
_BANT_UST_Y = 80  # bant ust kenari (olculdu: tek sayfalarda 495-496 px)
_BANT_ALT_Y = 121  # bant alt kenari (507-529 px); ilk soru numarasi y ~131
_BANT_ESIK = 450


def ust_bant(a: np.ndarray) -> int:
    """Testin ILK (tek) sayfasinda ust bant var: 'Test N' dairesi + gri konu
    kutusu; kenarlari tam genislik cizgi (y 80 ve y 121). Devam (cift)
    sayfasinda bant yok, ilk soru y ~83'te -> UST_BANT."""
    b = a[:, 30:715]
    say = (b.min(axis=2) < 235).sum(axis=1)
    if say[_BANT_UST_Y] > _BANT_ESIK and say[_BANT_ALT_Y] > _BANT_ESIK:
        return _BANT_ALT_Y + 2
    return UST_BANT


# Sag sutun icerigi y 900'e kadar iner (s311 D/E sik sekilleri), 901-907 bos,
# 908'den sonra kose susu / cevap seridi.
SAYFA_ALTI = 904
SAYFA_ALTLIGI_Y = 905
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1330

KOK_KOD = "FIZ"
KOD_ONEKI = "FIZ-BS24FZ"
ALAN = "FIZIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = "icindekiler: 5 bolum, 63 konu (s4-s5)"
BOLUMLER: tuple[tuple[int, str], ...] = (
    (
        1,
        "1. B\u00d6L\u00dcM F\u0130Z\u0130K B\u0130L\u0130M\u0130NE G\u0130R\u0130\u015e, MADDE B\u0130LG\u0130S\u0130",
    ),
    (
        2,
        "2. B\u00d6L\u00dcM HAREKET - KUVVET - \u0130\u015e G\u00dc\u00c7 - ENERJ\u0130",
    ),
    (3, "3. B\u00d6L\u00dcM ELEKTR\u0130K VE MANYET\u0130ZMA"),
    (4, "4. B\u00d6L\u00dcM OPT\u0130K"),
    (5, "5. B\u00d6L\u00dcM DALGALAR"),
)
# Icindekiler s4-s5 (gozle okundu): konu = ayni ada sahip ardisik test grubu;
# 'OSYM Tipi', 'Sarmal Test', 'Simulasyon Testi' kendi konularidir.
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Fizik Bilimine Giri\u015f", 7),
    (1, "\u00d6zk\u00fctle", 15),
    (1, "Dayan\u0131kl\u0131l\u0131k, Adezyon, Kohezyon", 23),
    (1, "\u00d6SYM Tipi-1", 31),
    (1, "Kat\u0131 Bas\u0131nc\u0131", 33),
    (1, "S\u0131v\u0131 Bas\u0131nc\u0131", 41),
    (1, "Gaz ve Ak\u0131\u015fkan Bas\u0131nc\u0131", 49),
    (1, "\u00d6SYM Tipi-2", 57),
    (1, "S\u0131v\u0131lar\u0131n Kald\u0131rma Kuvveti", 59),
    (1, "Sarmal Test-1", 67),
    (1, "\u00d6SYM Tipi-3", 69),
    (1, "Is\u0131 S\u0131cakl\u0131k", 71),
    (1, "Genle\u015fme, Is\u0131 \u0130letimi", 79),
    (1, "Sarmal Test-2", 87),
    (1, "\u00d6SYM Tipi-4", 89),
    (1, "Sim\u00fclasyon Testi", 91),
    (2, "Hareket", 95),
    (2, "Sarmal Test-3", 107),
    (2, "\u00d6SYM Tipi-1", 109),
    (2, "Kuvvet ve \u00d6zellikleri", 111),
    (2, "Dinamik", 119),
    (2, "\u00d6SYM Tipi-2", 127),
    (2, "\u0130\u015f G\u00fc\u00e7 Enerji", 129),
    (2, "Sarmal Test-4", 139),
    (2, "\u00d6SYM Tipi-3", 141),
    (2, "Sim\u00fclasyon Testi", 143),
    (3, "Elektrik Y\u00fckleri", 147),
    (3, "Elektrostatik", 153),
    (3, "Coulomb Kuvveti ve Elektrik Alan", 161),
    (3, "Sarmal Test-5", 167),
    (3, "\u00d6SYM Tipi-1", 169),
    (3, "Ohm Yasas\u0131", 171),
    (3, "Piller", 183),
    (3, "Elektriksel G\u00fc\u00e7 ve Enerji", 187),
    (3, "Lamba Parlakl\u0131\u011f\u0131", 193),
    (3, "\u00d6SYM Tipi-2", 199),
    (3, "Manyetizma", 201),
    (3, "Sarmal Test-6", 209),
    (3, "\u00d6SYM Tipi-3", 211),
    (3, "Sim\u00fclasyon Testi", 213),
    (4, "Ayd\u0131nlanma", 217),
    (4, "G\u00f6lge", 223),
    (4, "\u00d6SYM Tipi-1", 229),
    (4, "Yans\u0131ma ve D\u00fczlem Ayna", 231),
    (4, "Sarmal Test-7", 239),
    (4, "K\u00fcresel Ayna", 241),
    (4, "K\u0131r\u0131lma", 249),
    (4, "Mercekler", 257),
    (4, "\u00d6SYM Tipi-2", 265),
    (4, "Prizma", 267),
    (4, "Renk", 275),
    (4, "\u00d6SYM Tipi-3", 283),
    (4, "Sarmal Test-8", 285),
    (4, "Sim\u00fclasyon Testi", 287),
    (5, "Dalgalar ve Genel \u00d6zellikleri", 291),
    (5, "Yay Dalgalar\u0131", 297),
    (5, "Sarmal Test-9", 305),
    (5, "Su Dalgalar\u0131", 307),
    (5, "Deprem ve Ses Dalgalar\u0131", 315),
    (5, "Sarmal Test-10", 323),
    (5, "\u00d6SYM Tipi", 325),
    (5, "Sim\u00fclasyon Testi", 327),
    (5, "E\u011filim Kontrol Testi", 329),
)
SON_SAYFA = 336
BANT_ESLER: dict[str, str | tuple[str, ...]] = {}

KITAP_BASLIGI = "BILGI SARMAL 2024 TYT Fizik Soru Bankas\u0131"
GRUP_SORU = 60
SEKIL_SATIRI = True
TALIMAT_EK = ""

DERSLER = ("FIZIK",)
ESKI_KAYNAKLAR: tuple[str, ...] = ()
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Bilgi Sarmal Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "FIZ_BILGI_SARMAL_2024_TYT_YONTEM.md"

SONUC: dict = {}
