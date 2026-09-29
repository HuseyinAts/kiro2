"""2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi: kitabin kendi bolum / konu agaci (KIM-APO19KM).

Revision ID: 0122_apo19km_agac
Revises: 0121_apo19fz_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (169 test, 1838 soru) kitabin bolum / konu
yapisina baglar. KIM kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini KIM-APO19KM onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/apotemi_2019_tyt_ayt_kimya_konu_haritasi.json` ile
BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya icindekiler ve
test ust bandindan (iki bagimsiz okuma) uretildi.

DUZEY
-----
Bolum kok+1, konu kok+2; sorular konu dugumune baglanir.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca onlari
siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0122_apo19km_agac"
down_revision: Union[str, None] = "0121_apo19fz_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19km_konu_gunlugu_0122"
KOK = "KIM"
KOD_ONEKI = "KIM-APO19KM"
ALAN = "KIMYA"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("KIM-APO19KM-B01", "1. \u00dcN\u0130TE K\u0130MYA B\u0130L\u0130M\u0130"),
    ("KIM-APO19KM-B02", "2. \u00dcN\u0130TE ATOM VE YAPISI"),
    ("KIM-APO19KM-B03", "3. \u00dcN\u0130TE PER\u0130YOD\u0130K S\u0130STEM"),
    (
        "KIM-APO19KM-B04",
        "4. \u00dcN\u0130TE K\u0130MYASAL T\u00dcRLER ARASI ETK\u0130LE\u015e\u0130MLER",
    ),
    ("KIM-APO19KM-B05", "5. \u00dcN\u0130TE B\u0130LE\u015e\u0130KLER"),
    ("KIM-APO19KM-B06", "6. \u00dcN\u0130TE K\u0130MYASAL TEPK\u0130MELER"),
    ("KIM-APO19KM-B07", "7. \u00dcN\u0130TE DO\u011eA VE K\u0130MYA"),
    ("KIM-APO19KM-B08", "8. \u00dcN\u0130TE K\u0130MYA HER YERDE"),
    (
        "KIM-APO19KM-B09",
        "9. \u00dcN\u0130TE K\u0130MYANIN TEMEL KANUNLARI VE K\u0130MYASAL HESAPLAMALAR",
    ),
    ("KIM-APO19KM-B10", "10. \u00dcN\u0130TE MADDEN\u0130N HALLER\u0130"),
    ("KIM-APO19KM-B11", "11. \u00dcN\u0130TE KARI\u015eIMLAR"),
    (
        "KIM-APO19KM-B12",
        "12. \u00dcN\u0130TE K\u0130MYASAL TEPK\u0130MELERDE ENERJ\u0130",
    ),
    ("KIM-APO19KM-B13", "13. \u00dcN\u0130TE TEPK\u0130MELERDE HIZ"),
    ("KIM-APO19KM-B14", "14. \u00dcN\u0130TE TEPK\u0130MELERDE DENGE"),
    (
        "KIM-APO19KM-B15",
        "15. \u00dcN\u0130TE SULU \u00c7\u00d6ZELT\u0130LERDE AS\u0130T \u2013 BAZ DENGES\u0130 / \u00c7\u00d6Z\u00dcNME-\u00c7\u00d6KELME DENGELER\u0130",
    ),
    ("KIM-APO19KM-B16", "16. \u00dcN\u0130TE K\u0130MYA VE ELEKTR\u0130K"),
    (
        "KIM-APO19KM-B17",
        "17. \u00dcN\u0130TE KARBON K\u0130MYASINA G\u0130R\u0130\u015e",
    ),
    ("KIM-APO19KM-B18", "18. \u00dcN\u0130TE ORGAN\u0130K B\u0130LE\u015e\u0130KLER"),
    (
        "KIM-APO19KM-B19",
        "19. \u00dcN\u0130TE ENERJ\u0130 KAYNAKLARI VE B\u0130L\u0130MSEL GEL\u0130\u015eMELER",
    ),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    (
        "KIM-APO19KM-B01-K01",
        "Kimya Nedir?, Kimya Ne \u0130\u015fe Yarar?",
        "KIM-APO19KM-B01",
    ),
    (
        "KIM-APO19KM-B01-K02",
        "Kimyan\u0131n Sembolik Dili, G\u00fcvenli\u011fimiz Ve Kimya",
        "KIM-APO19KM-B01",
    ),
    ("KIM-APO19KM-B01-K03", "Madde Ve \u00d6zellikleri", "KIM-APO19KM-B01"),
    (
        "KIM-APO19KM-B01-K04",
        "Maddenin Ortak Ve Ay\u0131rt Edici \u00d6zellikleri",
        "KIM-APO19KM-B01",
    ),
    (
        "KIM-APO19KM-B01-K05",
        "Maddenin Halleri, Is\u0131 Ve Hal De\u011fi\u015fimi",
        "KIM-APO19KM-B01",
    ),
    (
        "KIM-APO19KM-B01-K06",
        "Element, Bile\u015fik Ve Kar\u0131\u015f\u0131m",
        "KIM-APO19KM-B01",
    ),
    (
        "KIM-APO19KM-B01-K07",
        "Bile\u015fiklerin Adland\u0131r\u0131lmas\u0131",
        "KIM-APO19KM-B01",
    ),
    ("KIM-APO19KM-B01-K08", "Kimya Bilimi (Karma Test)", "KIM-APO19KM-B01"),
    ("KIM-APO19KM-B02-K01", "Atom Modelleri", "KIM-APO19KM-B02"),
    (
        "KIM-APO19KM-B02-K02",
        "Atom Modelleri, Atom Spektrumlar\u0131",
        "KIM-APO19KM-B02",
    ),
    (
        "KIM-APO19KM-B02-K03",
        "Atom Modelleri, Atom Alt\u0131 Taneciklerin Ke\u015ffi",
        "KIM-APO19KM-B02",
    ),
    ("KIM-APO19KM-B02-K04", "Atomdaki Temel Tanecikler", "KIM-APO19KM-B02"),
    ("KIM-APO19KM-B02-K05", "Atom \u0130le \u0130lgili Terimler", "KIM-APO19KM-B02"),
    (
        "KIM-APO19KM-B02-K06",
        "Bohr Atom Modeli, Atom Spektrumlar\u0131",
        "KIM-APO19KM-B02",
    ),
    ("KIM-APO19KM-B02-K07", "Atomun Kuantum Modeli", "KIM-APO19KM-B02"),
    ("KIM-APO19KM-B02-K08", "Atom Ve Yap\u0131s\u0131", "KIM-APO19KM-B02"),
    (
        "KIM-APO19KM-B03-K01",
        "Periyodik Sistemin Tarih\u00e7esi, \u00d6zellikleri, Periyodik Sistemde Yer Bulma",
        "KIM-APO19KM-B03",
    ),
    (
        "KIM-APO19KM-B03-K02",
        "Periyodik Sistemin Genel \u00d6zellikleri",
        "KIM-APO19KM-B03",
    ),
    (
        "KIM-APO19KM-B03-K03",
        "Periyodik Sistemin Genel \u00d6zellikleri, Periyodik Sistemde Yer Bulma",
        "KIM-APO19KM-B03",
    ),
    ("KIM-APO19KM-B03-K04", "Periyodik \u00d6zellikler", "KIM-APO19KM-B03"),
    (
        "KIM-APO19KM-B03-K05",
        "Periyodik Sistemde Baz\u0131 Gruplar Ve \u00d6zellikleri",
        "KIM-APO19KM-B03",
    ),
    ("KIM-APO19KM-B03-K06", "Periyodik Sistem (Karma Test)", "KIM-APO19KM-B03"),
    (
        "KIM-APO19KM-B03-K07",
        "Periyodik \u00d6zellikler (Karma Test)",
        "KIM-APO19KM-B03",
    ),
    ("KIM-APO19KM-B03-K08", "Elementleri Tan\u0131yal\u0131m", "KIM-APO19KM-B03"),
    ("KIM-APO19KM-B03-K09", "Periyodik Sistem (Karma Test)", "KIM-APO19KM-B03"),
    (
        "KIM-APO19KM-B04-K01",
        "Kimyasal T\u00fcrlerin S\u0131n\u0131fland\u0131r\u0131lmas\u0131, Lewis Yap\u0131lar\u0131, G\u00fc\u00e7l\u00fc Etkile\u015fimler",
        "KIM-APO19KM-B04",
    ),
    (
        "KIM-APO19KM-B04-K02",
        "G\u00fc\u00e7l\u00fc Etkile\u015fimler",
        "KIM-APO19KM-B04",
    ),
    ("KIM-APO19KM-B04-K03", "Zay\u0131f Etkile\u015fimler", "KIM-APO19KM-B04"),
    (
        "KIM-APO19KM-B04-K04",
        "Kimyasal T\u00fcrler Aras\u0131 Etkile\u015fimler (Karma Test)",
        "KIM-APO19KM-B04",
    ),
    (
        "KIM-APO19KM-B05-K01",
        "Bile\u015fiklerin Adland\u0131r\u0131lmas\u0131, Bile\u015fik Form\u00fclleri",
        "KIM-APO19KM-B05",
    ),
    (
        "KIM-APO19KM-B05-K02",
        "Form\u00fcl T\u00fcrleri, Form\u00fcl Yazma, De\u011ferlik Bulma",
        "KIM-APO19KM-B05",
    ),
    ("KIM-APO19KM-B05-K03", "Asitler Ve Bazlar", "KIM-APO19KM-B05"),
    ("KIM-APO19KM-B05-K04", "Yayg\u0131n Asitler Ve Bazlar", "KIM-APO19KM-B05"),
    ("KIM-APO19KM-B05-K05", "Tuzlar, Yayg\u0131n Tuzlar", "KIM-APO19KM-B05"),
    ("KIM-APO19KM-B05-K06", "Bile\u015fikler (Karma Test)", "KIM-APO19KM-B05"),
    (
        "KIM-APO19KM-B06-K01",
        "Kimyasal Tepkimelerin \u00d6zellikleri, Denkle\u015ftirme",
        "KIM-APO19KM-B06",
    ),
    ("KIM-APO19KM-B06-K02", "Tepkime T\u00fcrleri", "KIM-APO19KM-B06"),
    ("KIM-APO19KM-B06-K03", "Kimyasal Tepkimeler (Karma Test)", "KIM-APO19KM-B06"),
    ("KIM-APO19KM-B07-K01", "Su Ve Hayat", "KIM-APO19KM-B07"),
    ("KIM-APO19KM-B07-K02", "\u00c7evre Kimyas\u0131", "KIM-APO19KM-B07"),
    (
        "KIM-APO19KM-B08-K01",
        "Yayg\u0131n G\u00fcnl\u00fck Hayat Kimyasallar\u0131",
        "KIM-APO19KM-B08",
    ),
    ("KIM-APO19KM-B08-K02", "G\u0131dalar", "KIM-APO19KM-B08"),
    ("KIM-APO19KM-B08-K03", "Kimya Her Yerde (Karma Test)", "KIM-APO19KM-B08"),
    ("KIM-APO19KM-B09-K01", "Kimyan\u0131n Temel Kanunlar\u0131", "KIM-APO19KM-B09"),
    ("KIM-APO19KM-B09-K02", "Mol Kavram\u0131", "KIM-APO19KM-B09"),
    (
        "KIM-APO19KM-B09-K03",
        "Denklemli Miktar Ge\u00e7i\u015fleri, Art\u0131k Madde Problemleri",
        "KIM-APO19KM-B09",
    ),
    (
        "KIM-APO19KM-B09-K04",
        "Form\u00fcl Bulma Problemleri, Verim Problemleri",
        "KIM-APO19KM-B09",
    ),
    (
        "KIM-APO19KM-B09-K05",
        "Kimyan\u0131n Temel Kanunlar\u0131 Ve Kimyasal Hesaplamalar (Karma Test)",
        "KIM-APO19KM-B09",
    ),
    (
        "KIM-APO19KM-B10-K01",
        "Gazlar\u0131n \u00d6zellikleri, Gazlar\u0131n Nitelenmesinde Kullan\u0131lan Nicelikler",
        "KIM-APO19KM-B10",
    ),
    ("KIM-APO19KM-B10-K02", "Gaz Kanunlar\u0131", "KIM-APO19KM-B10"),
    (
        "KIM-APO19KM-B10-K03",
        "\u0130deal Gaz Denklemi, Genel Gaz Denklemi",
        "KIM-APO19KM-B10",
    ),
    (
        "KIM-APO19KM-B10-K04",
        "K\u0131smi Bas\u0131n\u00e7, Gazlar\u0131n Kar\u0131\u015ft\u0131r\u0131lmas\u0131",
        "KIM-APO19KM-B10",
    ),
    (
        "KIM-APO19KM-B10-K05",
        "Gazlarda Yo\u011funluk, Gazlarda Kinetik, Ger\u00e7ek Gazlar",
        "KIM-APO19KM-B10",
    ),
    ("KIM-APO19KM-B10-K06", "S\u0131v\u0131lar", "KIM-APO19KM-B10"),
    (
        "KIM-APO19KM-B10-K07",
        "S\u0131v\u0131 Buhar Bas\u0131nc\u0131, Su \u00dcst\u00fcnde Gaz Toplanmas\u0131",
        "KIM-APO19KM-B10",
    ),
    ("KIM-APO19KM-B10-K08", "Kat\u0131lar", "KIM-APO19KM-B10"),
    ("KIM-APO19KM-B10-K09", "Hal De\u011fi\u015fimleri", "KIM-APO19KM-B10"),
    ("KIM-APO19KM-B10-K10", "Maddenin Halleri (Karma Test)", "KIM-APO19KM-B10"),
    (
        "KIM-APO19KM-B11-K01",
        "Kar\u0131\u015f\u0131m T\u00fcrleri, \u00c7\u00f6z\u00fcnme S\u00fcreci",
        "KIM-APO19KM-B11",
    ),
    (
        "KIM-APO19KM-B11-K02",
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fck, \u00c7\u00f6z\u00fcn\u00fcrl\u00fc\u011fe Etki Eden Fakt\u00f6rler",
        "KIM-APO19KM-B11",
    ),
    ("KIM-APO19KM-B11-K03", "Deri\u015fim Birimleri", "KIM-APO19KM-B11"),
    (
        "KIM-APO19KM-B11-K04",
        "Deri\u015fme Seyrelme, \u00c7\u00f6zeltilerin Kar\u0131\u015ft\u0131r\u0131lmas\u0131",
        "KIM-APO19KM-B11",
    ),
    ("KIM-APO19KM-B11-K05", "Koligatif \u00d6zellikler", "KIM-APO19KM-B11"),
    (
        "KIM-APO19KM-B11-K06",
        "Kar\u0131\u015f\u0131mlar\u0131n Ayr\u0131lmas\u0131",
        "KIM-APO19KM-B11",
    ),
    (
        "KIM-APO19KM-B11-K07",
        "Kar\u0131\u015f\u0131mlar (Karma Test)",
        "KIM-APO19KM-B11",
    ),
    (
        "KIM-APO19KM-B12-K01",
        "Tepkimelerde Is\u0131 De\u011fi\u015fimi",
        "KIM-APO19KM-B12",
    ),
    ("KIM-APO19KM-B12-K02", "Olu\u015fum Entalpisi", "KIM-APO19KM-B12"),
    ("KIM-APO19KM-B12-K03", "Ba\u011f Enerjileri", "KIM-APO19KM-B12"),
    (
        "KIM-APO19KM-B12-K04",
        "Tepkime Is\u0131lar\u0131n\u0131n Toplanabilirli\u011fi",
        "KIM-APO19KM-B12",
    ),
    (
        "KIM-APO19KM-B12-K05",
        "Kimyasal Tepkimelerde Enerji (Karma Test)",
        "KIM-APO19KM-B12",
    ),
    ("KIM-APO19KM-B13-K01", "Tepkimelerde H\u0131z", "KIM-APO19KM-B13"),
    (
        "KIM-APO19KM-B13-K02",
        "Tepkime H\u0131z\u0131n\u0131 Etkileyen Fakt\u00f6rler",
        "KIM-APO19KM-B13",
    ),
    (
        "KIM-APO19KM-B13-K03",
        "Tepkime H\u0131z\u0131n\u0131 Etkileyen Fakt\u00f6rler, Kademeli Tepkimeler",
        "KIM-APO19KM-B13",
    ),
    ("KIM-APO19KM-B13-K04", "Tepkime H\u0131zlar\u0131", "KIM-APO19KM-B13"),
    ("KIM-APO19KM-B13-K05", "Tepkimelerde H\u0131z (Karma Test)", "KIM-APO19KM-B13"),
    (
        "KIM-APO19KM-B14-K01",
        "Kimyasal Denge, Basit Denge Hesaplamalar\u0131",
        "KIM-APO19KM-B14",
    ),
    ("KIM-APO19KM-B14-K02", "Denge Hesaplamalar\u0131", "KIM-APO19KM-B14"),
    ("KIM-APO19KM-B14-K03", "Dengeyi Etkileyen Fakt\u00f6rler", "KIM-APO19KM-B14"),
    (
        "KIM-APO19KM-B14-K04",
        "Dengeyi Etkileyen Fakt\u00f6rler, Denge Kesri",
        "KIM-APO19KM-B14",
    ),
    ("KIM-APO19KM-B14-K05", "Tepkimelerde Denge (Karma Test)", "KIM-APO19KM-B14"),
    (
        "KIM-APO19KM-B15-K01",
        "Asit-Baz Tan\u0131mlar\u0131, Suyun Otoiyonizasyonu, Ph-Poh Kavramlar\u0131",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K02",
        "Kuvvetli Asit-Bazlarda Ph-Poh Hesaplamalar\u0131, N\u00f6tralle\u015fme Tepkimeleri",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K03",
        "Zay\u0131f Asit-Bazlarda Ph-Poh Hesaplamalar\u0131",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K04",
        "Tampon \u00c7\u00f6zeltiler, Hidroliz, Titrasyon",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K05",
        "Sulu \u00c7\u00f6zeltilerde Asit-Baz Dengesi",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K06",
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fck, \u00c7\u00f6z\u00fcn\u00fcrl\u00fck \u00c7arp\u0131m\u0131",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K07",
        "Doymu\u015fluk, Doymam\u0131\u015fl\u0131k, \u00c7\u00f6kelme",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K08",
        "\u00c7\u00f6z\u00fcn\u00fcrl\u00fc\u011fe Etki Eden Fakt\u00f6rler",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B15-K09",
        "Sulu \u00c7\u00f6zelti Dengeleri (Karma Test)",
        "KIM-APO19KM-B15",
    ),
    (
        "KIM-APO19KM-B16-K01",
        "Redoks Tepkimelerinin Denkle\u015ftirilmesi",
        "KIM-APO19KM-B16",
    ),
    (
        "KIM-APO19KM-B16-K02",
        "Yar\u0131 Pil Potansiyelleri, Elektrokimyasal Piller",
        "KIM-APO19KM-B16",
    ),
    (
        "KIM-APO19KM-B16-K03",
        "Pil Gerilimini Etkileyen Fakt\u00f6rler, G\u00fcnl\u00fck Hayatta Kullan\u0131lan Piller",
        "KIM-APO19KM-B16",
    ),
    ("KIM-APO19KM-B16-K04", "Elektroliz, Korozyon", "KIM-APO19KM-B16"),
    ("KIM-APO19KM-B16-K05", "Kimya Ve Elektrik", "KIM-APO19KM-B16"),
    (
        "KIM-APO19KM-B17-K01",
        "Karbon Kimyas\u0131na Giri\u015f (Anorganik Ve Organik Bile\u015fikler, Karbon Elementi, Do\u011fada Karbon)",
        "KIM-APO19KM-B17",
    ),
    (
        "KIM-APO19KM-B17-K02",
        "Anorganik Ve Organik Bile\u015fikler, Karbon Elementi, Do\u011fada Karbon",
        "KIM-APO19KM-B17",
    ),
    ("KIM-APO19KM-B17-K03", "Lewis Ve Yap\u0131 Form\u00fclleri", "KIM-APO19KM-B17"),
    (
        "KIM-APO19KM-B17-K04",
        "Hibritle\u015fme-Molek\u00fcl Geometrileri",
        "KIM-APO19KM-B17",
    ),
    (
        "KIM-APO19KM-B17-K05",
        "Karbon Kimyas\u0131na Giri\u015f (Karma Test)",
        "KIM-APO19KM-B17",
    ),
    ("KIM-APO19KM-B18-K01", "Alkanlar (Parafinler)", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K02", "Alkenler (Olefinler)", "KIM-APO19KM-B18"),
    (
        "KIM-APO19KM-B18-K03",
        "Alkinler (Asetilen S\u0131n\u0131f\u0131 Bile\u015fikler)",
        "KIM-APO19KM-B18",
    ),
    ("KIM-APO19KM-B18-K04", "Alkan, Alken, Alkin", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K05", "\u0130zomerlik", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K06", "Aromatik Bile\u015fikler (Arenler)", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K07", "Alkoller", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K08", "Eterler", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K09", "Alkol - Eter", "KIM-APO19KM-B18"),
    (
        "KIM-APO19KM-B18-K10",
        "Karbonil Bile\u015fikleri (Aldehitler Ve Ketonlar)",
        "KIM-APO19KM-B18",
    ),
    ("KIM-APO19KM-B18-K11", "Karboksilik Asitler", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K12", "Esterler", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B18-K13", "Organik Bile\u015fikler", "KIM-APO19KM-B18"),
    ("KIM-APO19KM-B19-K01", "Fosil Yak\u0131tlar", "KIM-APO19KM-B19"),
    ("KIM-APO19KM-B19-K02", "Alternatif Enerji Kaynaklar\u0131", "KIM-APO19KM-B19"),
    (
        "KIM-APO19KM-B19-K03",
        "S\u00fcrd\u00fcr\u00fclebilirlik - Nanoteknoloji",
        "KIM-APO19KM-B19",
    ),
    (
        "KIM-APO19KM-B19-K04",
        "Enerji Kaynaklar\u0131 Ve Bilimsel Geli\u015fmeler (Karma Test)",
        "KIM-APO19KM-B19",
    ),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, :alan, TRUE, now(), now())
    """
)

_ACIKLAMA = (
    "2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0122)."
)

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


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0122] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0122] mv_safe_for_beta yenilendi")


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _yaz(b, kod, ad, level, parent_id, *, alan) -> str:
    yeni_id = _dugum_id(kod)
    b.execute(
        _EKLE,
        {
            "id": yeni_id,
            "level": level,
            "parent_id": parent_id,
            "code": kod,
            "name_tr": ad,
            "aciklama": _ACIKLAMA,
            "alan": alan,
        },
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            "VALUES (:id, :kod, TRUE)"
        ),
        {"id": yeni_id, "kod": kod},
    )
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0122] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0122] %s kok konusu yok -- atlandi", KOK)
        return
    kok_id, kok_level = r[0], int(r[1])
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Yalniz KOD_ONEKI deseni; kokun diger dugumlerine DOKUNULMAZ ('-' ile biten desen).
    mevcut = {
        r[0]: r[1]
        for r in b.execute(
            sa.text("SELECT code, id FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }
    eklenen = 0
    bolum_id = {}
    for kod, ad in BOLUMLER:
        if kod in mevcut:
            bolum_id[kod] = mevcut[kod]
            continue
        bolum_id[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id, alan=ALAN)
        eklenen += 1
    for kod, ad, bolum in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, bolum_id[bolum], alan=ALAN)
        eklenen += 1
    _log.info(
        "[0122] %s bolum + %s konu tanimi; eklenen dugum: %s",
        len(BOLUMLER),
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0122] %s yok -- downgrade atlandi", GUNLUK)
        return
    idler = [
        r[0]
        for r in b.execute(
            sa.text(f"SELECT id FROM {GUNLUK} WHERE olusturuldu IS TRUE")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
        ).fetchall()
    ]
    if idler and sa.inspect(b).has_table("question_bank"):
        kullanilan = {
            r[0]
            for r in b.execute(
                sa.text(
                    "SELECT DISTINCT primary_topic_id FROM question_bank "
                    "WHERE primary_topic_id = ANY(:idler)"
                ),
                {"idler": idler},
            ).fetchall()
        }
        if kullanilan:
            _log.warning(
                "[0122] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        for _ in range(2):
            b.execute(
                sa.text(
                    "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                    "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                    "WHERE c.parent_id = topic_hierarchy.id)"
                ),
                {"idler": idler},
            )
    op.drop_table(GUNLUK)
    _log.info("[0122] downgrade tamam; silinmeye aday dugum: %s", len(idler))
