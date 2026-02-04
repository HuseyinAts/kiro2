"""
Dashboard veri modelleri
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardIstatistikleri(BaseModel):
    """Dashboard istatistikleri modeli"""

    tamamlanan_dersler: int = Field(..., description="Tamamlanan ders sayısı")
    toplam_dersler: int = Field(..., description="Toplam ders sayısı")
    tamamlanan_sinavlar: int = Field(..., description="Tamamlanan sınav sayısı")
    ortalama_puan: float = Field(..., description="Ortalama sınav puanı")
    toplam_calisma_suresi: int = Field(
        ..., description="Toplam çalışma süresi (dakika)"
    )
    haftalik_hedef: int = Field(..., description="Haftalık çalışma hedefi (dakika)")
    haftalik_ilerleme: int = Field(..., description="Bu hafta çalışma süresi (dakika)")
    gunluk_seri: int = Field(..., description="Günlük çalışma serisi")
    toplam_puan: int = Field(..., description="Toplam kazanılan puan")
    seviye: int = Field(..., description="Öğrenci seviyesi")
    deneyim: int = Field(..., description="Mevcut deneyim puanı")
    sonraki_seviye_deneyim: int = Field(
        ..., description="Sonraki seviye için gereken deneyim"
    )


class SinavSonucu(BaseModel):
    """Sınav sonucu modeli"""

    sinav_id: str = Field(..., description="Sınav ID")
    sinav_adi: str = Field(..., description="Sınav adı")
    sinav_tipi: str = Field(..., description="Sınav türü (TYT, AYT, YDT)")
    tarih: datetime = Field(..., description="Sınav tarihi")
    puan: float = Field(..., description="Alınan puan")
    dogru_sayisi: int = Field(..., description="Doğru cevap sayısı")
    yanlis_sayisi: int = Field(..., description="Yanlış cevap sayısı")
    bos_sayisi: int = Field(..., description="Boş cevap sayısı")
    sure: int = Field(..., description="Sınav süresi (dakika)")
    konu_performanslari: Dict[str, float] = Field(
        default_factory=dict, description="Konu bazlı performanslar"
    )


class Hedef(BaseModel):
    """Öğrenci hedefi modeli"""

    hedef_id: str = Field(..., description="Hedef ID")
    baslik: str = Field(..., description="Hedef başlığı")
    aciklama: Optional[str] = Field(None, description="Hedef açıklaması")
    hedef_tipi: str = Field(..., description="Hedef türü (gunluk, haftalik, aylik)")
    hedef_degeri: float = Field(..., description="Hedef değeri")
    mevcut_deger: float = Field(..., description="Mevcut değer")
    baslangic_tarihi: datetime = Field(..., description="Başlangıç tarihi")
    bitis_tarihi: datetime = Field(..., description="Bitiş tarihi")
    durum: str = Field(..., description="Hedef durumu (aktif, tamamlandi, iptal)")
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)


class Bildirim(BaseModel):
    """Bildirim modeli"""

    bildirim_id: str = Field(..., description="Bildirim ID")
    baslik: str = Field(..., description="Bildirim başlığı")
    mesaj: str = Field(..., description="Bildirim mesajı")
    tip: str = Field(..., description="Bildirim türü (basari, uyari, bilgi, hata)")
    okundu: bool = Field(False, description="Okunma durumu")
    tarih: datetime = Field(default_factory=datetime.now)
    eylem_url: Optional[str] = Field(None, description="Eylem URL'si")


class PerformansVerisi(BaseModel):
    """Performans verisi modeli"""

    tarih: str = Field(..., description="Tarih")
    dersler: int = Field(..., description="Tamamlanan ders sayısı")
    sinavlar: int = Field(..., description="Tamamlanan sınav sayısı")
    puan: int = Field(..., description="Günlük kazanılan puan")
    calisma_suresi: int = Field(..., description="Çalışma süresi (dakika)")


class ProfilGuncelleme(BaseModel):
    """Profil güncelleme modeli"""

    ad_soyad: Optional[str] = Field(None, description="Ad soyad")
    telefon: Optional[str] = Field(None, description="Telefon numarası")
    sinif_seviyesi: Optional[int] = Field(
        None, ge=9, le=12, description="Sınıf seviyesi"
    )
    okul_adi: Optional[str] = Field(None, description="Okul adı")
    hedef_universiteler: Optional[List[str]] = Field(
        None, description="Hedef üniversiteler"
    )
    gunluk_calisma_hedefi: Optional[int] = Field(
        None, ge=30, le=600, description="Günlük çalışma hedefi"
    )
