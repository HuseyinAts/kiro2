"""
Zone of Proximal Development + MEB Maarif Modeli
Türk eğitim kültürüne uyarlanmış ZPD sistemi - DEVRİMSEL

Bu modül Vygotsky'nin ZPD teorisini MEB Maarif modeli ile birleştirerek
Türk öğrenci psikolojisine özel bir öğrenme aralığı hesaplama sistemi sunar.

DEVRİMSEL ÖZELLİKLER:
- Türk kültürü faktörleri entegrasyonu
- MEB Maarif değerleri uyum sistemi
- Grup vs bireysel öğrenme dengeleme
- Kültürel bağlam farkındalıklı ZPD hesaplama
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class MaarifDegeri(str, Enum):
    """MEB Maarif Modeli Değerleri"""

    # Milli Değerler
    VATAN_SEVGISI = "vatan_sevgisi"
    MILLET_BILINCI = "millet_bilinci"
    AILE_BIRLIGI = "aile_birligi"
    BAYRAK_SEVGISI = "bayrak_sevgisi"
    ISTIKLAL_RUHU = "istiklal_ruhu"

    # Evrensel Değerler
    ADALET = "adalet"
    DOSTLUK = "dostluk"
    DURUSTLUK = "durustluk"
    OZGURLUK = "ozgurluk"
    ESITLIK = "esitlik"
    BARIŞ = "baris"

    # Kök Değerler
    SABIR = "sabir"
    SAYGI = "saygi"
    SEVGI = "sevgi"
    SORUMLULUK = "sorumluluk"
    DUYARLILIK = "duyarlilik"
    HOSGORU = "hosgoru"


class TurkKulturFaktoru(str, Enum):
    """Türk Öğrenci Kültürü Faktörleri"""

    GRUP_CALISMASI_TERCIHI = "grup_calismasi_tercihi"
    OGRETMENE_SAYGI = "ogretmene_saygi"
    AILE_KATILIMI = "aile_katilimi"
    AKRAN_REKABETI = "akran_rekabeti"
    OTORITE_KABULU = "otorite_kabulu"
    TOPLUMSAL_ONAY = "toplumsal_onay"
    BASARI_ODAKLILIK = "basari_odaklilik"
    KOLEKTIF_KIMLIK = "kolektif_kimlik"


class ZPDSeviyesi(str, Enum):
    """ZPD Zorluk Seviyeleri"""

    COK_KOLAY = "cok_kolay"  # Mevcut seviyenin altı
    KOLAY = "kolay"  # Mevcut seviye
    OPTIMAL = "optimal"  # ZPD içi - ideal zorluk
    ZOR = "zor"  # ZPD üst sınırı
    COK_ZOR = "cok_zor"  # ZPD dışı - çok zor


class KulturelBaglamProfili(BaseModel):
    """Türk öğrenci kültürel bağlam profili"""

    ogrenci_id: str

    # Kültürel faktör skorları (0.0 - 1.0)
    grup_calismasi_tercihi: float = Field(ge=0.0, le=1.0, default=0.7)
    ogretmene_saygi_seviyesi: float = Field(ge=0.0, le=1.0, default=0.8)
    aile_katilim_derecesi: float = Field(ge=0.0, le=1.0, default=0.6)
    akran_rekabet_egilimi: float = Field(ge=0.0, le=1.0, default=0.5)
    otorite_kabul_seviyesi: float = Field(ge=0.0, le=1.0, default=0.7)
    toplumsal_onay_ihtiyaci: float = Field(ge=0.0, le=1.0, default=0.6)
    basari_odaklilik: float = Field(ge=0.0, le=1.0, default=0.8)
    kolektif_kimlik_gucu: float = Field(ge=0.0, le=1.0, default=0.7)

    # Demografik faktörler
    bolge: Optional[str] = None  # Coğrafi bölge
    sosyoekonomik_durum: Optional[str] = None
    okul_turu: Optional[str] = None  # Devlet/özel

    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    guncelleme_tarihi: datetime = Field(default_factory=datetime.now)

    @field_validator(
        "grup_calismasi_tercihi",
        "ogretmene_saygi_seviyesi",
        "aile_katilim_derecesi",
        "akran_rekabet_egilimi",
        "otorite_kabul_seviyesi",
        "toplumsal_onay_ihtiyaci",
        "basari_odaklilik",
        "kolektif_kimlik_gucu",
    )
    @classmethod
    def validate_scores(cls, v):
        """Skor değerlerinin 0-1 arasında olduğunu doğrula"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Kültürel faktör skorları 0.0-1.0 arasında olmalıdır")
        return v


class MaarifDegerleriProfili(BaseModel):
    """MEB Maarif değerleri profili"""

    ogrenci_id: str

    # Milli değerler (0.0 - 1.0)
    vatan_sevgisi: float = Field(ge=0.0, le=1.0, default=0.8)
    millet_bilinci: float = Field(ge=0.0, le=1.0, default=0.7)
    aile_birligi: float = Field(ge=0.0, le=1.0, default=0.9)
    bayrak_sevgisi: float = Field(ge=0.0, le=1.0, default=0.8)
    istiklal_ruhu: float = Field(ge=0.0, le=1.0, default=0.7)

    # Evrensel değerler (0.0 - 1.0)
    adalet: float = Field(ge=0.0, le=1.0, default=0.8)
    dostluk: float = Field(ge=0.0, le=1.0, default=0.9)
    durustluk: float = Field(ge=0.0, le=1.0, default=0.8)
    ozgurluk: float = Field(ge=0.0, le=1.0, default=0.7)
    esitlik: float = Field(ge=0.0, le=1.0, default=0.8)
    baris: float = Field(ge=0.0, le=1.0, default=0.9)

    # Kök değerler (0.0 - 1.0)
    sabir: float = Field(ge=0.0, le=1.0, default=0.7)
    saygi: float = Field(ge=0.0, le=1.0, default=0.9)
    sevgi: float = Field(ge=0.0, le=1.0, default=0.8)
    sorumluluk: float = Field(ge=0.0, le=1.0, default=0.8)
    duyarlilik: float = Field(ge=0.0, le=1.0, default=0.7)
    hosgoru: float = Field(ge=0.0, le=1.0, default=0.8)

    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    guncelleme_tarihi: datetime = Field(default_factory=datetime.now)

    def get_milli_degerler_ortalamasi(self) -> float:
        """Milli değerlerin ortalamasını hesapla"""
        return (
            self.vatan_sevgisi
            + self.millet_bilinci
            + self.aile_birligi
            + self.bayrak_sevgisi
            + self.istiklal_ruhu
        ) / 5

    def get_evrensel_degerler_ortalamasi(self) -> float:
        """Evrensel değerlerin ortalamasını hesapla"""
        return (
            self.adalet
            + self.dostluk
            + self.durustluk
            + self.ozgurluk
            + self.esitlik
            + self.baris
        ) / 6

    def get_kok_degerler_ortalamasi(self) -> float:
        """Kök değerlerin ortalamasını hesapla"""
        return (
            self.sabir
            + self.saygi
            + self.sevgi
            + self.sorumluluk
            + self.duyarlilik
            + self.hosgoru
        ) / 6


class TurkZPDAraligi(BaseModel):
    """Türk eğitim kültürüne uyarlanmış ZPD aralığı"""

    ogrenci_id: str
    konu: str

    # ZPD sınırları
    mevcut_seviye: float = Field(ge=0.0, le=10.0)
    alt_sinir: float = Field(ge=0.0, le=10.0)
    ust_sinir: float = Field(ge=0.0, le=10.0)
    optimal_zorluk: float = Field(ge=0.0, le=10.0)

    # Kültürel ayarlamalar
    kulturel_carpan: float = Field(ge=0.5, le=2.0, default=1.0)
    maarif_uyum_katsayisi: float = Field(ge=0.0, le=1.0, default=0.8)
    grup_calismasi_bonusu: float = Field(ge=0.0, le=0.5, default=0.0)
    ogretmen_rehberlik_faktoru: float = Field(ge=0.0, le=0.3, default=0.0)

    # Güven seviyeleri
    hesaplama_guveni: float = Field(ge=0.0, le=1.0, default=0.8)
    kulturel_uyum_guveni: float = Field(ge=0.0, le=1.0, default=0.7)

    hesaplama_tarihi: datetime = Field(default_factory=datetime.now)
    gecerlilik_suresi_gun: int = Field(default=7)  # 1 hafta geçerli

    @field_validator("alt_sinir", "ust_sinir", "optimal_zorluk")
    @classmethod
    def validate_zpd_bounds(cls, v, values):
        """ZPD sınırlarının mantıklı olduğunu doğrula"""
        if "mevcut_seviye" in values:
            mevcut = values["mevcut_seviye"]
            if v < mevcut - 2 or v > mevcut + 5:
                raise ValueError("ZPD sınırları mevcut seviyeye göre mantıksız")
        return v

    def is_gecerli(self) -> bool:
        """ZPD hesaplamasının hala geçerli olup olmadığını kontrol et"""
        gecen_gun = (datetime.now() - self.hesaplama_tarihi).days
        return gecen_gun <= self.gecerlilik_suresi_gun

    def get_zorluk_seviyesi(self, hedef_zorluk: float) -> ZPDSeviyesi:
        """Hedef zorluğun ZPD içindeki seviyesini belirle"""
        if hedef_zorluk < self.alt_sinir:
            return ZPDSeviyesi.COK_KOLAY
        elif hedef_zorluk < self.mevcut_seviye:
            return ZPDSeviyesi.KOLAY
        elif hedef_zorluk <= self.optimal_zorluk:
            return ZPDSeviyesi.OPTIMAL
        elif hedef_zorluk <= self.ust_sinir:
            return ZPDSeviyesi.ZOR
        else:
            return ZPDSeviyesi.COK_ZOR


class ZPDHesaplamaParametreleri(BaseModel):
    """ZPD hesaplama parametreleri"""

    # Temel ZPD parametreleri
    temel_zpd_genisligi: float = Field(default=0.3, ge=0.1, le=1.0)
    optimal_zorluk_orani: float = Field(default=0.7, ge=0.5, le=0.9)

    # Türk kültürü ağırlıkları
    grup_calismasi_agirligi: float = Field(default=0.2, ge=0.0, le=0.5)
    ogretmen_saygi_agirligi: float = Field(default=0.15, ge=0.0, le=0.3)
    aile_katilim_agirligi: float = Field(default=0.1, ge=0.0, le=0.2)
    akran_rekabet_agirligi: float = Field(default=0.1, ge=0.0, le=0.2)

    # MEB Maarif ağırlıkları
    milli_degerler_agirligi: float = Field(default=0.15, ge=0.0, le=0.3)
    evrensel_degerler_agirligi: float = Field(default=0.1, ge=0.0, le=0.2)
    kok_degerler_agirligi: float = Field(default=0.2, ge=0.0, le=0.4)

    # Dinamik ayarlama parametreleri
    basari_artis_carpani: float = Field(default=1.1, ge=1.0, le=1.5)
    basarisizlik_azalma_carpani: float = Field(default=0.9, ge=0.5, le=1.0)
    motivasyon_faktoru: float = Field(default=0.05, ge=0.0, le=0.2)


class ZPDHesaplamaGecmisi(BaseModel):
    """ZPD hesaplama geçmişi"""

    ogrenci_id: str
    konu: str
    hesaplama_tarihi: datetime

    # Hesaplama sonuçları
    zpd_araligi: TurkZPDAraligi
    kullanilan_parametreler: ZPDHesaplamaParametreleri
    kulturel_profil: KulturelBaglamProfili
    maarif_profili: MaarifDegerleriProfili

    # Performans verileri
    onceki_basari_orani: Optional[float] = None
    sonraki_basari_orani: Optional[float] = None
    tahmin_dogrulugu: Optional[float] = None

    notlar: Optional[str] = None


class ZPDOptimizasyonSonucu(BaseModel):
    """ZPD optimizasyon sonucu"""

    ogrenci_id: str
    konu: str

    # Önerilen ayarlamalar
    onerilen_zorluk_seviyesi: float
    onerilen_ogrenme_yontemi: str
    grup_calismasi_onerisi: bool
    ogretmen_rehberlik_ihtiyaci: bool

    # Kişiselleştirme önerileri
    icerik_turu_onerileri: List[str]
    ogrenme_hizi_ayarlama: float
    motivasyon_stratejileri: List[str]

    # Güven metrikleri
    oneri_guveni: float = Field(ge=0.0, le=1.0)
    beklenen_basari_artisi: float = Field(ge=0.0, le=1.0)

    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
