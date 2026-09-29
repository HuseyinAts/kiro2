"""2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi (Apotemi 'unite testi' duzeni) -- profil.

KAYNAK: FERNUS 1920x1080 ekran goruntusu, 352 PNG; kart (589,43)-(1331,1022).
Basili sayfa = dosya - 1 (icindekiler s7-9: 'Kimya Nedir?' 11 = dosya 12).
Kesif: kitap_hat/kesif.py (_kesif_apo19km); duzen APO19FZ ile ayni seri.

SAYFA DUZENI (olculdu; 29 Eyl 2026):
* Dosya 12-349 test sayfalari (1-11 kapak / on soz / icindekiler / cozumler,
  350-352 arka kapak); bolum acilis sayfasi YOK.
* 19 unite; ust bantta mavi seritte beyaz BUYUK HARFLE UNITE adi (konu adi
  DEGIL) ve 'TEST - N' (N her unitede 1'den baslar); sagda/solda yesil
  'UNITE N' sekmesi.
* Cevap seridi testin son sayfasinin altliginda: soluk sari kutularda gri
  '1-B 2-D ...' (APO19FZ ile ayni kutu maskesi).
* Okuyucu simgesi (mor buyutec) numaranin solunda ayni satirda L 74 / R 363;
  numara SIYAH kalin (kesif: siyah 1840 / mavi 188 / kirmizi 4 isabet).
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
from scripts.kitap.kitap_hat.profiller.apo19fz import (  # noqa: F401
    ANAHTAR_DISLA_X,
    GLIF_HARF_ESIK,
    GLIF_HARF_H,
    GLIF_HARF_W_EN_COK,
    HUCRE_BOSLUK,
    SERIT_HUCRE_TARIFI,
    SERIT_Y,
    anahtar_bolgesi,
    harf_bloblari,
)

KOD = "APO19KM"
KAYNAK_ADI = "2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi"
CIKTI_ONEK = "apotemi_2019_tyt_ayt_kimya"
KLASOR = "Apotemi Tyt Ayt Kimya 2019-2020"
VERAF = "c6"
BEKLENEN_SAYFA = 352
BEKLENEN_TEST = 169
ANAHTAR_KAPSAMI = "test"
TEST_SINIRI = "anahtar"
TEST_SAYFALARI = ((12, 349),)
_TEST = frozenset(n for a, b in TEST_SAYFALARI for n in range(a, b + 1))


def sayfa_turu(a: np.ndarray, n: int) -> str:
    if n in _TEST:
        return "test"
    return "kapak"


# Seritte yanlis basilmis hucre numarasi (gozle, serit_122 2x): test 122'nin
# 10. hucresi '9-E' (9. hucre '9-D'); sira numarasi 10.
ANAHTAR_NUMARA_BASKI: dict[tuple[int, int], int] = {(122, 10): 9}
ANAHTAR_NEREDEN = (
    "her testin son sayfasinin altligindaki serit: soluk sari kutularda 'numara-harf'"
)

BANT_Y_ALT = 100
BANT_TARIFI = (
    "Ust bantta mavi seritte beyaz BUYUK HARFLE unite adi ve ayri kutuda "
    "'TEST - N' yazar; kenarda yesil 'UNITE N' sekmesi vardir."
)
BANT_KONU_TARIFI = "mavi seritteki BUYUK HARFLI unite adini"
BANT_TEST_NO_TARIFI = "'TEST - N' yazisindaki N sayisini"
# Bant konu degil UNITE adi tasir: konu icindekiler sayfa araligindan; bant
# adi bolum (unite) adiyla kapidan gecer (BANT_BOLUM_KAPISI).
BANT_KONU_KAPISI = False
BANT_BOLUM_KAPISI = True

# --- capa ---
SIMGE_X = {0: {"L": 74, "R": 363}, 1: {"L": 74, "R": 363}}
SIMGE_TOLERANS = 14
PENCERE = (-10, 37, 15, 52)
NUMARA_H = (7, 13)
NUMARA_W_EN_COK = 30
NUMARA_DX = (13, 40)
NUMARASIZ_CAPA: tuple[tuple[int, int, int], ...] = ()
# Capa numaradan (gozle; c6_num_olc.py): s122 L '4.' okuyucu simgesi konmamis
# (numara ust y 733, x 99; anahtar 13 hucre, capa 12).
EK_CAPA: tuple[tuple[int, str, int, int], ...] = ((122, "L", 732, 99),)
# Test 121 (dosya 252-253, 15. unite Test 5): anahtarda 11 hucre, sayfada 8. soru
# BASILMAMIS (s253 sol sutun '7.' -> '9.', arada bos alan; gozle).
YAKALANMAYAN_SORU: dict[int, tuple[int, ...]] = {121: (8,)}
KUTU_UST: dict[tuple[int, str, int], int] = {}
KUTU_UST_KESIN: dict[tuple[int, str, int], int] = {}
KESIK_GOZ_ONAY: tuple[str, ...] = ()
# s219 L 7. soru: III. grafigin 'TK' eksen yazisi x 360'ta biter, sutun siniri
# 361 (sekme 361'den); kirpim gozle tam (c6_zoom.py 219, 4x).
KENAR_GOZ_ONAY: tuple[str, ...] = ("APO19KM-T104_07",)
ORTAK_ONCUL_YOK: tuple[str, ...] = ()


def numara_maskesi(a: np.ndarray) -> np.ndarray:
    m: np.ndarray = ortak.NUMARA_MASKELERI["siyah"](a)
    return m


# --- harita (icindekiler s7-9; dosya = basili + 1) ---
KOK_KOD = "KIM"
KOD_ONEKI = "KIM-APO19KM"
ALAN = "KIMYA"
SINAV = "TYT"
SINIF = 9
HARITA_NEREDEN = (
    "icindekiler (s7-9): 19 unite, 116 konu basligi (sayfa no basili, dosya = "
    "basili + 1; 10. unitede baslangic test iceriginden); konu icindekiler sayfa araligindan, test bandindaki unite adi "
    "bolum adiyla kapidan gecer"
)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "1. \u00dcN\u0130TE K\u0130MYA B\u0130L\u0130M\u0130"),
    (2, "2. \u00dcN\u0130TE ATOM VE YAPISI"),
    (3, "3. \u00dcN\u0130TE PER\u0130YOD\u0130K S\u0130STEM"),
    (
        4,
        "4. \u00dcN\u0130TE K\u0130MYASAL T\u00dcRLER ARASI ETK\u0130LE\u015e\u0130MLER",
    ),
    (5, "5. \u00dcN\u0130TE B\u0130LE\u015e\u0130KLER"),
    (6, "6. \u00dcN\u0130TE K\u0130MYASAL TEPK\u0130MELER"),
    (7, "7. \u00dcN\u0130TE DO\u011eA VE K\u0130MYA"),
    (8, "8. \u00dcN\u0130TE K\u0130MYA HER YERDE"),
    (
        9,
        "9. \u00dcN\u0130TE K\u0130MYANIN TEMEL KANUNLARI VE K\u0130MYASAL HESAPLAMALAR",
    ),
    (10, "10. \u00dcN\u0130TE MADDEN\u0130N HALLER\u0130"),
    (11, "11. \u00dcN\u0130TE KARI\u015eIMLAR"),
    (12, "12. \u00dcN\u0130TE K\u0130MYASAL TEPK\u0130MELERDE ENERJ\u0130"),
    (13, "13. \u00dcN\u0130TE TEPK\u0130MELERDE HIZ"),
    (14, "14. \u00dcN\u0130TE TEPK\u0130MELERDE DENGE"),
    (
        15,
        "15. \u00dcN\u0130TE SULU \u00c7\u00d6ZELT\u0130LERDE AS\u0130T \u2013 BAZ DENGES\u0130 / \u00c7\u00d6Z\u00dcNME-\u00c7\u00d6KELME DENGELER\u0130",
    ),
    (16, "16. \u00dcN\u0130TE K\u0130MYA VE ELEKTR\u0130K"),
    (17, "17. \u00dcN\u0130TE KARBON K\u0130MYASINA G\u0130R\u0130\u015e"),
    (18, "18. \u00dcN\u0130TE ORGAN\u0130K B\u0130LE\u015e\u0130KLER"),
    (
        19,
        "19. \u00dcN\u0130TE ENERJ\u0130 KAYNAKLARI VE B\u0130L\u0130MSEL GEL\u0130\u015eMELER",
    ),
)
# (unite, icindekiler adi, BASILI baslangic, sinav, sinif). Sinav / sinif kitapta
# basili DEGIL: MEB 2018 kimya programi unite sinifi (9-10 TYT, 11-12 AYT).
# 10. unite: icindekiler sayfa numaralari 4 sayfa kaymis ('10. UNITE 155',
# 'MADDENIN HALLERI 157' satirlari da sayfa no tasir; 'Sivilar 168' cift).
# Baslangiclar test iceriginden gozle (29 Eyl 2026; c6_bak.py 156-178): Test 1
# (155) gaz ozellikleri, 3 (159) ideal gaz, 4 (161) kismi basinc, 5 (163)
# difuzyon / kinetik / gercek gaz, 6 (165) viskozite / yuzey gerilimi, 7 (167)
# buhar basinci / nem, 8 (169) katilar, 9 (171) hal degisimi, 10 (173) plazma
# (icindekilerde yok -> Hal Degisimleri araligi), 11-12 (175-178) karma.
_KONULAR: tuple[tuple[int, str, int, str, int], ...] = (
    (1, "Kimya Nedir?, Kimya Ne \u0130\u015fe Yarar?", 11, "TYT", 9),
    (1, "Kimyan\u0131n Sembolik Dili, G\u00fcvenli\u011fimiz Ve Kimya", 13, "TYT", 9),
    (1, "Madde Ve \u00d6zellikleri", 15, "TYT", 9),
    (1, "Maddenin Ortak Ve Ay\u0131rt Edici \u00d6zellikleri", 17, "TYT", 9),
    (1, "Maddenin Halleri, Is\u0131 Ve Hal De\u011fi\u015fimi", 21, "TYT", 9),
    (1, "Element, Bile\u015fik Ve Kar\u0131\u015f\u0131m", 23, "TYT", 9),
    (1, "Bile\u015fiklerin Adland\u0131r\u0131lmas\u0131", 25, "TYT", 9),
    (1, "Kimya Bilimi (Karma Test)", 27, "TYT", 9),
    (2, "Atom Modelleri", 31, "TYT", 9),
    (2, "Atom Modelleri, Atom Spektrumlar\u0131", 33, "TYT", 9),
    (2, "Atom Modelleri, Atom Alt\u0131 Taneciklerin Ke\u015ffi", 35, "TYT", 9),
    (2, "Atomdaki Temel Tanecikler", 37, "TYT", 9),
    (2, "Atom \u0130le \u0130lgili Terimler", 41, "TYT", 9),
    (2, "Bohr Atom Modeli, Atom Spektrumlar\u0131", 45, "TYT", 9),
    (2, "Atomun Kuantum Modeli", 47, "AYT", 11),
    (2, "Atom Ve Yap\u0131s\u0131", 51, "TYT", 9),
    (
        3,
        "Periyodik Sistemin Tarih\u00e7esi, \u00d6zellikleri, Periyodik Sistemde Yer Bulma",
        53,
        "TYT",
        9,
    ),
    (3, "Periyodik Sistemin Genel \u00d6zellikleri", 55, "TYT", 9),
    (
        3,
        "Periyodik Sistemin Genel \u00d6zellikleri, Periyodik Sistemde Yer Bulma",
        57,
        "TYT",
        9,
    ),
    (3, "Periyodik \u00d6zellikler", 59, "TYT", 9),
    (3, "Periyodik Sistemde Baz\u0131 Gruplar Ve \u00d6zellikleri", 61, "TYT", 9),
    (3, "Periyodik Sistem (Karma Test)", 65, "TYT", 9),
    (3, "Periyodik \u00d6zellikler (Karma Test)", 67, "TYT", 9),
    (3, "Elementleri Tan\u0131yal\u0131m", 71, "AYT", 11),
    (3, "Periyodik Sistem (Karma Test)", 73, "TYT", 9),
    (
        4,
        "Kimyasal T\u00fcrlerin S\u0131n\u0131fland\u0131r\u0131lmas\u0131, Lewis Yap\u0131lar\u0131, G\u00fc\u00e7l\u00fc Etkile\u015fimler",
        77,
        "TYT",
        9,
    ),
    (4, "G\u00fc\u00e7l\u00fc Etkile\u015fimler", 79, "TYT", 9),
    (4, "Zay\u0131f Etkile\u015fimler", 83, "TYT", 9),
    (4, "Kimyasal T\u00fcrler Aras\u0131 Etkile\u015fimler (Karma Test)", 85, "TYT", 9),
    (
        5,
        "Bile\u015fiklerin Adland\u0131r\u0131lmas\u0131, Bile\u015fik Form\u00fclleri",
        91,
        "TYT",
        9,
    ),
    (
        5,
        "Form\u00fcl T\u00fcrleri, Form\u00fcl Yazma, De\u011ferlik Bulma",
        93,
        "TYT",
        9,
    ),
    (5, "Asitler Ve Bazlar", 95, "TYT", 10),
    (5, "Yayg\u0131n Asitler Ve Bazlar", 97, "TYT", 10),
    (5, "Tuzlar, Yayg\u0131n Tuzlar", 99, "TYT", 10),
    (5, "Bile\u015fikler (Karma Test)", 101, "TYT", 10),
    (6, "Kimyasal Tepkimelerin \u00d6zellikleri, Denkle\u015ftirme", 103, "TYT", 10),
    (6, "Tepkime T\u00fcrleri", 105, "TYT", 10),
    (6, "Kimyasal Tepkimeler (Karma Test)", 109, "TYT", 10),
    (7, "Su Ve Hayat", 113, "TYT", 9),
    (7, "\u00c7evre Kimyas\u0131", 119, "TYT", 9),
    (8, "Yayg\u0131n G\u00fcnl\u00fck Hayat Kimyasallar\u0131", 123, "TYT", 10),
    (8, "G\u0131dalar", 131, "TYT", 10),
    (8, "Kimya Her Yerde (Karma Test)", 133, "TYT", 10),
    (9, "Kimyan\u0131n Temel Kanunlar\u0131", 135, "TYT", 10),
    (9, "Mol Kavram\u0131", 141, "TYT", 10),
    (
        9,
        "Denklemli Miktar Ge\u00e7i\u015fleri, Art\u0131k Madde Problemleri",
        145,
        "TYT",
        10,
    ),
    (9, "Form\u00fcl Bulma Problemleri, Verim Problemleri", 147, "TYT", 10),
    (
        9,
        "Kimyan\u0131n Temel Kanunlar\u0131 Ve Kimyasal Hesaplamalar (Karma Test)",
        149,
        "TYT",
        10,
    ),
    (
        10,
        "Gazlar\u0131n \u00d6zellikleri, Gazlar\u0131n Nitelenmesinde Kullan\u0131lan Nicelikler",
        155,
        "AYT",
        11,
    ),
    (10, "Gaz Kanunlar\u0131", 157, "AYT", 11),
    (10, "\u0130deal Gaz Denklemi, Genel Gaz Denklemi", 159, "AYT", 11),
    (
        10,
        "K\u0131smi Bas\u0131n\u00e7, Gazlar\u0131n Kar\u0131\u015ft\u0131r\u0131lmas\u0131",
        161,
        "AYT",
        11,
    ),
    (
        10,
        "Gazlarda Yo\u011funluk, Gazlarda Kinetik, Ger\u00e7ek Gazlar",
        163,
        "AYT",
        11,
    ),
    (10, "S\u0131v\u0131lar", 165, "TYT", 9),
    (
        10,
        "S\u0131v\u0131 Buhar Bas\u0131nc\u0131, Su \u00dcst\u00fcnde Gaz Toplanmas\u0131",
        167,
        "AYT",
        11,
    ),
    (10, "Kat\u0131lar", 169, "TYT", 9),
    (10, "Hal De\u011fi\u015fimleri", 171, "TYT", 9),
    (10, "Maddenin Halleri (Karma Test)", 175, "AYT", 11),
    (
        11,
        "Kar\u0131\u015f\u0131m T\u00fcrleri, \u00c7\u00f6z\u00fcnme S\u00fcreci",
        179,
        "TYT",
        10,
    ),
    (
        11,
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fck, \u00c7\u00f6z\u00fcn\u00fcrl\u00fc\u011fe Etki Eden Fakt\u00f6rler",
        181,
        "AYT",
        11,
    ),
    (11, "Deri\u015fim Birimleri", 183, "AYT", 11),
    (
        11,
        "Deri\u015fme Seyrelme, \u00c7\u00f6zeltilerin Kar\u0131\u015ft\u0131r\u0131lmas\u0131",
        187,
        "AYT",
        11,
    ),
    (11, "Koligatif \u00d6zellikler", 189, "AYT", 11),
    (11, "Kar\u0131\u015f\u0131mlar\u0131n Ayr\u0131lmas\u0131", 193, "TYT", 10),
    (11, "Kar\u0131\u015f\u0131mlar (Karma Test)", 197, "AYT", 11),
    (12, "Tepkimelerde Is\u0131 De\u011fi\u015fimi", 201, "AYT", 11),
    (12, "Olu\u015fum Entalpisi", 203, "AYT", 11),
    (12, "Ba\u011f Enerjileri", 205, "AYT", 11),
    (12, "Tepkime Is\u0131lar\u0131n\u0131n Toplanabilirli\u011fi", 207, "AYT", 11),
    (12, "Kimyasal Tepkimelerde Enerji (Karma Test)", 209, "AYT", 11),
    (13, "Tepkimelerde H\u0131z", 215, "AYT", 11),
    (13, "Tepkime H\u0131z\u0131n\u0131 Etkileyen Fakt\u00f6rler", 217, "AYT", 11),
    (
        13,
        "Tepkime H\u0131z\u0131n\u0131 Etkileyen Fakt\u00f6rler, Kademeli Tepkimeler",
        219,
        "AYT",
        11,
    ),
    (13, "Tepkime H\u0131zlar\u0131", 221, "AYT", 11),
    (13, "Tepkimelerde H\u0131z (Karma Test)", 223, "AYT", 11),
    (14, "Kimyasal Denge, Basit Denge Hesaplamalar\u0131", 229, "AYT", 11),
    (14, "Denge Hesaplamalar\u0131", 231, "AYT", 11),
    (14, "Dengeyi Etkileyen Fakt\u00f6rler", 233, "AYT", 11),
    (14, "Dengeyi Etkileyen Fakt\u00f6rler, Denge Kesri", 235, "AYT", 11),
    (14, "Tepkimelerde Denge (Karma Test)", 237, "AYT", 11),
    (
        15,
        "Asit-Baz Tan\u0131mlar\u0131, Suyun Otoiyonizasyonu, Ph-Poh Kavramlar\u0131",
        243,
        "AYT",
        11,
    ),
    (
        15,
        "Kuvvetli Asit-Bazlarda Ph-Poh Hesaplamalar\u0131, N\u00f6tralle\u015fme Tepkimeleri",
        245,
        "AYT",
        11,
    ),
    (15, "Zay\u0131f Asit-Bazlarda Ph-Poh Hesaplamalar\u0131", 247, "AYT", 11),
    (15, "Tampon \u00c7\u00f6zeltiler, Hidroliz, Titrasyon", 249, "AYT", 11),
    (15, "Sulu \u00c7\u00f6zeltilerde Asit-Baz Dengesi", 251, "AYT", 11),
    (
        15,
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fck, \u00c7\u00f6z\u00fcn\u00fcrl\u00fck \u00c7arp\u0131m\u0131",
        257,
        "AYT",
        11,
    ),
    (
        15,
        "Doymu\u015fluk, Doymam\u0131\u015fl\u0131k, \u00c7\u00f6kelme",
        259,
        "AYT",
        11,
    ),
    (
        15,
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fc\u011fe Etki Eden Fakt\u00f6rler",
        261,
        "AYT",
        11,
    ),
    (15, "Sulu \u00c7\u00f6zelti Dengeleri (Karma Test)", 263, "AYT", 11),
    (16, "Redoks Tepkimelerinin Denkle\u015ftirilmesi", 271, "AYT", 12),
    (16, "Yar\u0131 Pil Potansiyelleri, Elektrokimyasal Piller", 273, "AYT", 12),
    (
        16,
        "Pil Gerilimini Etkileyen Fakt\u00f6rler, G\u00fcnl\u00fck Hayatta Kullan\u0131lan Piller",
        275,
        "AYT",
        12,
    ),
    (16, "Elektroliz, Korozyon", 277, "AYT", 12),
    (16, "Kimya Ve Elektrik", 279, "AYT", 12),
    (
        17,
        "Karbon Kimyas\u0131na Giri\u015f (Anorganik Ve Organik Bile\u015fikler, Karbon Elementi, Do\u011fada Karbon)",
        285,
        "AYT",
        12,
    ),
    (
        17,
        "Anorganik Ve Organik Bile\u015fikler, Karbon Elementi, Do\u011fada Karbon",
        287,
        "AYT",
        12,
    ),
    (17, "Lewis Ve Yap\u0131 Form\u00fclleri", 289, "AYT", 12),
    (17, "Hibritle\u015fme-Molek\u00fcl Geometrileri", 291, "AYT", 12),
    (17, "Karbon Kimyas\u0131na Giri\u015f (Karma Test)", 293, "AYT", 12),
    (18, "Alkanlar (Parafinler)", 299, "AYT", 12),
    (18, "Alkenler (Olefinler)", 301, "AYT", 12),
    (18, "Alkinler (Asetilen S\u0131n\u0131f\u0131 Bile\u015fikler)", 303, "AYT", 12),
    (18, "Alkan, Alken, Alkin", 305, "AYT", 12),
    (18, "\u0130zomerlik", 307, "AYT", 12),
    (18, "Aromatik Bile\u015fikler (Arenler)", 309, "AYT", 12),
    (18, "Alkoller", 313, "AYT", 12),
    (18, "Eterler", 315, "AYT", 12),
    (18, "Alkol - Eter", 317, "AYT", 12),
    (18, "Karbonil Bile\u015fikleri (Aldehitler Ve Ketonlar)", 319, "AYT", 12),
    (18, "Karboksilik Asitler", 323, "AYT", 12),
    (18, "Esterler", 327, "AYT", 12),
    (18, "Organik Bile\u015fikler", 329, "AYT", 12),
    (19, "Fosil Yak\u0131tlar", 339, "AYT", 12),
    (19, "Alternatif Enerji Kaynaklar\u0131", 343, "AYT", 12),
    (19, "S\u00fcrd\u00fcr\u00fclebilirlik - Nanoteknoloji", 345, "AYT", 12),
    (
        19,
        "Enerji Kaynaklar\u0131 Ve Bilimsel Geli\u015fmeler (Karma Test)",
        347,
        "AYT",
        12,
    ),
)
ICINDEKILER: tuple[tuple[int, str, int], ...] = tuple(
    (b, ad, s + 1) for b, ad, s, _, _ in _KONULAR
)


def _sinav_konu() -> dict[str, tuple[str, int]]:
    say: dict[int, int] = {}
    out = {}
    for b, _ad, _s, sinav, sinif in _KONULAR:
        say[b] = say.get(b, 0) + 1
        out[f"{KOD_ONEKI}-B{b:02d}-K{say[b]:02d}"] = (sinav, sinif)
    return out


SINAV_KONU = _sinav_konu()
SON_SAYFA = 349
# Bantta unite adindan farkli basilmis adlar (serit okumasi; normalize anahtar):
# test 26 bandi alt konu adini tasir (dizgi hatasiyla), 13. unite 'TEPKIME
# HIZLARI', 15. unite bant adi icindekilerden farkli.
BANT_ESLER: dict[str, str] = {
    _norm(bant): _norm(bolum)
    for bant, bolum in (
        (
            "PER\u0130YOD\u0130K S\u0130STEM\u0130DE BAZI GRUPLAR VE \u00d6ZEL\u0130L\u0130KLER\u0130",
            "PER\u0130YOD\u0130K S\u0130STEM",
        ),
        ("TEPK\u0130ME HIZLARI", "TEPK\u0130MELERDE HIZ"),
        (
            "SULU \u00c7\u00d6ZELT\u0130LERDE AS\u0130T-BAZ DENGES\u0130 - \u00c7\u00d6Z\u00dcNME "
            "\u2013 \u00c7\u00d6KELME TEPK\u0130MELER\u0130",
            "SULU \u00c7\u00d6ZELT\u0130LERDE AS\u0130T \u2013 BAZ DENGES\u0130 / \u00c7\u00d6Z\u00dcNME-"
            "\u00c7\u00d6KELME DENGELER\u0130",
        ),
    )
}

# --- kutu / kirpim (APO19FZ olcumleri; kutu / kirp kapilariyla dogrulanir) ---
# Kart kenarinda her satirda gri dikey cizgi x 30 (195) ve x 710 (190)
# (c6_mur.py s12 / s13): sutun disinda birakilir, yoksa her satir murekkep
# sayilir ve ust sinir bos bandi bulunamaz ('cok kisa' 836). Dikey mavi APOTEMI
# sekmesi x 361-380 (s12 y 440-533): L sutunu 361'de biter (dahil degil).
SUTUNLAR = {0: {"L": (32, 361), "R": (381, 709)}, 1: {"L": (32, 361), "R": (381, 709)}}
UST_BANT = 98
SAYFA_ALTI = 876
SAYFA_ALTLIGI_Y = 878
SERIT_ALTLIKTA = True
SUS_BOLGELERI: tuple[tuple[int, int, int, int], ...] = ()
BEKLENEN_SORU = 1838

# --- metin ---
KITAP_BASLIGI = "2019-2020 Apotemi TYT-AYT Kimya Soru Bankas\u0131"
GRUP_SORU = 60
SEKIL_SATIRI = True
TALIMAT_EK = (
    "\n## Bu kitaba ozel\n"
    "Soru numarasi SIYAH kalin basilidir; her test 1'den baslar. Kimyasal "
    "formullerde alt indis `_` ile, iyon yuku / ust simge `^` ile yazilir (DB'deki "
    "kimya kitaplariyla ayni sozlesme): `H_2O`, `Na_2CO_3`, `NH_4Cl`, `Na^+`, "
    "`SO_4^(2\u2212)`, `^(12)C`, `5 \u00b7 10^(\u221223)`; hal simgeleri basildigi "
    "gibi `(suda)`, `(g)`, `(k)`, `(s)`. Okun yonu `\u2192` / `\u21cc`. Sayfadaki "
    "soluk 'APOTEMI' filigrani metne girmez.\n"
    "YAPI FORMULU (mekanik kural): iki boyutlu cizilmis yapi formulu (acik "
    "formul, Lewis yapisi, halka / benzen cizimi, ustunde ya da altinda dal / "
    "cift bagli O olan zincir -- yani DIKEY bag iceren her yapi) metne AKTARILMAZ: "
    "bulundugu yere `[yapi]` yaz (romen rakamli listede `I. [yapi]`, tabloda hucreye "
    "`[yapi]`), `sekil_var` true. Dikey bag icermeyen, tek satirda basili formul ve "
    "tepkime denklemi (`CH_3 \u2212 CH_2 \u2212 OH`, `C_2H_5OH + O_2 \u2192 X`) "
    "metin olarak yazilir. Yapi cizimlerindeki atom / indis yazilari `\u015eekil:` "
    "satirina GIRMEZ; `\u015eekil:` satiri yalniz deney duzenegi, grafik ve "
    "cizimlerdeki rakamli etiketler icindir (`25 \u00b0C`, `2 atm`, `1 L`).\n"
    "GORUNMEYEN ISARET: ekran goruntusunde ince yatay cizgiler (eksi, kesir "
    "cizgisi parcasi, arti isaretinin yatay kolu, ok govdesi) bazen HIC cikmamis "
    "olabilir: yerinde yalniz bosluk vardir. Boyle bir yere isaret TAHMIN ETME: "
    "o yere `[??]` yaz ve `kaynak_kusuru`na 'isaret gorunmuyor: <yer>' yaz. Soluk "
    "ama pikselde secilebilen isaret basildigi gibi yazilir.\n"
)

# --- mukerrer / ithal ---
DERSLER = ("KIMYA",)
ESKI_KAYNAKLAR: tuple[str, ...] = ("Apotemi Tyt Ayt Kimya 2019-2020",)
MODERN_IKIZ_KAYNAK = None
YAYINEVI = "Apotemi Yayinlari"
BEKLENEN_ETIKET = 0
YONTEM_BELGESI = "KIM_APOTEMI_2019_TYT_AYT_YONTEM.md"

SONUC = {
    "sayfa_turu": {"kapak": 14, "test": 338},
    "harf": {"A": 343, "B": 329, "C": 344, "D": 388, "E": 434},
    "glif_hucre": 1839,
    "glif_uyum": 1838,
    "goz_teyit": {"T005#4": "C"},
    "glif_disi": [],
    "metin_parca": 29,
    "farkli_soru": 290,
    "okunamaz": 35,
    "ithal": 1838,
    "beta": "1803/1838",
    "eski_modern": 236,
    "migration_no": 122,
    "onceki": "0121_apo19fz_beta_onay",
}
