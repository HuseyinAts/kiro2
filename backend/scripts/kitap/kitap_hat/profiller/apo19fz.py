"""2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi (Apotemi 'konu testi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 448 PNG (+ goruntu PDF'i); kart
(589,43)-(1331,1022). Basili sayfa = dosya (icindekiler s6-7 ile gozle).
Kesif: kitap_hat/kesif.py (_kesif_apo19fz).

SAYFA DUZENI (olculdu, _a21_gecici/c5_*.py; 29 Eyl 2026):
* 4 bolum (acilis dosya 9, 143, 247, 345); 144 / 248 / 346 ve 10 baska
  kitaplarin reklam sayfasi (okuyucu simgeli ornek sorular tasir) -> kapak.
* Her test IKI sayfa (tek + cift); ust bantta yesil kutuda BUYUK HARFLE konu
  (icindekilerdeki kalin baslik), beyaz zeminde alt konu ve 'Test N'.
* Cevap seridi cift sayfanin altliginda: soluk sari (240,236,189) kutularda
  gri '1-D 2-E ...' (y 892-904; c5_serit.py: 216 cift sayfa, 216 test).
* Okuyucu simgesi numaranin solunda ayni satirda L 74 / R 361, numara
  kirmizi (kesif).
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
from scripts.kitap.kitap_hat.profiller.apo19mt import hucre_harf_bloblari

KOD = "APO19FZ"
KAYNAK_ADI = "2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi"
CIKTI_ONEK = "apotemi_2019_tyt_ayt_fizik"
KLASOR = "Apotemi 2019 2020 Tyt Ayt Fizik Soru Bankas\u0131"
VERAF = "c5"
BEKLENEN_SAYFA = 448
BEKLENEN_TEST = 216
ANAHTAR_KAPSAMI = "test"
TEST_SINIRI = "anahtar"
TEST_SAYFALARI = ((11, 142), (145, 246), (249, 344), (347, 448))
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))

# --- anahtar seridi ---
SERIT_Y = (886, 910)


def _kutu_maskesi(a: np.ndarray) -> np.ndarray:
    r, g, b = (a[..., i].astype(int) for i in range(3))
    m: np.ndarray = (r > 215) & (g > 210) & (b > 140) & (b < 205) & (r - b > 35)
    return m


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Altliktaki soluk sari kutu dizisi: genisligi >= 18 px olan kutu kosulari
    (soldaki azalan noktalar <= 12 px, sayfa no kutusu parlak sari -> disarida).
    Bos son kutu da kosuya girer; okuyucu yalniz yazili hucreleri okur."""
    y0, y1 = SERIT_Y
    m = _kutu_maskesi(a[y0:y1])
    satir = np.where(m.sum(axis=1) > 150)[0]
    if len(satir) == 0:
        return None
    kol = m[satir].any(axis=0)
    kos, x = [], 0
    while x < len(kol):
        if kol[x]:
            xa = x
            while x < len(kol) and kol[x]:
                x += 1
            if x - xa >= 18:
                kos.append((xa, x))
        x += 1
    if len(kos) < 3:
        return None
    return [y0 + int(satir[0]), y0 + int(satir[-1]) + 1, kos[0][0], kos[-1][1]]


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in _TEST:
        return "test"
    return "kapak"


SERIT_HUCRE_TARIFI = (
    "Goruntu sayfa altligindaki cevap seridir: soluk sari kutularda gri "
    '"1-D", "2-E" ... (numara, tire, harf), tek satir. Sondaki BOS kutu '
    "hucre degildir; soldaki noktalar ve sari sayfa numarasi hucre degildir."
)
ANAHTAR_NEREDEN = (
    "her testin ikinci (cift) sayfasinin altligindaki serit: soluk sari kutularda "
    "'numara-harf'"
)
ANAHTAR_DISLA_X = None
GLIF_HARF_ESIK = 190
GLIF_HARF_H = (6, 11)
GLIF_HARF_W_EN_COK = 10
HUCRE_BOSLUK = 5


def harf_bloblari(s: np.ndarray) -> list[tuple[slice, slice]]:
    out: list[tuple[slice, slice]] = hucre_harf_bloblari(s, GLIF_HARF_ESIK)
    return out


BANT_Y_ALT = 100
BANT_TARIFI = (
    "Ust bantta yesil kutularda BUYUK HARFLE konu adi ve 'Test N' yazar; "
    "aralarinda beyaz zeminde alt konu adi (kalin, kucuk harf) olabilir."
)
BANT_KONU_TARIFI = "yesil kutudaki BUYUK HARFLI konu adini (alt konu adini DEGIL)"
BANT_TEST_NO_TARIFI = "'Test N' yazisindaki N sayisini"
BANT_KONU_KAPISI = True

# --- capa ---
SIMGE_X = {0: {"L": 74, "R": 361}, 1: {"L": 74, "R": 361}}
SIMGE_TOLERANS = 14
PENCERE = (-10, 37, 15, 52)
NUMARA_H = (7, 12)
NUMARA_W_EN_COK = 30
NUMARA_DX = (13, 40)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Capa numaradan (gozle; c5_numara.py): s186 R '11.' simgesiz (sayfadaki tek
# fazla simge dikey APOTEMI sekmesinin uzerinde, numarasiz); s216 L '5.' simgesi
# seklin altina kaymis (y 229, blob_yok); s125 R '6.', s307 R '4.' ve '5.' okuyucu
# simgesi konmamis (anahtar hucresi capadan fazla; gozle).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = (
    (125, "R", 631, 389),
    (186, "R", 346, 388),
    (216, "L", 113, 99),
    (307, "R", 368, 389),
    (307, "R", 621, 389),
)
KUTU_UST: dict[tuple[int, str, int], int] = {}
# s307 R '4.' (EK_CAPA): onceki sorunun E sikki (y 347-357) ile numara (y 368)
# arasi 9 bos satir (< BOSLUK): ust, bos kosunun basindan (ust_artik.py).
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {(307, "R", 1): 361}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
# s88 L 5. soru: tablo metni ('LM arasi ve L ye yakin') x 359'da biter, sutun
# siniri 361 (sekme 361'den); kirpim gozle tam (c5_kes.py 88).
KENAR_GOZ_ONAY: tuple[str, ...] = ("APO19FZ-T039_05",)
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["kirmizi"](a)
    return m


# --- harita (icindekiler s6-7; dosya = basili) ---
KOK_KOD = "FIZ"
KOD_ONEKI = "FIZ-APO19FZ"
ALAN = "FIZIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s6-7): 4 bolum, 36 kalin konu basligi (alt basliklar test bandinda "
    "beyaz zeminde); konu = test bandindaki yesil BUYUK HARFLI ad (iki bagimsiz okuma), "
    "sayfa araligi icindekiler sayfa numarasindan (dosya = basili)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "1. B\u00d6L\u00dcM"),
    (2, "2. B\u00d6L\u00dcM"),
    (3, "3. B\u00d6L\u00dcM"),
    (4, "4. B\u00d6L\u00dcM"),
)
# (bolum, icindekiler adi, baslangic, sinav, sinif). Sinav / sinif etiketi kitapta
# basili DEGIL: MEB 2018 fizik programi unite sinifi (9-10 TYT, 11-12 AYT);
# karma tekrar testleri (2. ve 3. bolum) icerdikleri AYT konulari icin AYT.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "Fizik Bilimine Giri\u015f", 11, "TYT", 9),
    (1, "Madde ve \u00d6zellikleri", 17, "TYT", 9),
    (1, "S\u0131v\u0131lar\u0131n Kald\u0131rma Kuvveti", 27, "TYT", 10),
    (1, "Bas\u0131n\u00e7", 39, "TYT", 10),
    (1, "Is\u0131 ve S\u0131cakl\u0131k", 59, "TYT", 9),
    (1, "Genle\u015fme", 77, "TYT", 9),
    (1, "Tekrar Testi", 83, "TYT", 9),
    (1, "Vekt\u00f6rler", 95, "AYT", 11),
    (1, "Kuvvet ve Denge", 101, "AYT", 11),
    (1, "Tork", 113, "AYT", 11),
    (1, "Basit Makineler", 121, "AYT", 11),
    (1, "A\u011f\u0131rl\u0131k Merkezi", 137, "AYT", 11),
    (2, "Hareket", 145, "TYT", 9),
    (2, "Ba\u011f\u0131l Hareket", 159, "AYT", 11),
    (2, "Newton'un Hareket Yasalar\u0131", 163, "TYT", 9),
    (2, "Yery\u00fcz\u00fcnde At\u0131\u015f Hareketleri", 177, "AYT", 11),
    (2, "\u0130\u015f - G\u00fc\u00e7 - Enerji", 187, "TYT", 9),
    (2, "Tekrar Testi", 213, "AYT", 11),
    (2, "\u0130tme ve \u00c7izgisel Momentum", 221, "AYT", 11),
    (2, "D\u00fczg\u00fcn \u00c7embersel Hareket", 231, "AYT", 12),
    (2, "A\u00e7\u0131sal Momentum", 235, "AYT", 12),
    (2, "Genel \u00c7ekim ve Kepler Kanunlar\u0131", 239, "AYT", 12),
    (2, "Basit Harmonik Hareket", 243, "AYT", 12),
    (3, "Elektrostatik", 249, "TYT", 9),
    (3, "Elektriksel Potansiyel", 267, "AYT", 11),
    (3, "D\u00fczg\u00fcn Elektrik Alan ve S\u0131\u011fa", 269, "AYT", 11),
    (3, "Elektrik Ak\u0131m\u0131", 277, "TYT", 10),
    (3, "Tekrar Testi", 309, "AYT", 11),
    (3, "Manyetizma", 315, "AYT", 11),
    (4, "Optik", 347, "TYT", 10),
    (4, "Dalgalar", 381, "TYT", 10),
    (4, "Tekrar Testi", 395, "TYT", 10),
    (4, "Dalga Mekani\u011fi", 401, "AYT", 12),
    (4, "Atom Fizi\u011fine Giri\u015f ve Radyoaktivite", 417, "AYT", 12),
    (4, "Modern Fizik", 435, "AYT", 12),
    (4, "Modern Fizi\u011fin Teknolojideki Uygulamalar\u0131", 445, "AYT", 12),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s) for b, ad, s, _, _ in _KONULAR
)


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinav, sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = (sinav, sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 448
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (ilk olcum kesif; kutu / kirp kapilariyla duzeltilir) ---
# Dikey mavi APOTEMI sekmesi orta ayracin ustunde x 361-380 (s88 kolon olcumu):
# L sutunu 361'de biter (dahil degil).
SUTUNLAR = {0: {"L": (28, 361), "R": (381, 712)}, 1: {"L": (28, 361), "R": (381, 712)}}
# Ust bant (yesil kutular) y 75-96. Altlik: gri tam genislik cizgi y ~879,
# altinda serit / sayfa no.
UST_BANT = 98
SAYFA_ALTI = 876
# Gri cizgi koyu esigin (160) ustunde: alt tarama cizgide durmaz, altligin
# noktalari / sayfa no'su (y 887-888) 'alt sinir altinda murekkep' olurdu.
SAYFA_ALTLIGI_Y = 878
# Cift sayfada serit (y 892) altlikta: kutu alt siniri seridin ustu degil SAYFA_ALTI
# (yoksa sol sutunun son kutusu cizgiyi ve sari sayfa no blokunu icine alir).
SERIT_ALTLIKTA = True
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 2180

# --- metin ---
KITAP_BASLIGI = "2019-2020 Apotemi TYT-AYT Fizik Soru Bankas\u0131"
GRUP_SORU = 60
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi kirmizi basilidir; her test 1'den baslar. Fizik birimleri "
    "ve indisler basildigi gibi: `m/s^2`, `F_1`, `v_0`, `10 N`; harfin ustunde "
    "vektor oku basiliysa harfi yaz, oku `kaynak_kusuru` sayma. Sekil icindeki "
    "olcu ve etiketler soru onlara dayaniyorsa kisa satirlar halinde govdeye "
    "girer.\n"
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
YAYINEVI = "Apotemi Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "FIZ_APOTEMI_2019_TYT_AYT_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 16, "test": 432},
    "harf": {"A": 434, "B": 444, "C": 454, "D": 452, "E": 396},
    "glif_hucre": 2180,
    "glif_uyum": 2180,
    "goz_teyit": {},
    "glif_disi": [],
    "metin_parca": 34,
    "farkli_soru": 455,
    "okunamaz": 46,
    "ithal": 2180,
    "beta": "2132/2180",
    "eski_modern": 0,
    "migration_no": 119,
    "onceki": "0118_apo19mt_beta_onay",
}
