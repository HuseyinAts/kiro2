"""2022-2023 ACIL Kati Cisimler (Konu Anlatimli Soru Fasikulu) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 160 PNG; kart (589,43)-(1331,1022).
YAKALAMA BASILI SAYFA 10'DAN BASLIYOR: dosya 1 = basili sayfa 10 (kapak,
kunye, icindekiler ve ilk konu sayfalari yakalamada YOK). Basili sayfa =
dosya + SAYFA_OFSETI. Icindekiler olmadigi icin konu adlari ve araliklari
test ust bandindan (iki bagimsiz okuma) ve konu anlatim sayfalarinin
bantlarindan alindi (HARITA_NEREDEN).

SAYFA DUZENI: acl23ag ile ayni seri (ayni bant, ayni cevap tablosu, ayni
okuyucu simgesi); kancalar oradan alinir. Simge sutunlari sayfa paritesine
gore TERS (dosya numarasi basili sayfadan 9 kayik).
"""

from __future__ import annotations

import numpy as np

from scripts.kitap.kitap_hat.profiller.acl23ag import (  # noqa: F401
    ANAHTAR_KAPSAMI,
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
    SERIT_SIMGE_PAY,
    SIMGE_TOLERANS,
    sayfa_turu,
)

KOD = "ACL23KC"
KAYNAK_ADI = "2022-2023 ACIL Kati Cisimler"
CIKTI_ONEK = "acil_2023_kati_cisimler"
KLASOR = "2022-2023-AC\u0130L-Kat\u0131 Cisimler"
VERAF = "b2"
BEKLENEN_SAYFA = 160
SAYFA_OFSETI = 9
BEKLENEN_TEST = 39
# Kontak sayfasindan gozle; ilk yazimda 54 (Silindir konu) / 87 (Piramit Test-1)
# karistirilmisti -- kapi yakaladi, sayfalar acilip dogrulandi.
TEST_SAYFALARI = ((10, 29), (41, 53), (63, 76), (87, 98), (112, 123), (131, 139))

# --- capa (olculdu: dosya 10-29, a_olc_glif) ---
SIMGE_X = {1: {"L": 32, "R": 363}, 0: {"L": 13, "R": 347}}
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()

BANT_TARIFI = (
    "Bir kenarda kirmizi 'Test - N' (N roma rakami ya da sayi), diger kenarda "
    "koyu lacivert KONU ADI (ornek 'Dik Prizmalar')."
)
BANT_KONU_TARIFI = "banttaki koyu lacivert KONU ADINI"

ANAHTAR_NEREDEN = (
    "her testin son sayfasinin sag altindaki 6 sutunlu cevap tablosu (1. E | 2. A ...) "
    "+ testin ilk sayfasinin ust bandi (konu adi, 'Test - N')"
)


def anahtar_bolgesi(a: np.ndarray, n: int) -> list[int] | None:
    """Cevap tablosu TURUNCU hucre izgarasi (mavi cerceve icinde; s11 olculdu:
    turuncu 240,160,16 / mavi 48,112,176). Izgara cizgisi = y >= 780'de
    >= 60 px kesintisiz turuncu kosu (eksik son satir kisa cizgi)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    tur = (r > 200) & (g > 120) & (g < 200) & (b < 90)
    cizgi = [y for y in range(780, a.shape[0]) if _kosu(tur[y]) >= 60]
    if len(cizgi) < 2:
        return None
    xs = np.where(tur[cizgi[0] : cizgi[-1] + 1].any(axis=0))[0]
    return [cizgi[0], cizgi[-1], int(xs.min()), int(xs.max())]


def _kosu(v: np.ndarray) -> int:
    en = say = 0
    for x in v:
        say = say + 1 if x else 0
        en = max(en, say)
    return en


# --- harita (icindekiler yakalamada YOK) ---
KOK_KOD = "GEO"
KOD_ONEKI = "GEO-ACL23KC"
ALAN = "GEOMETRI"
SINAV = "AYT"
SINIF = 12
HARITA_NEREDEN = (
    "icindekiler yakalamada yok (yakalama basili s10'dan basliyor); konu adlari test "
    "ust bandindan (iki bagimsiz okuma, fark 0), konu araligi o konunun ilk test "
    "sayfasindan (dosya no) bir sonraki konunun ilk test sayfasina"
)
BOLUMLER: tuple[tuple[int, str], ...] = ((1, "KATI C\u0130S\u0130MLER"),)
# (bolum, konu adi -- test bandinda basildigi gibi, ilk test sayfasi DOSYA no)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Dik Prizmalar", 10),
    (1, "K\u00fcp", 41),
    (1, "Silindir", 63),
    (1, "Piramit", 87),
    (1, "Koni", 112),
    (1, "K\u00fcre", 131),
)
SON_SAYFA = 139
BANT_ESLER: dict[str, str] = {}

# --- kutu / kirpim: acl23ag ile ayni duzen, parite TERS ---
SUTUNLAR = {0: {"L": (36, 352), "R": (369, 700)}, 1: {"L": (52, 369), "R": (386, 716)}}
# Kart icerigi acl23ag'ye gore ~7 px asagida: kirmizi yatay cizgiler y 34 / 83
# / 917 (dosya 10, 11, 63, 64, 131 olculdu).
UST_BANT = 86
SAYFA_ALTI = 908
# Turuncu izgaranin ~13 px ustunde mavi cerceve (s11 olculdu; ilk kirpimda
# T016_12'nin altina girdi, gozle yakalandi).
SERIT_PAY = 18
BEKLENEN_SORU = 339
LEKE = None

# --- metin ---
KITAP_BASLIGI = "2022-2023 AC\u0130L Kat\u0131 Cisimler"
GRUP_SORU = 33
TALIMAT_EK = ""

# --- mukerrer / ithal ---
DERSLER = ("MATEMATIK", "GEOMETRI")
ESKI_KAYNAKLAR: tuple[str, ...] = ()  # DB'de eski hat yok (olculdu)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "ACIL Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "GEO_ACIL_2023_KATI_CISIMLER_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 10, "konu": 70, "test": 80},
    "harf": {"A": 22, "B": 62, "C": 80, "D": 102, "E": 73},
    "glif_hucre": 160,
    "glif_uyum": 150,
    "goz_teyit": {
        "T016#3": "D",
        "T016#4": "E",
        "T016#5": "D",
        "T016#7": "C",
        "T016#9": "B",
        "T016#10": "D",
        "T016#11": "E",
        "T026#1": "D",
        "T039#5": "C",
        "T039#6": "E",
    },
    "glif_disi": [
        3,
        8,
        10,
        11,
        12,
        14,
        15,
        17,
        18,
        20,
        21,
        22,
        23,
        25,
        27,
        30,
        34,
        35,
        36,
        37,
        38,
    ],
    "metin_parca": 10,
    "farkli_soru": 35,
    "okunamaz": 14,
    "ithal": 338,
    "beta": "324/338",
    "eski_modern": 0,
    "migration_no": 80,
    "onceki": "0079_acl23ag_beta_onay",
}
