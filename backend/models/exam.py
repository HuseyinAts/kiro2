"""
Sınav sistemi veri modelleri
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import SinavDurumu, SinavTipi, ZorlukSeviyesi


class SinavSorusu(BaseModel):
    """Sınav sorusu modeli"""

    soru_id: str = Field(..., description="Benzersiz soru ID")
    soru_metni: str = Field(..., description="Soru metni")
    secenekler: List[str] = Field(
        ..., min_items=4, max_items=5, description="Soru seçenekleri"
    )
    dogru_cevap: str = Field(..., description="Doğru cevap (A, B, C, D, E)")
    konu: str = Field(..., description="Soru konusu")
    alt_konu: Optional[str] = Field(None, description="Alt konu")
    zorluk_seviyesi: ZorlukSeviyesi = Field(..., description="Zorluk seviyesi")
    cozum_aciklamasi: Optional[str] = Field(None, description="Çözüm açıklaması")

    # ÖSYM Uyumluluk
    sinav_tipi: SinavTipi = Field(..., description="Hangi sınav türü için uygun")
    mufredat_kodu: Optional[str] = Field(None, description="MEB müfredat kodu")

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    guncelleme_tarihi: datetime = Field(default_factory=datetime.now)
    aktif: bool = Field(True, description="Soru aktif durumu")

    class Config:
        from_attributes = True


class SinavOturumu(BaseModel):
    """Sınav oturum modeli"""

    sinav_id: str = Field(..., description="Benzersiz sınav ID")
    ogrenci_id: str = Field(..., description="Sınava giren öğrenci ID")
    sinav_tipi: SinavTipi = Field(..., description="Sınav türü")

    # Sınav Konfigürasyonu
    toplam_soru_sayisi: int = Field(..., description="Toplam soru sayısı")
    sure_dakika: int = Field(..., description="Sınav süresi (dakika)")
    soru_listesi: List[str] = Field(..., description="Sınav sorularının ID listesi")

    # Durum Takibi
    durum: SinavDurumu = Field(SinavDurumu.HAZIR, description="Sınav durumu")
    baslangic_zamani: Optional[datetime] = Field(None, description="Başlangıç zamanı")
    bitis_zamani: Optional[datetime] = Field(None, description="Bitiş zamanı")
    kalan_sure: Optional[int] = Field(None, description="Kalan süre (saniye)")

    # İlerleme
    mevcut_soru_index: int = Field(0, description="Mevcut soru indeksi")
    cevaplanan_sorular: Dict[str, str] = Field(
        default_factory=dict, description="Cevaplanan sorular"
    )
    isaretlenen_sorular: List[str] = Field(
        default_factory=list, description="İşaretlenen sorular"
    )

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class SinavCevabi(BaseModel):
    """Sınav cevap modeli"""

    sinav_id: str = Field(..., description="Sınav ID")
    soru_id: str = Field(..., description="Soru ID")
    ogrenci_cevabi: Optional[str] = Field(None, description="Öğrenci cevabı")
    cevap_zamani: datetime = Field(default_factory=datetime.now)
    cevap_suresi: Optional[int] = Field(None, description="Cevaplama süresi (saniye)")

    class Config:
        from_attributes = True


class KonuPerformansi(BaseModel):
    """Konu bazlı performans modeli"""

    konu: str = Field(..., description="Konu adı")
    toplam_soru: int = Field(..., description="Toplam soru sayısı")
    dogru_sayisi: int = Field(..., description="Doğru cevap sayısı")
    yanlis_sayisi: int = Field(..., description="Yanlış cevap sayısı")
    bos_sayisi: int = Field(..., description="Boş cevap sayısı")
    basari_yuzdesi: float = Field(..., description="Başarı yüzdesi")
    ortalama_sure: Optional[float] = Field(
        None, description="Ortalama cevaplama süresi"
    )


class SinavSonucu(BaseModel):
    """Sınav sonuç modeli"""

    sonuc_id: str = Field(..., description="Benzersiz sonuç ID")
    sinav_id: str = Field(..., description="Sınav ID")
    ogrenci_id: str = Field(..., description="Öğrenci ID")
    sinav_tipi: SinavTipi = Field(..., description="Sınav türü")

    # Temel Sonuçlar
    toplam_soru: int = Field(..., description="Toplam soru sayısı")
    dogru_sayisi: int = Field(..., description="Doğru cevap sayısı")
    yanlis_sayisi: int = Field(..., description="Yanlış cevap sayısı")
    bos_sayisi: int = Field(..., description="Boş cevap sayısı")
    net_sayisi: float = Field(..., description="Net sayısı")
    ham_puan: float = Field(..., description="Ham puan")

    # Detaylı Analiz
    konu_performanslari: List[KonuPerformansi] = Field(default_factory=list)
    zorluk_dagilimi: Dict[str, int] = Field(default_factory=dict)
    zaman_analizi: Dict[str, float] = Field(default_factory=dict)

    # Karşılaştırma Verileri
    sinif_ortalamasi: Optional[float] = Field(None, description="Sınıf ortalaması")
    okul_ortalamasi: Optional[float] = Field(None, description="Okul ortalaması")
    ulusal_ortalama: Optional[float] = Field(None, description="Ulusal ortalama")
    basari_sirasi: Optional[int] = Field(None, description="Başarı sırası")

    # Öneriler ve Analiz
    zayif_konular: List[str] = Field(default_factory=list)
    guclu_konular: List[str] = Field(default_factory=list)
    calisma_onerileri: List[str] = Field(default_factory=list)

    # Meta Veriler
    analiz_tarihi: datetime = Field(default_factory=datetime.now)
    gecerli: bool = Field(True, description="Sonuç geçerliliği")

    class Config:
        from_attributes = True


class PerformansRaporu(BaseModel):
    """Kapsamlı performans raporu"""

    ogrenci_id: str = Field(..., description="Öğrenci ID")
    rapor_donemi: str = Field(..., description="Rapor dönemi")

    # Genel İstatistikler
    toplam_sinav_sayisi: int = Field(..., description="Toplam sınav sayısı")
    ortalama_net: float = Field(..., description="Ortalama net sayısı")
    gelisim_trendi: str = Field(..., description="Gelişim trendi (artan/azalan/sabit)")

    # Konu Bazlı Analiz
    en_basarili_konular: List[str] = Field(default_factory=list)
    en_zayif_konular: List[str] = Field(default_factory=list)
    gelisim_gosteren_konular: List[str] = Field(default_factory=list)

    # Karşılaştırmalı Pozisyon
    sinif_sirasi: Optional[int] = Field(None)
    okul_sirasi: Optional[int] = Field(None)
    ulusal_yuzdelik: Optional[float] = Field(None)

    # Öneriler
    oncelikli_calisma_alanlari: List[str] = Field(default_factory=list)
    onerilen_kaynak_turleri: List[str] = Field(default_factory=list)
    hedef_net_sayilari: Dict[str, float] = Field(default_factory=dict)

    # Meta Veriler
    rapor_tarihi: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
