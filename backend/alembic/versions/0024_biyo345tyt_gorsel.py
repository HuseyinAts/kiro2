"""345 TYT Biyoloji sekilli sorulara gorsel baglar ve 333'unu aktiflestirir

Revision ID: 0024_biyo345tyt_gorsel
Revises: 0023_345_beta_onay
Create Date: 2026-09-15

BAGLAM
------
0023, bu kitabin 334 sorusunu BILEREK disarida biraktu: `bayraklar` icinde
`gorsel_yok_sekilli` tasiyorlardi. Gerekce YONTEM belgesinde yaziliydi --
kitabin gorsel hatti sayfa ve SUTUN kirpimi uretmisti, soru kutusu
uretmemisti; `question_image_url` NULL idi ve sekil iceren sorular metin
olarak EKSIKti, ogrenciye sekli olmadan gosterilirse cozulemezdi.

YENI BIR KUTU TURU KOSULMADI -- VAR OLAN SET OLCULDU
----------------------------------------------------
Kutu tespit turuna baslamadan once disk olculdu ve bu kitabin ESKI bir kutu
kirpim setinin zaten durdugu gorulda: 1050 kutu, her biri bbox ve guven
skoruyla, `d-dataset/output/crops/` altinda. Yeni hat bunu kullanmamisti.

Sete korukorune guvenilmedi: geo345'te tam bu sinifta bir kutu seti (F2c)
cevap anahtariyla kiyaslaninca BOZUK cikmisti. Bu yuzden kullanilmadan once
dort ayri olcum yapildi.

1. KALITE (backend/_geo_gecici/btyt_kutu_kalite.py)
   medyan guven 0.899, ortalama 0.890; 0.7 altinda yalnizca 18 kutu (%1.7).
   Bozuk bbox 0. %30'dan fazla ortusen kutu cifti yalnizca 2. Genislikler
   316-321 araliginda siki kumelenmis (sutun genisligi).

2. SIFIR SERBESTLIK DERECELI HIZALAMA (btyt_hizalama.py)
   IKI BAGIMSIZ KANAL kiyaslandi:
     A) ESKI kutu dedektorunun bbox x merkezi -> sol/sag
     B) YENI sayfa+sutun hattinin `sutun_gorseli` alani -> _sol/_sag
   Kanallar birbirini HIC GORMEDI. 219 sayfanin 215'inde sayfa basina
   sol/sag adetleri BIREBIR tuttu (%98.17).

   Ek olarak D1: her sayfada SOL sutundaki soru_no'lar SAG'dakilerden
   kucuk mu? 219/219 sayfada evet, SIFIR ihlal -- okuma sirasi kurali
   (once sol sutun yukaridan asagi, sonra sag) boylece dogrulandi.

3. ANTI-CAPA BASILI NUMARA DOGRULAMASI (btyt_no_seridi.py, btyt_no_kiyas.py)
   333 sekilli sorudan 80'i rastgele secildi; her kirpimin sol ust kosesi
   (basili soru numarasinin durdugu yer) montajlandi. Montajda YALNIZCA
   INDEKS yaziyordu; beklenen `soru_no` okuyucudan gizlenip ayri bir JSON'da
   tutuldu. Okuma bittikten SONRA programatik kiyaslandi:

       80/80 BIREBIR, SIFIR SAPMA.

   (77'si ilk turda okundu; 3'u OSYM kosesi cercevesi numarayi seridin
   disina ittigi icin tam kirpimdan tek tek okundu, ucu de uydu.)

   Kirpimlarin ICERIGINE de bakildi: hepsi TAM SORU -- numara, kok, sekil
   ve bes sikkin tamami.

4. FARKLARIN TAMAMI HESABA KATILDI (btyt_kayip_soru.py)
   Diskte 1050 kutu, DB'de 1023 soru var. 28 fazla + 1 eksik su sekilde
   TAMAMEN acikland:
     - 25 kutu, DB'de HIC OLMAYAN sayfalarda (viewer'in cift cektigi
       196/197/198 ve 234/235, bolum kapaklari, on sayfalar). Yeni hat
       bunlari dogru sekilde disarida birakmis.
     -  2 kutu SAHTE: s92 q04 (asiri buyuk, 5. ve 6. soruyu birlikte
        yutuyor, g=0.426) ve s221 q04 (BOMBOS kutu, g=0.344). Ikisine de
        tek tek BAKILDI.
     -  1 kutu s148 q02: basili no4. O soru bu kitaba degil, zaten aktif
        olan `OSYM 2025 TYT` s41 satirina ait -- YONTEM'in belgeledigi
        dedup. Kutu hakli, DB hakli.
     -  1 EKSIK: s16'da dedektor `sag` sorusunu KACIRMIS.
   Aciklanamayan fark: SIFIR.

NE YAPILIYOR
------------
1. 1022 satira `question_image_url` yazilir. Bunlarin 333'u sekilli
   sorulardir; kalan 689'u zaten aktif olan sorulardir ve gorseli olmak
   onlari da iyilestirir (sema genelinde diger kitaplarin hepsinde bu alan
   dolu). Esleme AYNI dogrulanmis kuraldan gelir.
2. Gorsel kavusan 333 sekilli soru, 0023'un actigi satirlarla AYNI
   muameleyi gorur: quality_review_status, review_status, is_active ve
   ayni metadata anahtarlari.
3. Artik dogru olmayan iki alan duzeltilir:
     bayraklar icinden `gorsel_yok_sekilli` CIKARILIR (artik gorsel var)
     `gorsel_kaynagi` -> 'kutu_kirpimi_dogrulanmis_eski_hat'

DISARIDA KALAN TEK SORU
-----------------------
s16 sag no3 (sekilli). Dedektor o kutuyu kacirmis; kirpimi YOK. Satir
PASIF kalir ve `gorsel_yok_sekilli` bayragini KORUR -- yani bu migration
sonrasi o bayragi tasiyan tam olarak 1 satir kalir. Uydurma bir gorsel
baglanmadi.

SINYAL LISTESI DEGISMIYOR
-------------------------
Bu 333 satir 0023'teki kardeslerinin `konsensus_sinyalleri` listesini alir
(konu_bandi_sifir_serbestlik, dogrulayici_k1_k11_sifir_kusur,
manifest_soru_sayisi_ortusmesi). Ustteki kutu dogrulamasi GORSEL eslemesini
dogrular, transkripsiyonu ya da cevabi degil; bu yuzden sinyal listesine
yeni bir madde EKLENMEDI. Cevaplar yine dogrulanmadi; tek kaynak kitabin
basili anahtaridir.

GERI ALINABILIR
---------------
Her satirin onceki question_image_url, is_active, review_status,
quality_review_status degerleri GUNLUK'e yazilir; downgrade tam olarak
onlari geri koyar, eklenen metadata anahtarlarini siler, `bayraklar`a
`gorsel_yok_sekilli`i geri ekler ve `gorsel_kaynagi`ni eski degerine
dondurur.
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0024_biyo345tyt_gorsel"
down_revision: Union[str, None] = "0023_345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "biyo345tyt_gorsel_gunlugu_0024"
KAYNAK = "345 2025 TYT Biyoloji Soru Bankasi"
# Kirpim klasoru; ASCII kalsin diye kacis dizisiyle yazildi (i without dot).
KLASOR = "345_2025_Tyt_Biyoloji_Soru_Bankas\u0131"
ESKI_GORSEL_KAYNAGI = "yok_soru_kirpimi_uretilmedi"
YENI_GORSEL_KAYNAGI = "kutu_kirpimi_dogrulanmis_eski_hat"

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)
SINYALLER = (
    "konu_bandi_sifir_serbestlik",
    "dogrulayici_k1_k11_sifir_kusur",
    "manifest_soru_sayisi_ortusmesi",
)

# sayfa -> {"<sutun><soru_no>": "<kirpim q indeksi>"}
# Uretim: backend/_geo_gecici/btyt_esleme_son.py (kural + elle bakilan 4 sayfa)
HARITA: dict[int, dict[str, str]] = {
    6: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    7: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    8: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "05",
        "sol1": "01",
        "sol2": "03",
        "sol3": "06",
    },
    9: {"sag10": "03", "sag11": "04", "sag9": "01", "sol7": "02", "sol8": "05"},
    10: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    11: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    12: {"sag3": "02", "sol1": "01", "sol2": "03"},
    13: {"sag6": "01", "sag7": "03", "sag8": "04", "sol4": "02", "sol5": "05"},
    14: {"sag4": "02", "sag5": "05", "sol1": "01", "sol2": "03", "sol3": "04"},
    15: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    16: {"sol1": "01", "sol2": "02"},
    18: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "05",
        "sol1": "01",
        "sol2": "03",
        "sol3": "06",
    },
    19: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    20: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    21: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    22: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    23: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    24: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    25: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    26: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    27: {
        "sag10": "02",
        "sag11": "03",
        "sag12": "06",
        "sol7": "01",
        "sol8": "04",
        "sol9": "05",
    },
    28: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    29: {
        "sag10": "02",
        "sag11": "03",
        "sag12": "06",
        "sol7": "01",
        "sol8": "04",
        "sol9": "05",
    },
    30: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    31: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    32: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    33: {
        "sag10": "03",
        "sag11": "06",
        "sag9": "02",
        "sol6": "01",
        "sol7": "04",
        "sol8": "05",
    },
    34: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    35: {"sag10": "04", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "05"},
    36: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "06",
        "sol1": "01",
        "sol2": "04",
        "sol3": "05",
    },
    37: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    38: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    39: {"sag7": "02", "sag8": "03", "sag9": "05", "sol5": "01", "sol6": "04"},
    40: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    41: {"sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    42: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    43: {"sag10": "05", "sag8": "01", "sag9": "03", "sol6": "02", "sol7": "04"},
    44: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    45: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    46: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    47: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    48: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    49: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    50: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    51: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    52: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    53: {"sag10": "05", "sag8": "01", "sag9": "03", "sol6": "02", "sol7": "04"},
    54: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    55: {"sag8": "02", "sol5": "01", "sol6": "03", "sol7": "04"},
    56: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    57: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    58: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    59: {"sag7": "02", "sag8": "03", "sag9": "04", "sol5": "01", "sol6": "05"},
    60: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    61: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    62: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    63: {
        "sag10": "02",
        "sag11": "03",
        "sag12": "05",
        "sol7": "01",
        "sol8": "04",
        "sol9": "06",
    },
    64: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    65: {"sag10": "04", "sag9": "02", "sol7": "01", "sol8": "03"},
    66: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    67: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    68: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "06",
        "sol1": "01",
        "sol2": "04",
        "sol3": "05",
    },
    70: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    71: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    72: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    73: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    74: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    75: {
        "sag10": "03",
        "sag11": "06",
        "sag9": "01",
        "sol6": "02",
        "sol7": "04",
        "sol8": "05",
    },
    76: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    77: {"sag10": "04", "sag8": "01", "sag9": "03", "sol6": "02", "sol7": "05"},
    78: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    79: {
        "sag10": "04",
        "sag11": "06",
        "sag9": "02",
        "sol6": "01",
        "sol7": "03",
        "sol8": "05",
    },
    80: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    81: {
        "sag10": "05",
        "sag8": "01",
        "sag9": "03",
        "sol5": "02",
        "sol6": "04",
        "sol7": "06",
    },
    82: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    83: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    84: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    85: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    86: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    87: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    88: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "06",
        "sol1": "01",
        "sol2": "04",
        "sol3": "05",
    },
    89: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    90: {"sag3": "02", "sag4": "04", "sag5": "05", "sol1": "01", "sol2": "03"},
    91: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    92: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "06",
        "sol1": "01",
        "sol2": "05",
        "sol3": "07",
    },
    93: {
        "sag10": "02",
        "sag11": "04",
        "sag12": "06",
        "sol7": "01",
        "sol8": "03",
        "sol9": "05",
    },
    94: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    95: {"sag10": "04", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "05"},
    96: {"sag4": "02", "sag5": "05", "sol1": "01", "sol2": "03", "sol3": "04"},
    97: {"sag8": "02", "sol6": "01", "sol7": "03"},
    98: {"sag4": "02", "sag5": "05", "sol1": "01", "sol2": "03", "sol3": "04"},
    99: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    100: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    101: {"sag8": "02", "sag9": "04", "sol5": "01", "sol6": "03", "sol7": "05"},
    102: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    103: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    104: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    105: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    106: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    108: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    109: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    110: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    111: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    112: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    113: {
        "sag10": "04",
        "sag11": "05",
        "sag9": "02",
        "sol6": "01",
        "sol7": "03",
        "sol8": "06",
    },
    114: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    115: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    116: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    117: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    118: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    119: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    120: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    121: {"sag4": "02", "sag5": "05", "sol1": "01", "sol2": "03", "sol3": "04"},
    122: {"sag4": "02", "sag5": "05", "sol1": "01", "sol2": "03", "sol3": "04"},
    123: {"sag8": "01", "sag9": "03", "sol6": "02", "sol7": "04"},
    124: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    125: {"sag10": "02", "sag11": "04", "sol7": "01", "sol8": "03", "sol9": "05"},
    126: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    127: {
        "sag10": "04",
        "sag11": "06",
        "sag9": "02",
        "sol6": "01",
        "sol7": "03",
        "sol8": "05",
    },
    128: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    129: {"sag10": "05", "sag8": "01", "sag9": "03", "sol6": "02", "sol7": "04"},
    130: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    131: {"sag10": "04", "sag9": "02", "sol7": "01", "sol8": "03"},
    132: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    133: {"sag8": "01", "sag9": "04", "sol6": "02", "sol7": "03"},
    134: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    135: {"sag8": "02", "sag9": "04", "sol6": "01", "sol7": "03"},
    136: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    137: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    138: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    139: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    140: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    142: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    143: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    144: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    145: {"sag8": "01", "sag9": "04", "sol5": "02", "sol6": "03", "sol7": "05"},
    146: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    147: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    148: {"sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    149: {"sag10": "05", "sag8": "01", "sag9": "03", "sol6": "02", "sol7": "04"},
    150: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    151: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    152: {"sag4": "01", "sag5": "04", "sol1": "02", "sol2": "03", "sol3": "05"},
    153: {"sag10": "04", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "05"},
    154: {"sag4": "01", "sag5": "04", "sol1": "02", "sol2": "03", "sol3": "05"},
    155: {"sag10": "04", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "05"},
    156: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    157: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    158: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    159: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    160: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    161: {"sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    162: {"sag3": "01", "sag4": "03", "sag5": "04", "sol1": "02", "sol2": "05"},
    163: {"sag10": "04", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "05"},
    164: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    165: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    166: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    167: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    168: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    169: {"sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    170: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    171: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    172: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    174: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "05",
        "sol1": "01",
        "sol2": "03",
        "sol3": "06",
    },
    175: {
        "sag4": "01",
        "sag5": "03",
        "sag6": "05",
        "sol1": "02",
        "sol2": "04",
        "sol3": "06",
    },
    176: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    177: {
        "sag10": "01",
        "sag11": "04",
        "sag12": "06",
        "sol7": "02",
        "sol8": "03",
        "sol9": "05",
    },
    178: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    179: {"sag10": "05", "sag8": "02", "sag9": "03", "sol6": "01", "sol7": "04"},
    180: {"sag3": "02", "sag4": "03", "sag5": "04", "sol1": "01", "sol2": "05"},
    181: {"sag8": "02", "sol6": "01", "sol7": "03"},
    182: {
        "sag4": "02",
        "sag5": "03",
        "sag6": "05",
        "sol1": "01",
        "sol2": "04",
        "sol3": "06",
    },
    183: {"sag10": "02", "sag11": "04", "sol7": "01", "sol8": "03", "sol9": "05"},
    184: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    185: {"sag8": "01", "sag9": "04", "sol6": "02", "sol7": "03"},
    186: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    187: {"sag6": "02", "sag7": "03", "sol5": "01"},
    188: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    189: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    190: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    191: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    192: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    193: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    194: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    195: {"sag7": "01", "sag8": "03", "sol5": "02", "sol6": "04"},
    199: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    200: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    201: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    202: {"sag7": "01", "sag8": "03", "sol5": "02", "sol6": "04"},
    203: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    204: {"sag8": "02", "sag9": "04", "sol5": "01", "sol6": "03", "sol7": "05"},
    205: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    206: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    207: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    208: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    209: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    210: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    211: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    213: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    214: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    215: {"sag4": "02", "sag5": "04", "sol1": "01", "sol2": "03", "sol3": "05"},
    216: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    217: {
        "sag4": "02",
        "sag5": "04",
        "sag6": "06",
        "sol1": "01",
        "sol2": "03",
        "sol3": "05",
    },
    218: {"sag10": "04", "sag9": "01", "sol7": "02", "sol8": "03"},
    219: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    220: {"sag8": "02", "sag9": "04", "sol5": "01", "sol6": "03", "sol7": "05"},
    221: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "05"},
    222: {"sag7": "02", "sag8": "03", "sag9": "05", "sol5": "01", "sol6": "04"},
    223: {"sag3": "02", "sag4": "03", "sag5": "05", "sol1": "01", "sol2": "04"},
    224: {"sag10": "05", "sag9": "02", "sol6": "01", "sol7": "03", "sol8": "04"},
    225: {"sag3": "02", "sag4": "04", "sag5": "05", "sol1": "01", "sol2": "03"},
    226: {"sag8": "01", "sag9": "04", "sol6": "02", "sol7": "03"},
    227: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    228: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    229: {"sag3": "02", "sag4": "03", "sol1": "01", "sol2": "04"},
    230: {"sag7": "02", "sag8": "03", "sol5": "01", "sol6": "04"},
    231: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
    232: {"sag7": "02", "sag8": "04", "sol5": "01", "sol6": "03"},
    233: {"sag3": "02", "sag4": "04", "sol1": "01", "sol2": "03"},
}


def _tablolar_var(b) -> bool:
    d = sa.inspect(b)
    return all(
        d.has_table(t)
        for t in (
            "question_bank",
            "question_content",
            "question_metadata",
            "question_statistics",
        )
    )


def _url(sayfa: int, q: str) -> str:
    return f"/static/crops/{KLASOR}/{KLASOR}_p{sayfa:04d}_q{q}.png"


def _hedefler(b):
    """(id, sayfa, sutun, soru_no, sekilli, eski_url, ...) listesi dondurur."""
    return b.execute(
        sa.text(
            "SELECT qb.id, qm.source_page, qm.pipeline_metadata::jsonb, "
            "       qc.question_image_url, qb.is_active, qb.review_status, "
            "       qs.quality_review_status "
            "  FROM question_bank qb "
            "  JOIN question_metadata qm ON qm.id = qb.id "
            "  JOIN question_content qc ON qc.id = qb.id "
            "  LEFT JOIN question_statistics qs ON qs.id = qb.id "
            " WHERE qm.source_book = :kaynak"
        ),
        {"kaynak": KAYNAK},
    ).fetchall()


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0024] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


_SAYAC_SQL = """
UPDATE topic_hierarchy t
   SET total_questions = COALESCE(g.adet, 0), updated_at = now()
  FROM (SELECT th.id, count(qb.id) AS adet
          FROM topic_hierarchy th
          LEFT JOIN question_bank qb
                 ON qb.primary_topic_id = th.id AND qb.is_active IS TRUE
         GROUP BY th.id) g
 WHERE g.id = t.id
   AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
"""


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0024] soru tablolari yok (taze DB?) -- atlandi")
        return
    satirlar = _hedefler(b)
    if not satirlar:
        _log.info("[0024] %s satiri yok -- atlandi (veri ithal edilmemis)", KAYNAK)
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_url", sa.String(), nullable=True),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.Column("aktiflestirildi", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    gorsel, aktif, kirpimsiz = [], [], []
    for sid, sayfa, pm, eski_url, akt, rs, qrs in satirlar:
        anahtar = f"{(pm or {}).get('sutun')}{(pm or {}).get('soru_no')}"
        q = HARITA.get(sayfa, {}).get(anahtar)
        sekilli = "gorsel_yok_sekilli" in ((pm or {}).get("bayraklar") or [])
        if q is None:
            if sekilli:
                kirpimsiz.append(sid)
            continue
        gorsel.append({"id": sid, "url": _url(sayfa, q)})
        if sekilli:
            aktif.append(sid)
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, onceki_url, onceki_is_active,"  # noqa: S608  # nosec B608
                " onceki_review_status, onceki_quality_review_status,"
                " aktiflestirildi) VALUES (:id, :u, :a, :r, :q, :f)"
            ),
            {"id": sid, "u": eski_url, "a": akt, "r": rs, "q": qrs, "f": sekilli},
        )

    b.execute(
        sa.text("UPDATE question_content SET question_image_url = :url WHERE id = :id"),
        gorsel,
    )
    _log.info("[0024] question_image_url yazildi: %s satir", len(gorsel))

    # gorsel_kaynagi artik GORSELI OLAN HER satirda dogru olmali -- yalnizca
    # aktiflestirilenlerde degil. Aksi halde 689 satir gorseli oldugu halde
    # "kirpim uretilmedi" demeye devam ederdi.
    tum_id = [g["id"] for g in gorsel]
    b.execute(
        sa.text(
            "UPDATE question_metadata SET pipeline_metadata = ("
            "  pipeline_metadata::jsonb"
            "  || jsonb_build_object('gorsel_kaynagi',"
            "       CAST(:yeni_kaynak AS text))"
            ")::json WHERE id = ANY(:idler)"
        ),
        {"idler": tum_id, "yeni_kaynak": YENI_GORSEL_KAYNAGI},
    )

    if aktif:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = TRUE,"
                " review_status = 'APPROVED', updated_at = now()"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": aktif},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics"
                " SET quality_review_status = 'auto_judged_high'"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": aktif},
        )
        b.execute(
            sa.text(
                "UPDATE question_metadata SET pipeline_metadata = ("
                "  (pipeline_metadata::jsonb"
                "   || jsonb_build_object("
                "        'consensus_2signal_run', true,"
                "        'konsensus_sinyalleri', CAST(:sinyaller AS jsonb),"
                "        'onay_turu', 'toplu_beta_sahibi',"
                "        'bireysel_denetim_yapildi', false))"
                "  || jsonb_build_object('bayraklar',"
                "       (pipeline_metadata::jsonb -> 'bayraklar')"
                "       - 'gorsel_yok_sekilli')"
                ")::json WHERE id = ANY(:idler)"
            ),
            {
                "idler": aktif,
                "sinyaller": json.dumps(list(SINYALLER)),
                "yeni_kaynak": YENI_GORSEL_KAYNAGI,
            },
        )
        _log.info("[0024] aktiflestirilen sekilli soru: %s", len(aktif))
    _log.info("[0024] kirpimi olmadigi icin PASIF kalan: %s", len(kirpimsiz))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0024] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            "SELECT id, onceki_url, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608
            f" onceki_quality_review_status, aktiflestirildi FROM {GUNLUK}"
        )
    ).fetchall()

    for sid, u, akt, rs, qrs, aktiflestirildi in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_content SET question_image_url = :u WHERE id = :id"
            ),
            {"id": sid, "u": u},
        )
        if not aktiflestirildi:
            continue
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :a, review_status = :r,"
                " updated_at = now() WHERE id = :id"
            ),
            {"id": sid, "a": akt, "r": rs},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = :q"
                " WHERE id = :id"
            ),
            {"id": sid, "q": qrs},
        )

    # gorsel_kaynagi gorseli verilen HER satirda degistirilmisti -- hepsinde
    # geri alinir.
    tum_id = [r[0] for r in kayitlar]
    if tum_id:
        b.execute(
            sa.text(
                "UPDATE question_metadata SET pipeline_metadata = ("
                "  pipeline_metadata::jsonb"
                "  || jsonb_build_object('gorsel_kaynagi',"
                "       CAST(:eski_kaynak AS text))"
                ")::json WHERE id = ANY(:idler)"
            ),
            {"idler": tum_id, "eski_kaynak": ESKI_GORSEL_KAYNAGI},
        )

    geri = [r[0] for r in kayitlar if r[5]]
    if geri:
        for anahtar in EK_ANAHTARLAR:
            b.execute(
                sa.text(
                    "UPDATE question_metadata SET pipeline_metadata ="
                    " (pipeline_metadata::jsonb - :a)::json WHERE id = ANY(:idler)"
                ),
                {"a": anahtar, "idler": geri},
            )
        b.execute(
            sa.text(
                "UPDATE question_metadata SET pipeline_metadata = ("
                "  pipeline_metadata::jsonb"
                "  || jsonb_build_object('bayraklar',"
                "       (pipeline_metadata::jsonb -> 'bayraklar')"
                "       || '[\"gorsel_yok_sekilli\"]'::jsonb)"
                ")::json WHERE id = ANY(:idler)"
            ),
            {"idler": geri},
        )

    _log.info("[0024] geri alindi: %s satir", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
