"""2022-2023 ACIL Analitik Geometri (Konu Anlatimli Soru Fasikulu) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 176 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi.

SAYFA DUZENI (kontak sayfasi + olcum, 27 Eyl 2026)
-------------------------------------------------
* Konu anlatim sayfalari: ust bantta genis sari/kirmizi/lacivert cubuk
  (bant y 10-60 satirinda sari piksel 197); ORNEK / COZUM kutulari -- cozumlu
  ornek, test sorusu DEGIL, kapsam disi.
* Test sayfalari: ince cerceveli bant, kirmizi 'Test - N' + bolum adi; bantta
  yalniz kucuk logo karelerinin sarisi (12 px). Test ici numara kirmizi,
  solunda okuyucu simgesi (buyutec, dolgusuz halka: 3x3 genisletilmis 14x15).
* Cevap anahtari: testin SON sayfasinin sag altinda 6 sutunlu tablo
  ('1. E | 2. A ...', kirmizi numara + siyah harf), 301 px yatay koyu
  cizgiler 16 px arayla (1 ya da 2 satir).
* 4 bolum: Nokta Analitigi (Test I-6, s22-35), Dogru Analitigi (Test 1-12,
  s72-101), Donusum Geometrisi (Test 1-7, s119-134), Cember Analitigi
  (Test 1-8, s155-175). Kapak / kareli bos sayfalar: 1-8, 36-37, 102-104,
  135-136, 176.
"""

from __future__ import annotations

import numpy as np

KOD = "ACL23AG"
KAYNAK_ADI = "2022-2023 ACIL Analitik Geometri"
CIKTI_ONEK = "acil_2023_analitik_geometri"
KLASOR = "2022-2023-AC\u0130L-Analitik Geometri"
VERAF = "b1"
KART = (589, 43, 1331, 1022)
BEKLENEN_SAYFA = 176
BEKLENEN_TEST = 33
TEST_SAYFALARI = ((22, 35), (72, 101), (119, 134), (155, 175))
ANAHTAR_KAPSAMI = "test"

# --- capa (olculdu: s22-35, a_olc_glif) ---
GLIF_GENISLET = True
GLIF_BOY = (12, 17, 12, 17)  # h0, h1, w0, w1 (genisletilmis)
SIMGE_X = {1: {"L": 13, "R": 347}, 0: {"L": 32, "R": 363}}
SIMGE_TOLERANS = 16
PENCERE = (-6, 30, 18, 52)  # y0, y1, x0, x1 simge sol-ustune gore
NUMARA_H = (6, 16)
NUMARA_W_EN_COK = 30
NUMARA_DX = (14, 44)  # iki basamakli numara daha solda baslar
SERIT_SIMGE_PAY = 10
# Numarasi BASILMAMIS soru (gozle: s92 sag sutun alt soru, 'Dik koordinat
# duzleminde K noktasinda kesisen d1 ve d2...'; simge var, kirmizi numara yok).
NUMARASIZ_CAPA = ((92, 579, 378),)

# --- cevap anahtari ---
ANAHTAR_NEREDEN = (
    "her testin son sayfasinin sag altindaki 6 sutunlu cevap tablosu (1. E | 2. A ...) "
    "+ testin ilk sayfasinin ust bandi (bolum adi, 'Test - N')"
)
BANT_Y_ALT = 80
BANT_TARIFI = (
    "Bir kenarda kirmizi 'Test - N' (N roma rakami ya da sayi), diger kenarda "
    "koyu lacivert BOLUM ADI (ornek 'NOKTA ANALITIGI')."
)
BANT_KONU_TARIFI = "banttaki koyu lacivert BOLUM ADINI"
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (6, 12)
GLIF_HARF_W_EN_COK = 14

# --- harita (icindekiler s3, bolum kapaklari s5/37/103/135) ---
KOK_KOD = "GEO"
KOD_ONEKI = "GEO-ACL23AG"
ALAN = "GEOMETRI"
SINAV = "AYT"
SINIF = 12
HARITA_NEREDEN = (
    "icindekiler (s3) + bolum kapaklari + test ilk sayfasi ust bandi (iki okuma)"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "NOKTA ANAL\u0130T\u0130\u011e\u0130"),
    (2, "DO\u011eRU ANAL\u0130T\u0130\u011e\u0130"),
    (3, "D\u00d6N\u00dc\u015e\u00dcM GEOMETR\u0130S\u0130"),
    (4, "\u00c7EMBER ANAL\u0130T\u0130\u011e\u0130"),
)
# Yalniz TEST bolumleri (konu anlatim araliklari 5 / 37 / 103 / 135 test
# tasimaz; ORNEK-COZUM kapsam disi). Basili sayfa = dosya.
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Nokta Analiti\u011fi Testler", 22),
    (2, "Do\u011fru Analiti\u011fi Testler", 72),
    (3, "D\u00f6n\u00fc\u015f\u00fcm Geometrisi Testler", 119),
    (4, "\u00c7ember Analiti\u011fi Testler", 155),
)
SON_SAYFA = 175
BANT_ESLER: dict[str, str] = {
    "NOKTA ANALITIGI": "NOKTA ANALITIGI TESTLER",
    "DOGRU ANALITIGI": "DOGRU ANALITIGI TESTLER",
    "DONUSUM GEOMETRISI": "DONUSUM GEOMETRISI TESTLER",
    "CEMBER ANALITIGI": "CEMBER ANALITIGI TESTLER",
}

# --- kutu / kirpim (olculdu: test sayfalari murekkep projeksiyonu) ---
# Kirmizi dikey 'ACIL MATEMATIK' ayraci tek x 362, cift x 378-379; murekkep
# tek 14..676, cift 33..692. Ayracin dikey yazisi tek 356-366, cift 373-383
# (kirmizi); sol sutun metni <= 349 / 365, sag sutun >= 375 / 392 (tum test
# sayfalari, disk beyazlatilmis). Test bandi alti kirmizi cizgi y 75-76; sayfa
# numarasi ve alt kirmizi cizgi y 918-928.
SUTUNLAR = {1: {"L": (36, 352), "R": (369, 700)}, 0: {"L": (52, 369), "R": (386, 716)}}
UST_BANT = 79
SAYFA_ALTI = 912
SERIT_PAY = 8
BEKLENEN_SORU = 361
# Okuyucu diski (s30 olculdu): glif (genisletilmis) sol-ust + (10, 8) merkez,
# disk y 78-106 / x 25-55 -> yaricap 17 (golge dahil).
DISK_MERKEZ = (10, 8)
BEYAZ_YARICAP = 17
HALKA = (19, 23)
LEKE = None

# --- metin ---
KITAP_BASLIGI = "2022-2023 AC\u0130L Analitik Geometri"
GRUP_SORU = 24
TALIMAT_EK = (
    "## Numaras\u0131 bas\u0131lmam\u0131\u015f soru\n"
    "Kitapta numaras\u0131 BASILMAMI\u015e tek bir soru var (ACL23AG-T015_04: k\u0131rp\u0131m\u0131n solunda "
    "k\u0131rm\u0131z\u0131 numara yok). Orada `basili_no: null` yaz; numara uydurma."
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
# Ayni kitabin eski aktarimi (DB'deki ad, Turkce harfle): 1 satir, aktif.
ESKI_KAYNAKLAR = ("2022-2023-AC\u0130L-Analitik Geometri",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "GEO_ACIL_2023_ANALITIK_YONTEM.md"

# --- olculen sonuc (tests/e2e/test_kitap_hat.py bunlari dogrular) ---
SONUC = {
    "sayfa_turu": {"kapak": 8, "konu": 87, "test": 81},
    "harf": {"A": 47, "B": 69, "C": 96, "D": 85, "E": 64},
    "glif_hucre": 259,
    "glif_uyum": 256,
    "goz_teyit": {"T001#4": "D", "T017#6": "D", "T017#7": "C"},
    "glif_disi": [5, 7, 9, 11, 16, 20, 28, 32, 33],
    "metin_parca": 14,
    "farkli_soru": 16,
    "okunamaz": 10,
    "ithal": 360,
    "beta": "350/360",
    "eski_modern": 1,
    "migration_no": 77,
    "onceki": "0076_acl21t_beta_onay",
}

SARI_BANT_ESIK = 60  # konu sayfasi 197, test 12, kapak 0/138
KIRMIZI_CIZGI_ESIK = 600


def sayfa_turu(a: np.ndarray, n: int) -> str:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sari = (r > 230) & (g > 160) & (b < 120)
    if int(sari[10:60].sum(axis=1).max()) > SARI_BANT_ESIK:
        return "konu"
    kir = (r > 170) & (g < 100) & (b < 110)
    # test bandi: tam genislik ince kirmizi cerceve cizgisi (olculdu: 724/725 px;
    # kapak 61, diger 0)
    return "test" if int(kir[0:80].sum(axis=1).max()) > KIRMIZI_CIZGI_ESIK else "kapak"


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Sag alt 6 sutunlu cevap tablosu: y >= 800'de 290-310 px koyu yatay cizgi (>= 2)."""
    mx, mn = a.max(axis=2), a.min(axis=2)
    koyu = (mx < 150) & (mx - mn < 30)
    satir = koyu[800:].sum(axis=1)
    ys = [int(y) + 800 for y in np.where((satir >= 290) & (satir <= 310))[0]]
    if len(ys) < 2:
        return None
    xs = np.where(koyu[ys[0]])[0]
    x0, x1 = int(xs.min()), int(xs.max())
    # Izgara cizgileri tablonun x araliginda sayilir: ust cizgiye yandaki metin
    # (331/336 px), alt cizgiye golge/ortusme (251 px) karisabiliyor (olculdu:
    # testler 7, 13, 19, 23).
    # Son satir eksik hucreliyse alt cizgi kisa (10 hucre: 4 hucrelik cizgi,
    # test 24 / 32): cizgi = x araliginda >= CIZGI_EN_AZ px KESINTISIZ koyu kosu.
    cizgi = [
        y
        for y in range(780, a.shape[0])
        if _en_uzun_kosu(koyu[y, x0 : x1 + 1]) >= CIZGI_EN_AZ
    ]
    return [cizgi[0], cizgi[-1], x0, x1]


CIZGI_EN_AZ = 90


def _en_uzun_kosu(v: np.ndarray) -> int:
    en = say = 0
    for x in v:
        say = say + 1 if x else 0
        en = max(en, say)
    return en
