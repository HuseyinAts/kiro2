"""Acil 2024 AYT Matematik Kitap-1 (MOZ Akademi duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 224 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya numarasi.

SAYFA DUZENI: acl24mg (2024 ACIL TYT Matematik Kitap-1) ile ayni MOZ Akademi
serisi: konu anlatim sayfalarinda halka icinde numarali ornekler (acik uclu,
kapsam DISI); 'KONU TESTLERI' sekmeli test sayfalari, her test tek sayfa,
sayfa alti cevap seridi, mavi soru numarasi. Kancalar acl24mg'den.
"""

from __future__ import annotations

import sys

import numpy as np

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.kitap_hat.profiller.acl24mg import (  # noqa: F401
    ANAHTAR_KAPSAMI,
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
    NUMARA_DX,
    NUMARA_H,
    NUMARA_W_EN_COK,
    PENCERE,
    SEKME,
    SEKME_ARALIK,
    SEKME_Y,
    SERIT_SIMGE_PAY,
    SIMGE_X,
    numara_maskesi,
)
from scripts.kitap.kitap_hat.profiller.acl24mg import (
    anahtar_bolgesi as _mg_anahtar_bolgesi,
)
from scripts.kitap.kitap_hat.profiller.acl25s1 import _en_uzun_kosu


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """acl24mg seridi; x araligi = alt cizgi satirindaki EN UZUN kesintisiz
    kosu (<= 30 px aralikla birlesen). acl24mg yontemi satirdaki tum koyu
    pikselin min/max'ini aliyordu: s114'te sol sutunun serit hizasindaki sik
    satiri x0'i 300'e cekti, sol sutun alt siniri serit ustune indi ve D/E
    siklari kesildi (kutu alt-sinir-alti kapisi, 28 Eyl 2026)."""
    b = _mg_anahtar_bolgesi(a, n)
    if b is None:
        return None
    k = a[b[1], 300:].max(axis=1) < 190
    x0, x1 = _en_uzun_kosu(k)
    return [b[0], b[1], x0 + 300, x1 + 300]


KOD = "ACL24AM"
KAYNAK_ADI = "Acil 2024 AYT Matematik Kitap-1"
CIKTI_ONEK = "acil_2024_ayt_matematik_kitap1"
KLASOR = "Acil-2024-AYT Matematik Kitap-1"
VERAF = "b7"
BEKLENEN_SAYFA = 224
BEKLENEN_TEST = 67
TEST_SAYFALARI = (
    (29, 35),
    (53, 59),
    (67, 69),
    (88, 97),
    (113, 118),
    (130, 135),
    (161, 165),
    (172, 176),
    (181, 183),
    (190, 192),
    (200, 203),
    (209, 212),
    (218, 221),
)
# s90 sag sutun ust soru: mavi numara okuyucu diskinin ALTINDA (yalniz nokta
# gorunuyor; gozle) -> capa simgeden, basili_no null.
NUMARASIZ_CAPA = ((90, 71, 386),)
# s90 simge x 386 (sag sutun 369'dan 17 px): tolerans 18.
SIMGE_TOLERANS = 18
# s133 sag sutun ust soru: numara simgeden 36 px sagda (NUMARA_DX disi; gozle).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ((133, "R", 91, 375),)


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


ANAHTAR_NEREDEN = (
    "her test sayfasinin altindaki tek satir cevap seridi (1) C | 2) D ...) "
    "+ ayni sayfanin ust bandi (konu adi, 'Test - N')"
)

# --- harita (bolum = konu anlatim sayfasi sekmesi; konu = test bandi; gozle) ---
KOK_KOD = "MAT"
KOD_ONEKI = "MAT-ACL24AM"
ALAN = "MATEMATIK"
SINAV = "AYT"
SINIF = 11
HARITA_NEREDEN = (
    "bolum adlari konu anlatim sayfalarinin sekmesinden (renk bolumu, gozle), konu "
    "adlari test bandindan (iki bagimsiz okuma, fark 0); Trigonometri testleri bantta "
    "'I. BOLUM' .. 'VII. BOLUM'; konu araligi ilk test sayfasindan bir sonrakine"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "POL\u0130NOM"),
    (2, "\u0130K\u0130NC\u0130 DERECEDEN DENKLEM"),
    (3, "KARMA\u015eIK SAYILAR"),
    (4, "PARABOL"),
    (5, "FONKS\u0130YON UYGULAMALARI"),
    (6, "E\u015e\u0130TS\u0130ZL\u0130KLER"),
    (7, "TR\u0130GONOMETR\u0130"),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Polinomlar", 29),
    (2, "\u0130kinci Dereceden Denklemler", 53),
    (3, "Karma\u015f\u0131k Say\u0131lar", 67),
    (4, "Parabol", 88),
    (5, "Fonksiyonlar\u0131n Uygulamalar\u0131", 113),
    (6, "E\u015fitsizlikler", 130),
    (7, "I. B\u00d6L\u00dcM", 161),
    (7, "II. B\u00d6L\u00dcM", 172),
    (7, "III. B\u00d6L\u00dcM", 181),
    (7, "IV. B\u00d6L\u00dcM", 190),
    (7, "V. B\u00d6L\u00dcM", 200),
    (7, "VI. B\u00d6L\u00dcM", 209),
    (7, "VII. B\u00d6L\u00dcM", 218),
)
KONU_AD_DUZELTME = {
    f"{r} B\u00d6L\u00dcM": f"Trigonometri {r} B\u00f6l\u00fcm"
    for r in ("I.", "II.", "III.", "IV.", "V.", "VI.", "VII.")
}
SON_SAYFA = 221
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim: acl24mg ile ayni MOZ duzeni (sutunlar, ust bant, serit
# payi); SAYFA_ALTI bu ciltte olculdu (asagida); kutu / kirp kapilari dogrular ---
from scripts.kitap.kitap_hat.profiller.acl24mg import (  # noqa: E402, F401
    SERIT_PAY,
    SUTUNLAR,
    TALIMAT_EK,
    UST_BANT,
)

# Sol sutun (seritle ortusmez) son sik satiri serit hizasina, hatta altina
# iner: s33 E) y 893-901, s114 D/E y 899-908 (kutu alt-sinir-alti kapisi iki
# kez yakaladi); serit alt cizgisi 905, sayfa cizgisi 920 -> 914.
SAYFA_ALTI = 914
BEKLENEN_SORU = 340
LEKE = None

# --- metin ---
KITAP_BASLIGI = "Acil 2024 AYT Matematik Kitap-1"
GRUP_SORU = 43

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = ("Acil-2024-AYT Matematik Kitap-1",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "MAT_ACIL_2024_AYT_KITAP1_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 10, "konu": 147, "test": 67},
    "harf": {"A": 55, "B": 78, "C": 71, "D": 75, "E": 61},
    "glif_hucre": 329,
    "glif_uyum": 329,
    "goz_teyit": {},
    "glif_disi": [26, 29, 55],
    "metin_parca": 8,
    "farkli_soru": 35,
    "okunamaz": 6,
    "ithal": 340,
    "beta": "334/340",
    "eski_modern": 3,
    "migration_no": 96,
    "onceki": "0095_acl25s2_beta_onay",
}
