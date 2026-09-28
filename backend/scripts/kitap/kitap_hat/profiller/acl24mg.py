"""2024 ACIL TYT Matematik Geometri Kitap-1 (MOZ Akademi duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 208 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi (s9, s10 ... sayfa altinda basili; gozle).
Icerik TYT matematik (sayilar .. oran-oranti); geometri bu ciltte yok.

SAYFA DUZENI (kontak sayfasi + olcum, 28 Eyl 2026)
-------------------------------------------------
* Konu anlatim sayfalari: yuvarlak halka icinde numarali cozumlu ORNEKLER
  (cogu acik uclu, sayfa altindaki seritte sayisal/metin cevap) -- kapsam
  DISI.
* Test sayfalari: ust bantta ic kenarda 'KONU TESTLERI' sekmesi, dis kenarda
  '<konu> / Test - N'. Her test TEK sayfa; sorular 1..N, numara MAVI
  ('1.'), solunda okuyucu simgesi. Cevap: sayfanin altinda tek satir serit
  ('1) C | 2) D ...'), iki ince yatay cizgi (y 890 / 905).
* Sayfa turu: 'KONU TESTLERI' sekme metninin koyu piksel kapsami
  (cift sayfa sol x 66-141, tek sayfa sag x 600-675; satir 37-46) --
  208 sayfada 92 test sayfasi; ayni satirda metni olan Mutlak Deger konu
  sayfalari (119-127) x kapsamiyla ayrilir (595 / 145; olculdu).
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak

KOD = "ACL24MG"
KAYNAK_ADI = "2024 ACIL TYT Matematik Geometri Kitap-1"
CIKTI_ONEK = "acil_2024_tyt_matematik_kitap1"
KLASOR = "2024-AC\u0130L TYT Matematik Geometri Kitap-1"
VERAF = "b3"
KART = (589, 43, 1331, 1022)
BEKLENEN_SAYFA = 208
BEKLENEN_TEST = 92
TEST_SAYFALARI = (
    (10, 12),
    (21, 29),
    (33, 37),
    (40, 41),
    (44, 45),
    (49, 54),
    (57, 59),
    (65, 69),
    (78, 82),
    (91, 97),
    (104, 106),
    (111, 118),
    (128, 134),
    (144, 149),
    (162, 168),
    (181, 187),
    (198, 204),
)
ANAHTAR_KAPSAMI = "test"

# --- sayfa turu ---
SEKME = {0: (66, 141), 1: (600, 675)}  # 'KONU TESTLERI' koyu metin x kapsami
SEKME_Y = (37, 46)
SEKME_ARALIK = {0: (40, 300), 1: (440, 720)}


def sayfa_turu(a: np.ndarray, n: int) -> str:
    x0, x1 = SEKME_ARALIK[n % 2]
    k = a[25:65, x0:x1].max(axis=2) < 110
    if k.any():
        ys, xs = np.where(k)
        kapsam = (int(ys.min()) + 25, int(ys.max()) + 25)
        xk = (int(xs.min()) + x0, int(xs.max()) + x0)
        if kapsam == SEKME_Y and xk == SEKME[n % 2]:
            return "test"
    return "konu" if ortak.glifler(sys.modules[__name__], a) else "kapak"


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Sayfa alti tek satir serit: ALT cizgi = y 895-915'te x >= 300 icinde
    280-330 px koyu (max < 190) yatay cizgi (91 sayfada y 905); ust cizgi
    alttan 15-16 px yukarida ama bazen cok soluk (s162: 229 gri) -> ust =
    alt - SERIT_YUKSEKLIK."""
    k = a[:, 300:].max(axis=2) < 190
    ys = [y for y in range(895, 916) if 280 <= int(k[y].sum()) <= 330]
    if not ys:
        return None
    y1 = ys[-1]
    xs = np.where(k[y1])[0] + 300
    return [y1 - SERIT_YUKSEKLIK, y1, int(xs.min()), int(xs.max())]


SERIT_YUKSEKLIK = 16


# --- capa (olculdu: s10, s11, s201, s203) ---
GLIF_GENISLET = True
GLIF_BOY = (12, 17, 12, 17)
SIMGE_X = {1: {"L": 27, "R": 353}, 0: {"L": 43, "R": 369}}
SIMGE_TOLERANS = 16
PENCERE = (-6, 34, 6, 52)
NUMARA_H = (8, 16)
NUMARA_W_EN_COK = 30
NUMARA_DX = (8, 30)
SERIT_SIMGE_PAY = 10
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    """Mavi basili soru numarasi (64,96,160); okuyucu glifi (69,39,160) g < r
    oldugu icin disarida."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m: np.ndarray = (b > 130) & (b - r > 50) & (g > r + 10)
    return m


# --- cevap anahtari ---
ANAHTAR_NEREDEN = (
    "her test sayfasinin altindaki tek satir cevap seridi (1) C | 2) D ...) "
    "+ ayni sayfanin ust bandi (konu adi, 'Test - N')"
)
BANT_Y_ALT = 66
BANT_TARIFI = (
    "Bir kenarda 'KONU TESTLER\u0130' sekmesi, diger kenardaki sekmede iki satir: "
    "ustte KONU ADI (ornek 'Say\u0131 K\u00fcmeleri'), altta 'Test - N'."
)
BANT_KONU_TARIFI = "sekmedeki KONU ADINI ('Test - N' satirinin ustundeki satir)"
GLIF_HARF_ESIK = 150
GLIF_HARF_H = (6, 12)
GLIF_HARF_W_EN_COK = 14

# --- harita (s4-5 'Kitap Plani' sayfasiz; konu adlari test bandindan) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ACL24MG"
ALAN = "MATEMATIK"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "kitap plani (s4-5) sayfa numarasi vermiyor; bolum adlari konu anlatim "
    "sayfalarinin sekmesinden (renk bolumu), konu adlari test bandindan (iki "
    "bagimsiz okuma, fark 0), konu araligi o konunun ilk test sayfasindan (dosya "
    "no) bir sonraki konunun ilk test sayfasina"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "SAYILAR"),
    (2, "RASYONEL SAYI"),
    (3, "B\u0130R\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    (4, "BAS\u0130T E\u015e\u0130TS\u0130ZL\u0130K"),
    (5, "MUTLAK DE\u011eER"),
    (6, "\u00dcSL\u00dc SAYILAR"),
    (7, "K\u00d6KL\u00dc SAYILAR"),
    (8, "\u00c7ARPANLARA AYIRMA"),
    (9, "ORAN-ORANTI"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Say\u0131 K\u00fcmeleri", 10),
    (
        1,
        "Pozitif-Negatif Say\u0131lar / Tek-\u00c7ift Say\u0131lar / Ard\u0131\u015f\u0131k Say\u0131lar",
        21,
    ),
    (1, "Basamak Kavram\u0131", 33),
    (1, "En K\u00fc\u00e7\u00fck ve En B\u00fcy\u00fck De\u011fer Bulma", 40),
    (1, "B\u00f6lme", 44),
    (1, "B\u00f6lme ve B\u00f6l\u00fcnebilme Kurallar\u0131", 49),
    (1, "Fakt\u00f6riyel", 57),
    (1, "Asal Say\u0131lar ve Asal \u00c7arpanlara Ay\u0131rma", 65),
    (1, "EBOB-EKOK", 78),
    (2, "Rasyonel ve Ondal\u0131kl\u0131 Say\u0131lar", 91),
    (3, "Birinci Dereceden Bir ve \u0130ki Bilinmeyenli Denklemler", 104),
    (4, "Birinci Dereceden E\u015fitsizlikler", 111),
    (5, "Mutlak De\u011fer", 128),
    (6, "\u00dcsl\u00fc Say\u0131lar", 144),
    (7, "K\u00f6kl\u00fc Say\u0131lar", 162),
    (8, "\u00c7arpanlara Ay\u0131rma", 181),
    (9, "Oran-Orant\u0131", 198),
)
SON_SAYFA = 204
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim (m3_sutun: test sayfalari x murekkep projeksiyonu) ---
# Orta ayrac: dikey cizgi + 'MOZ AKADEMI' dikey harfleri (cift x 370-386,
# tek 354-368); sag sutun simgesi ayracin USTUNDE (beyazlatilir), numara
# ayracin saginda (cift 392, tek 376).
SUTUNLAR = {0: {"L": (40, 368), "R": (390, 700)}, 1: {"L": (24, 352), "R": (372, 684)}}
UST_BANT = 67
SAYFA_ALTI = 885
SERIT_PAY = 4
BEKLENEN_SORU = 505
DISK_MERKEZ = (10, 8)
BEYAZ_YARICAP = 17
HALKA = (19, 23)
LEKE = None

# --- metin ---
KITAP_BASLIGI = "2024 AC\u0130L TYT Matematik Geometri Kitap-1"
GRUP_SORU = 51
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Bu kitapta soru numarasi KIRMIZI DEGIL, MAVI basilidir ('1.', '2.' ...); "
    "`basili_no` icin sorunun solundaki mavi numarayi oku. Siklar cogu zaman "
    "iki satira dizilidir (A B C ustte, D E altta): harf sirasina gore yaz.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = ("2024-AC\u0130L TYT Matematik Geometri Kitap-1",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_ACIL_2024_TYT_KITAP1_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 10, "konu": 106, "test": 92},
    "harf": {"A": 60, "B": 99, "C": 139, "D": 134, "E": 73},
    "glif_hucre": 431,
    "glif_uyum": 430,
    "goz_teyit": {"T076#3": "B"},
    "glif_disi": [3, 34, 35, 48, 50, 52, 68, 70, 75, 77, 78, 81],
    "metin_parca": 10,
    "farkli_soru": 45,
    "okunamaz": 2,
    "ithal": 498,
    "beta": "495/498",
    "eski_modern": 7,
    "migration_no": 83,
    "onceki": "0082_acl23kc_beta_onay",
}
