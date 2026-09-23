"""ACIL 2025 KURS TYT-AYT Geometri: kitabin kendi konu agaci (GEO-ACL25).

NEDEN
-----
Bu kitabin ithali her soruyu bir konu dugumune baglar. GEO kokunun altinda
baska agaclar var (GEO-U*, GEO-ACL24, GEO-C1C24, GEO-ORJ24); ACIL 2025
KURS'un kendi konu ve alt baslik adlari hicbiriyle birebir ortusmuyor (ayni
yayinevinin 2023-2024 baskisi dahil: farkli ISBN, farkli yazar kadrosu,
farkli dizgi). Sessizce "en yakin" dugume baglamak yanlis veridir; bu
migration kitabin agacini GEO-ACL25 onekiyle ayri bir alt agac olarak kurar
(0034 / 0035 / 0040 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Icindekiler sayfasi yakalamada YOK (Faz 0 K0.7). Kodlar ve adlar
`veriseti/zkitap/cikti/acil_2025_geometri_konu_haritasi.json` ile BIREBIR
aynidir (ASCII katlanmis); o dosya:
  * 33 konu: 392 soru sayfasinin ust bandindaki kirmizi baslik, iki
    bagimsiz okuma (391/392 ayni, fark kitabin kendi basim hatasi),
  * 315 alt konu: 'Konu Ogrenme' sayfalarindaki 331 sari alt baslik
    kutusu, iki bagimsiz okuma (330/331 ayni, fark bir virgul),
uzerinden uretildi. Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Kitapta bolum (ust grup) duzeyi GORUNMUYOR; uydurulmadi. Konu kok+1, alt
konu kok+2. Konu Ogrenme birimlerinin sorulari alt konuya, test
birimlerininki konuya baglanir (0034'te de alt konu dugumune baglanan soru
var -- baglanti derinligi agaca gore degisebilir).

33 konu + 315 alt konu = 348 dugum.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0041_acil25geo_agac"
down_revision: Union[str, None] = "0040_orijinalgeo_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acil25geo_konu_gunlugu_0041"
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ACL25"

# (kod, ad)
KONULAR: tuple[tuple[str, str], ...] = (
    ("GEO-ACL25-K01", "Dogruda Aci"),
    ("GEO-ACL25-K02", "Ucgende Aci"),
    ("GEO-ACL25-K03", "Pisagor Teoremi"),
    ("GEO-ACL25-K04", "Oklit Teoremi"),
    ("GEO-ACL25-K05", "Ozel Ucgenler"),
    ("GEO-ACL25-K06", "Aciortay"),
    ("GEO-ACL25-K07", "Kenarortay"),
    ("GEO-ACL25-K08", "Eslik ve Benzerlik"),
    ("GEO-ACL25-K09", "Ucgende Alan"),
    ("GEO-ACL25-K10", "Ucgende Aci ve Kenar Bagintilari"),
    ("GEO-ACL25-K11", "Geometrik Merkezler"),
    ("GEO-ACL25-K12", "Cokgenler"),
    ("GEO-ACL25-K13", "Genel Dortgenler"),
    ("GEO-ACL25-K14", "Yamuk"),
    ("GEO-ACL25-K15", "Paralelkenar"),
    ("GEO-ACL25-K16", "Eskenar Dortgen"),
    ("GEO-ACL25-K17", "Deltoid"),
    ("GEO-ACL25-K18", "Dikdortgen"),
    ("GEO-ACL25-K19", "Kare"),
    ("GEO-ACL25-K20", "Cemberde Aci"),
    ("GEO-ACL25-K21", "Cemberde Uzunluk"),
    ("GEO-ACL25-K22", "Cemberin Cevresi"),
    ("GEO-ACL25-K23", "Dairenin Alani"),
    ("GEO-ACL25-K24", "Noktanin Analitigi"),
    ("GEO-ACL25-K25", "Dogrunun Analitigi"),
    ("GEO-ACL25-K26", "Donusum Geometrisi"),
    ("GEO-ACL25-K27", "Analitik Geometri Genel"),
    ("GEO-ACL25-K28", "Dik Prizmalar"),
    ("GEO-ACL25-K29", "Dik Dairesel Silindir"),
    ("GEO-ACL25-K30", "Dik Piramitler"),
    ("GEO-ACL25-K31", "Koni"),
    ("GEO-ACL25-K32", "Kure"),
    ("GEO-ACL25-K33", "Cemberin Analitigi"),
)

# (ust kod, kod, ad)
ALT_KONULAR: tuple[tuple[str, str, str], ...] = (
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A01", "Aci Cesitleri"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A02", "Tumler ve Butunler Aci"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A03", "Aciortay Dogrulari"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A04", "Paralel Dogrularin Olusturdugu Acilar 1"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A05", "Paralel Dogrularin Olusturdugu Acilar 2"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A06", "Yorum Sorulari"),
    ("GEO-ACL25-K01", "GEO-ACL25-K01-A07", "Yon ve Dondurme Sorulari"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A01", "Ucgende Aci"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A02", "Ikizkenar Ucgende Aci"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A03", "Ikizkenar Ucgende Simetri"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A04", "Eskenar Ucgende Aci"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A05", "Kes Yapistir Sorulari"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A06", "Katlama Sorulari"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A07", "Dondurme Sorulari"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A08", "Aciortaylarin Olusturdugu Acilar"),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A09", "Muhtesem Uclu"),
    (
        "GEO-ACL25-K02",
        "GEO-ACL25-K02-A10",
        "Ozdes Ucgenlerle Olusturulmus Aci Sorulari",
    ),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A11", "Sozel Olarak Ifade Edilmis Aci Sorulari"),
    (
        "GEO-ACL25-K02",
        "GEO-ACL25-K02-A12",
        "Cetvel, Cubuk, Makas vb Kullanilarak Olusturulmus Aci Sorulari",
    ),
    ("GEO-ACL25-K02", "GEO-ACL25-K02-A13", "Pusula Sorulari"),
    ("GEO-ACL25-K03", "GEO-ACL25-K03-A01", "Pisagor Teoremi"),
    ("GEO-ACL25-K03", "GEO-ACL25-K03-A02", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K03", "GEO-ACL25-K03-A03", "En Kisa Mesafe Problemleri"),
    ("GEO-ACL25-K04", "GEO-ACL25-K04-A01", "Oklit Teoremi 1"),
    ("GEO-ACL25-K04", "GEO-ACL25-K04-A02", "Oklit Teoremi 2"),
    ("GEO-ACL25-K04", "GEO-ACL25-K04-A03", "Oklit Teoremi 3"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A01", "Ozel Acili Ucgenler"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A02", "Ikizkenar Ucgen"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A03", "Ikizkenar Ucgende Yukseklik 1"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A04", "Ikizkenar Ucgende Yukseklik 2"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A05", "Eskenar Ucgen"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A06", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A07", "Katlama Kesme Sorulari"),
    ("GEO-ACL25-K05", "GEO-ACL25-K05-A08", "Tanim Verilen Sorular"),
    (
        "GEO-ACL25-K06",
        "GEO-ACL25-K06-A01",
        "Aciortay Uzerindeki Bir Noktadan Yan Kenarlara Dikme Inme",
    ),
    ("GEO-ACL25-K06", "GEO-ACL25-K06-A02", "Ic Aciortay Teoremi"),
    (
        "GEO-ACL25-K06",
        "GEO-ACL25-K06-A03",
        "Bir Dogru Parcasinin Aciortay, Yukseklik ve Kenarortaydan Ikisi Olmasi",
    ),
    ("GEO-ACL25-K06", "GEO-ACL25-K06-A04", "Katlama Sorulari"),
    ("GEO-ACL25-K06", "GEO-ACL25-K06-A05", "Ic teget Cemberin Merkezi"),
    ("GEO-ACL25-K06", "GEO-ACL25-K06-A06", "Dis Aciortay Teoremi"),
    ("GEO-ACL25-K06", "GEO-ACL25-K06-A07", "Ic ve Dis Aciortay Teoremi"),
    ("GEO-ACL25-K07", "GEO-ACL25-K07-A01", "Kenarortaylarin Kesim Noktasi"),
    ("GEO-ACL25-K07", "GEO-ACL25-K07-A02", "Agirlik Merkezi ve Aciortay"),
    ("GEO-ACL25-K07", "GEO-ACL25-K07-A03", "Agirlik Merkezi ve Muhtesem Uclu Iliskisi"),
    ("GEO-ACL25-K07", "GEO-ACL25-K07-A04", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K07", "GEO-ACL25-K07-A05", "Katlama Sorulari"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A01", "Eslik"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A02", "Kenar Aci Kenar Esligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A03", "Aci Kenar Aci Esligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A04", "Kenar Kenar Kenar Esligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A05", "Benzer Ucgenler"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A06", "Aci Aci Aci Benzerligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A07", "Kenar Aci Kenar Benzerligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A08", "Kenar Kenar Kenar Benzerligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A09", "Benzerlik Orani"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A10", "Temel Benzerlik Teoremi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A11", "Orta Taban"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A12", "Kelebek Benzerligi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A13", "Aciortay Benzerlik Iliskisi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A14", "Kenarortay Benzerlik Iliskisi"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A15", "Katlama Sorulari"),
    ("GEO-ACL25-K08", "GEO-ACL25-K08-A16", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A01", "Dar Acili Ucgenlerin Alani"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A02", "Dik Ucgenin Alani"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A03", "Genis Acili Ucgenlerin Alani"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A04", "Ozel Acili Ucgenlerin Alani"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A05", "Eskenar Ucgenin Alani"),
    (
        "GEO-ACL25-K09",
        "GEO-ACL25-K09-A06",
        "Yukseklikleri Esit Ucgenlerin Alanlari Orani",
    ),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A07", "Tabanlari Esit Ucgenlerin Alanlari Orani"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A08", "Esit Alanli Ucgenleri Gorme"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A09", "Ucgende Benzerlik Alan Iliskisi"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A10", "Ucgende Aciortay ve Alan Iliskisi"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A11", "Ucgende Kenarortay ve Alan Iliskisi"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A12", "Sinuslu Alan Formulu"),
    (
        "GEO-ACL25-K09",
        "GEO-ACL25-K09-A13",
        "Ozdes Ucgenlerle Olusturulan Alan Sorulari",
    ),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A14", "Katlama Kesme Sorulari"),
    ("GEO-ACL25-K09", "GEO-ACL25-K09-A15", "Sozel Olarak Ifade Edilmis Sorular"),
    (
        "GEO-ACL25-K10",
        "GEO-ACL25-K10-A01",
        "Acilarin Siralanisindan Hareketle Kenarlari Siralama",
    ),
    ("GEO-ACL25-K10", "GEO-ACL25-K10-A02", "Ucgen Esitsizligi"),
    ("GEO-ACL25-K10", "GEO-ACL25-K10-A03", "Dar ya da Genis Aci Karsisindaki Kenar"),
    ("GEO-ACL25-K10", "GEO-ACL25-K10-A04", "Ic Bolgede Alinan Nokta"),
    ("GEO-ACL25-K10", "GEO-ACL25-K10-A05", "Katlama Sorulari"),
    ("GEO-ACL25-K10", "GEO-ACL25-K10-A06", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K11", "GEO-ACL25-K11-A01", "Bir Ucgenin Kenarorta Dikmeleri"),
    ("GEO-ACL25-K11", "GEO-ACL25-K11-A02", "Bir Ucgenin Diklik Merkezi"),
    (
        "GEO-ACL25-K11",
        "GEO-ACL25-K11-A03",
        "Ic-Dis Teget Cemberin Merkezi, Agirlik Merkezi",
    ),
    ("GEO-ACL25-K11", "GEO-ACL25-K11-A04", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A01", "Ic Acilar Toplami ve Dis Acilar Toplami"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A02", "Cokgenlerde Aci Hesaplama"),
    (
        "GEO-ACL25-K12",
        "GEO-ACL25-K12-A03",
        "Duzgun Cokgenlerde Ic Aci ve Dis Acinin Hesaplanmasi",
    ),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A04", "Duzgun Besgende Aci Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A05", "Duzgun Altigende Aci Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A06", "Duzgun Sekizgende Aci Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A07", "Ortak Kenari Olan Duzgun Cokgenler"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A08", "Kenar Sayisi Bilinmeyen Duzgun Cokgenler"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A09", "Duzgun Cokgenlerde Katlama Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A10", "Duzgun Besgende Uzunluk Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A11", "Duzgun Altigende Uzunluk Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A12", "Duzgun Altigende Alan Sorulari"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A13", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K12", "GEO-ACL25-K12-A14", "Kesme Sorulari"),
    ("GEO-ACL25-K13", "GEO-ACL25-K13-A01", "Dortgenlerde Aci"),
    (
        "GEO-ACL25-K13",
        "GEO-ACL25-K13-A02",
        "Dortgenlerde Aciortaylarin Olusturdugu Acilar",
    ),
    (
        "GEO-ACL25-K13",
        "GEO-ACL25-K13-A03",
        "Pisagor Teoreminin Dortgenlerde Kullanilmasi",
    ),
    (
        "GEO-ACL25-K13",
        "GEO-ACL25-K13-A04",
        "Dortgenin Kosegenleri ile Orta Noktalar Dortgeni Arasindaki Iliski",
    ),
    ("GEO-ACL25-K13", "GEO-ACL25-K13-A05", "Ozel Ucgenler Olusturma"),
    ("GEO-ACL25-K13", "GEO-ACL25-K13-A06", "Dortgenin Alani"),
    ("GEO-ACL25-K13", "GEO-ACL25-K13-A07", "Katlama Sorulari"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A01", "Yamukta Aci"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A02", "Yamugun Orta Tabani"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A03", "Komsu Iki Acinin Aciortayi"),
    (
        "GEO-ACL25-K14",
        "GEO-ACL25-K14-A04",
        "Yamukta Temel Benzerlik Kurali ve Kelebek Benzerligi",
    ),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A05", "Dik Yamuk"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A06", "Ikizkenar Yamuk"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A07", "Yamugun Alani 1"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A08", "Yamugun Alani 2"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A09", "Yamugun Alani 3"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A10", "Kosegenlerin Olusturdugu Alanlar"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A11", "Dik Yamuk ve Ikizkenar Yamugun Alani"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A12", "Ozdes Yamuklarla Olusturulan Sekiller"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A13", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K14", "GEO-ACL25-K14-A14", "Katlama Sorulari"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A01", "Paralelkenarda Aci"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A02", "Aciortayin Olusturdugu Ikizkenar Ucgen"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A03", "Aciortaylarin Olusturdugu Dik Ucgen 1"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A04", "Aciortaylarin Olusturdugu Dik Ucgen 2"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A05", "Kosegenlerin Birbirini Ortalamasi"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A06", "Paralelkenarda Benzerlik 1"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A07", "Paralelkenarda Benzerlik 2"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A08", "Paralelkenarda Benzerlik 3"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A09", "Paralelkenarda Alan"),
    (
        "GEO-ACL25-K15",
        "GEO-ACL25-K15-A10",
        "Paralelkenar ve Icine Cizilen Yamugun Alani",
    ),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A11", "Kosegenin Olusturdugu Esit Yukseklikler"),
    (
        "GEO-ACL25-K15",
        "GEO-ACL25-K15-A12",
        "Kenar Uzerindeki Bir Nokta Karsi Koselerle Birlestirilince Olusan Ucgenin Alani",
    ),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A13", "Kelebek Benzerligi ile Alan"),
    (
        "GEO-ACL25-K15",
        "GEO-ACL25-K15-A14",
        "Ic Bolgedeki Noktanin Koselerle Olusturdugu Ucgenlerin Alanlari",
    ),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A15", "Katlama Sorulari"),
    ("GEO-ACL25-K15", "GEO-ACL25-K15-A16", "Sozel Olarak Ifade Edilmis Sorular"),
    (
        "GEO-ACL25-K15",
        "GEO-ACL25-K15-A17",
        "Ozdes Paralelkenarlarla Olusturulmus Sekiller",
    ),
    ("GEO-ACL25-K16", "GEO-ACL25-K16-A01", "Eskenar Dortgende Aci"),
    ("GEO-ACL25-K16", "GEO-ACL25-K16-A02", "Eskenar Dortgenin Kenarlarinin Esitligi"),
    (
        "GEO-ACL25-K16",
        "GEO-ACL25-K16-A03",
        "Kosegenlerin Birbirini Dik Olarak Ortalamasi",
    ),
    ("GEO-ACL25-K16", "GEO-ACL25-K16-A04", "Eskenar Dortgenin Alani"),
    ("GEO-ACL25-K16", "GEO-ACL25-K16-A05", "Katlama Sorulari"),
    (
        "GEO-ACL25-K16",
        "GEO-ACL25-K16-A06",
        "Ozdes Eskenar Dortgenlerle olusturulan Sekiller",
    ),
    ("GEO-ACL25-K16", "GEO-ACL25-K16-A07", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A01", "Deltoidde Aci"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A02", "Deltoidin Ozellikleri 1"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A03", "Deltoidin Ozellikleri 2"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A04", "Deltoidin Alani"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A05", "Deltoidde Benzerlik"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A06", "Katlama Sorulari"),
    ("GEO-ACL25-K17", "GEO-ACL25-K17-A07", "Ozdes Deltoitlerle Sekiller Olusturma"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A01", "Dikdortgende Aci"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A02", "Dikdortgenin Temel Ozellikleri"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A03", "Dikdortgende Benzerlik 1"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A04", "Dikdortgende Benzerlik 2"),
    (
        "GEO-ACL25-K18",
        "GEO-ACL25-K18-A05",
        "Dikdortgende Kosegenlerin Esitligi ve Birbirini Ortalamasi",
    ),
    (
        "GEO-ACL25-K18",
        "GEO-ACL25-K18-A06",
        "Dikdortgenin Ic Bolgesindeki Noktanin Koselere Uzakliklari",
    ),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A07", "Dikdortgenin Alani"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A08", "Dikdortgende Alan Paylasimi"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A09", "Dikdortgende Benzerlik ve Alan Iliskisi"),
    (
        "GEO-ACL25-K18",
        "GEO-ACL25-K18-A10",
        "Ozdes Dikdortgenlerle Olusturulan Sekiller",
    ),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A11", "Katlama Sorulari"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A12", "Kesme Sorulari"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A13", "Dondurme Sorulari"),
    ("GEO-ACL25-K18", "GEO-ACL25-K18-A14", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A01", "Karede Aci"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A02", "Karenin Temel Ozellikleri"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A03", "Kosegenin Aciortay Olusu"),
    (
        "GEO-ACL25-K19",
        "GEO-ACL25-K19-A04",
        "Kosegenlerin Esit Olup Birbirini Dik Olarak Ortalamasi",
    ),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A05", "Karede Benzerlik"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A06", "Karede Eslik"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A07", "Karede Alan Paylasimi"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A08", "Ozdes Karelerle Olusturulan Sekiller"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A09", "Katlama ve Kesme Sorulari"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A10", "Gorsel Yetenek Sorulari"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A11", "Dondurme Sorulari"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A12", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K19", "GEO-ACL25-K19-A13", "Yorum Sorulari"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A01", "Cemberde Merkez Aci"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A02", "Yaricaplarin Esitligi"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A03", "Kiris ve Yay Arasindaki Iliski"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A04", "Cemberde Cevre Aci"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A05", "Cemberde Capi Goren Cevre Aci"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A06", "Paralel Kirisler Arasindaki Yaylar"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A07", "Cemberde Teget-Kiris Aci"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A08", "Cemberde Ic Aci"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A09", "Cemberde Dis Aci 1"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A10", "Cemberde Dis Aci 2"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A11", "Cemberde Dis Aci 3"),
    ("GEO-ACL25-K20", "GEO-ACL25-K20-A12", "Katlama ve Kesme Sorulari"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A01", "Cemberin Yaricapini Gorme"),
    (
        "GEO-ACL25-K21",
        "GEO-ACL25-K21-A02",
        "Cemberin Merkezinden Kirise Indirilen Dikme",
    ),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A03", "En Uzun ve En Kisa Kiris"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A04", "Merkeze Uzakliklari Esit Olan Kirisler"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A05", "Cemberde Teget Ozellikleri"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A06", "Bir Noktadan Cembere Cizilen Iki Teget"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A07", "Bir Ucgenin Ic Teget Cemberi"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A08", "Bir Ucgenin Dis Teget Cemberi"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A09", "Birbirlerine Teget Olan Cemberler"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A10", "Cembere En Yakin ve En Uzak Olan Nokta"),
    (
        "GEO-ACL25-K21",
        "GEO-ACL25-K21-A11",
        "Benzerlikle Cozulen Cemberde Uzunluk Sorulari",
    ),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A12", "Katlama ve Kesme Sorulari"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A13", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K21", "GEO-ACL25-K21-A14", "Ozdes Cemberlerle Olusturulmus Sekiller"),
    ("GEO-ACL25-K22", "GEO-ACL25-K22-A01", "Yay Uzunlugu"),
    ("GEO-ACL25-K22", "GEO-ACL25-K22-A02", "Cemberin Cevresi"),
    ("GEO-ACL25-K22", "GEO-ACL25-K22-A03", "Yarim Cemberin Cevresi"),
    ("GEO-ACL25-K22", "GEO-ACL25-K22-A04", "Cembersel Hareket"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A01", "Dairenin Alani 1"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A02", "Dairenin Alani 2"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A03", "Halkanin Alani"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A04", "Yarim Dairenin Alani"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A05", "Daire Diliminin Alani"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A06", "Istenmeyen Bolgenin Alanini Cikarmak"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A07", "Merkez Acidan Hareketle Alan Hesaplama"),
    (
        "GEO-ACL25-K23",
        "GEO-ACL25-K23-A08",
        "Uygun Bolgelerin Alanlarini Isimlendirerek Alani Bulunabilir Geometrik Sekiller Elde Etme",
    ),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A09", "Pisagor ile Alan Bulma"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A10", "Daire Dilimlerinin Alanlari Orani"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A11", "Dairede Katlama"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A12", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A13", "Daire Icine Yerlestirilmis Es Sekiller"),
    ("GEO-ACL25-K23", "GEO-ACL25-K23-A14", "Ozdes Sekillerden Olusan Sorular"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A01", "Nokta ve Eksenlere Uzaklik"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A02", "Analitik Duzlemin Bolgeleri"),
    (
        "GEO-ACL25-K24",
        "GEO-ACL25-K24-A03",
        "Koselerinin Koordinatlari Verilen Cokgenler",
    ),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A04", "Analitik Duzlemde Ucgenlerin Benzerligi"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A05", "Ozdes Sekillerle Olusturulan Sorular"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A06", "Iki Nokta Arasindaki Uzaklik"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A07", "Orta Noktanin Koordinatlari"),
    (
        "GEO-ACL25-K24",
        "GEO-ACL25-K24-A08",
        "Dogru Parcasini Belirli Oranda Bolen Nokta",
    ),
    (
        "GEO-ACL25-K24",
        "GEO-ACL25-K24-A09",
        "Paralelkenarin Karsilikli Koseleri Arasindaki Iliski",
    ),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A10", "Ucgenin Agirlik Merkezinin Koordinatlari"),
    (
        "GEO-ACL25-K24",
        "GEO-ACL25-K24-A11",
        "Koselerinin Koordinatlari Verilen Ucgenlerin Alani",
    ),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A12", "Analitik Duzlemde Katlama"),
    ("GEO-ACL25-K24", "GEO-ACL25-K24-A13", "Sozel Olarak Ifade Edilmis Sorular"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A01", "Egim Acisi Verilen Dogrunun Egimi"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A02", "Iki Noktasi Verilen Dogrunun Egimi"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A03", "Dogru Uzerindeki Nokta"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A04", "Denklemi Verilen Dogrunun Egimi"),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A05",
        "Birbirine Paralel Dogrularin Egimleri Arasindaki Iliski",
    ),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A06",
        "Birbirine Dik Dogrularin Egimleri Arasindaki Iliski",
    ),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A07", "Dogrunun Eksenleri Kestigi Noktalar"),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A08",
        "Egimi ve Bir Noktasi Verilen Dogrunun Denklemi",
    ),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A09", "Orijinden Gecen Dogrunun Denklemi"),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A10",
        "Eksenleri Kestigi Noktalar Verilen Dogrunun Denklemi",
    ),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A11",
        "Eksenlere Paralel Dogrularin Denklemi ve Aciortay Dogrularinin Denklemi",
    ),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A12",
        "Katlama Sorularinda Dogru Denkleminin Bulunmasi",
    ),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A13", "Iki Dogrunun Birbirine Gore Durumlari 1"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A14", "Iki Dogrunun Birbirine Gore Durumlari 2"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A15", "Iki Dogrunun Birbirine Gore Durumlari 3"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A16", "Bir Noktanin Bir Dogruya Uzakligi"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A17", "Paralel Iki Dogru Arasindaki Uzaklik"),
    ("GEO-ACL25-K25", "GEO-ACL25-K25-A18", "Sekli Esit Alanli Iki Bolgeye Bolen Dogru"),
    (
        "GEO-ACL25-K25",
        "GEO-ACL25-K25-A19",
        "Birinci Dereceden Iki Bilinmeyenli Esitsizlikler",
    ),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A01", "Oteleme Donusumu"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A02", "Eksenlere Gore Yansima"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A03", "x = a ve y = b Dogrularina Gore Yansima"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A04", "y = x ve y = -x Dogrularina Gore Yansima"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A05", "Noktanin Noktaya Gore Yansimasi"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A06", "Noktanin Dogruya Gore Yansimasi"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A07", "Dogrunun Noktaya Gore Yansimasi"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A08", "Dogrunun Dogruya Gore Yansimasi"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A09", "Donme Donusumu 1"),
    ("GEO-ACL25-K26", "GEO-ACL25-K26-A10", "Donme Donusumu 2"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A01", "Dik Prizmanin Alan ve Hacmi (Sozel)"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A02", "Dik Prizmanin Alan ve Hacmi (Sekilli)"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A03", "Prizmada Dogru Parcasi"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A04", "Prizmada Cokgen"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A05", "Prizmanin Yuzey Alani"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A06", "Prizmanin Yuzey Alanindaki Degisim"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A07", "Prizmanin Icine Cisim Atma"),
    (
        "GEO-ACL25-K28",
        "GEO-ACL25-K28-A08",
        "Prizmanin Icindeki Suyun Yuksekligi ve Hacmi",
    ),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A09", "Prizmanin Alan ve Hacmi (Sozel Sorular)"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A10", "Prizmanin Acinimi"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A11", "Kartondan Kutu Yapma Sorulari"),
    ("GEO-ACL25-K28", "GEO-ACL25-K28-A12", "Prizmanin Yuzeyi Uzerinde Hareket"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A01", "Dik Dairesel Silindirde Uzunluk Hesaplama"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A02", "Dik Dairesel Silindirin Yanal Alani"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A03", "Dik Dairesel Silindirin Yuzey Alani"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A04", "Yuzey Alanindaki Degisim"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A05", "Dik Dairesel Silindirin Hacmi"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A06", "Birbirine Teget Olan Silindirler"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A07", "Dik Dairesel Silindirin Acinimi"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A08", "Silindir Yuzeyinde Hareket"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A09", "Dondurme Sonucunda Olusan Silindir"),
    ("GEO-ACL25-K29", "GEO-ACL25-K29-A10", "Silindir ile Ilgili Sozel Sorular"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A01", "Piramitte Uzunluk"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A02", "Piramidin Yuksekligi"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A03", "Piramidin Hacmi"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A04", "Piramidin Yanal ve Yuzey Alani"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A05", "Piramidin Acinimi"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A06", "Yeni Nesil Soru"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A07", "Piramitte Benzerlik ve Hacim Iliskisi"),
    (
        "GEO-ACL25-K30",
        "GEO-ACL25-K30-A08",
        "Piramidin Bir Yan Yuzunun Taban ile Yaptigi Aci",
    ),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A09", "Piramidin Yuzeyi Uzerinde Hareket"),
    ("GEO-ACL25-K30", "GEO-ACL25-K30-A10", "Duzgun Dortyuzlu"),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A01", "Dik Dairesel koninin Yanal ve Yuzey Alani"),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A02", "Dik Dairesel Koninin Hacmi"),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A03", "Konilerde Benzerlik Hacim Iliskisi"),
    (
        "GEO-ACL25-K31",
        "GEO-ACL25-K31-A04",
        "Dik Dairesel Koni ile Ilgili Sozel Sorular",
    ),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A05", "Dik Dairesel Koninin Acinimi"),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A06", "Tabanlari Cakisik Koniler"),
    ("GEO-ACL25-K31", "GEO-ACL25-K31-A07", "En Kisa Yol Sorulari"),
    ("GEO-ACL25-K32", "GEO-ACL25-K32-A01", "Kurenin Alani"),
    ("GEO-ACL25-K32", "GEO-ACL25-K32-A02", "Kurenin Hacmi"),
    ("GEO-ACL25-K33", "GEO-ACL25-K33-A01", "Cemberin Standart Denklemi"),
    (
        "GEO-ACL25-K33",
        "GEO-ACL25-K33-A02",
        "Koordinat Duzleminde Verilen Cemberin Standart Denklemi",
    ),
    ("GEO-ACL25-K33", "GEO-ACL25-K33-A03", "Eksenlere Teget Olan Cemberler"),
    (
        "GEO-ACL25-K33",
        "GEO-ACL25-K33-A04",
        "Koordinat Duzleminde Eksenlere Teget Olan Cemberler",
    ),
    ("GEO-ACL25-K33", "GEO-ACL25-K33-A05", "Cemberin Genel Denklemi 1"),
    ("GEO-ACL25-K33", "GEO-ACL25-K33-A06", "Cemberin Genel Denklemi 2"),
    (
        "GEO-ACL25-K33",
        "GEO-ACL25-K33-A07",
        "Cember ve Dogrunun Birbirine Gore Durumlari 1",
    ),
    (
        "GEO-ACL25-K33",
        "GEO-ACL25-K33-A08",
        "Cember ve Dogrunun Birbirine Gore Durumlari 2",
    ),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'GEOMETRI', TRUE, now(), now())
    """
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

_ACIKLAMA = (
    "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi'nin sayfa basliklari ve sari "
    "alt baslik kutularindan uretildi; icindekiler yakalamada yok (0041)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0041] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0041] mv_safe_for_beta yenilendi")


def _yaz(b, kod, ad, level, parent_id) -> str:
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
        },
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608
            "VALUES (:id, :kod, TRUE)"
        ),
        {"id": yeni_id, "kod": kod},
    )
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0041] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": GEO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0041] %s kok konusu yok -- atlandi", GEO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz GEO-ACL25 deseni; GEO-ACL24 (ayni yayinevinin baska kitabi) dahil
    # mevcut agaclara DOKUNULMAZ. LIKE deseni '-' ile biter ki GEO-ACL250 gibi
    # bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    kimlik: dict[str, str] = {}

    def _id_al(kod: str) -> str:
        mevcut_id: str = b.execute(
            sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
        ).scalar_one()
        return mevcut_id

    eklenen = 0
    for kod, ad in KONULAR:
        if kod in mevcut:
            kimlik[kod] = _id_al(kod)
            continue
        kimlik[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, kod, ad in ALT_KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, kimlik[ust])
        eklenen += 1

    _log.info(
        "[0041] %s konu + %s alt konu tanimi; bu kosumda eklenen dugum: %s",
        len(KONULAR),
        len(ALT_KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0041] %s yok -- downgrade atlandi", GUNLUK)
        return
    idler = [
        r[0]
        for r in b.execute(
            sa.text(f"SELECT id FROM {GUNLUK} WHERE olusturuldu IS TRUE")  # noqa: S608  # nosec B608
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
                "[0041] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar (alt konu), sonra konular: cocugu olan silinmez.
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
    _log.info("[0041] downgrade tamam; silinmeye aday dugum: %s", len(idler))
