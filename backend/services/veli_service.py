"""
Veli takip sistemi servisi
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from models.dashboard import Bildirim
from services.user_service import kullanici_servisi


class VeliRaporu(BaseModel):
    """Veli için haftalık rapor modeli"""

    rapor_id: str = Field(..., description="Rapor ID")
    ogrenci_id: str = Field(..., description="Öğrenci ID")
    ogrenci_ad_soyad: str = Field(..., description="Öğrenci adı soyadı")
    rapor_donemi: str = Field(..., description="Rapor dönemi")
    baslangic_tarihi: datetime = Field(..., description="Dönem başlangıç tarihi")
    bitis_tarihi: datetime = Field(..., description="Dönem bitiş tarihi")

    # Genel İstatistikler
    toplam_calisma_suresi: int = Field(
        ..., description="Toplam çalışma süresi (dakika)"
    )
    tamamlanan_sinav_sayisi: int = Field(..., description="Tamamlanan sınav sayısı")
    ortalama_basari_orani: float = Field(..., description="Ortalama başarı oranı (%)")

    # Performans Verileri
    en_basarili_konular: List[str] = Field(
        default_factory=list, description="En başarılı konular"
    )
    gelisim_gereken_konular: List[str] = Field(
        default_factory=list, description="Gelişim gereken konular"
    )
    haftalik_ilerleme: str = Field(..., description="Haftalık ilerleme durumu")

    # Öneriler
    veli_onerileri: List[str] = Field(
        default_factory=list, description="Veli için öneriler"
    )
    destek_alanlari: List[str] = Field(
        default_factory=list, description="Destek alınması gereken alanlar"
    )

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class VeliOnayTalebi(BaseModel):
    """Veli onay talebi modeli"""

    talep_id: str = Field(..., description="Talep ID")
    ogrenci_id: str = Field(..., description="Öğrenci ID")
    veli_id: str = Field(..., description="Veli ID")
    talep_tipi: str = Field(..., description="Talep türü")
    talep_aciklamasi: str = Field(..., description="Talep açıklaması")
    durum: str = Field("beklemede", description="Onay durumu")
    talep_tarihi: datetime = Field(default_factory=datetime.now)
    yanit_tarihi: Optional[datetime] = Field(None, description="Yanıt tarihi")
    veli_notu: Optional[str] = Field(None, description="Veli notu")

    class Config:
        from_attributes = True


class VeliServisi:
    """Veli takip sistemi servisi"""

    def __init__(self):
        # In-memory veri saklama (production'da database kullanılacak)
        self.veli_raporlari: Dict[str, VeliRaporu] = {}
        self.veli_onay_talepleri: Dict[str, VeliOnayTalebi] = {}
        self.veli_bildirimleri: Dict[str, List[Bildirim]] = {}
        self.cocuk_performans_verileri: Dict[str, Dict] = {}

    async def veli_cocuklarini_getir(self, veli_id: str) -> List[Dict[str, Any]]:
        """Velinin çocuklarının listesini getir"""
        try:
            # Veli profilini getir
            veli_profili = await kullanici_servisi.veli_profili_getir(veli_id)
            if not veli_profili:
                raise ValueError("Veli profili bulunamadı")

            cocuklar = []
            for ogrenci_id in veli_profili.cocuk_ogrenci_ids:
                # Öğrenci profilini getir
                ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(
                    ogrenci_id
                )
                if ogrenci_profili:
                    # Öğrenci kullanıcı bilgilerini getir
                    kullanici = await kullanici_servisi.kullanici_getir(
                        ogrenci_profili.kullanici_id
                    )
                    if kullanici:
                        cocuklar.append(
                            {
                                "ogrenci_id": ogrenci_id,
                                "ad_soyad": kullanici.ad_soyad,
                                "sinif_seviyesi": ogrenci_profili.sinif_seviyesi,
                                "okul_adi": ogrenci_profili.okul_adi,
                                "hedef_sinav": ogrenci_profili.hedef_sinav,
                                "veli_onay": ogrenci_profili.veli_onay,
                                "son_giris": kullanici.son_giris,
                            }
                        )

            return cocuklar

        except Exception as e:
            raise ValueError(f"Çocuk listesi alınırken hata: {str(e)}")

    async def cocuk_performansini_getir(
        self, veli_id: str, ogrenci_id: str
    ) -> Dict[str, Any]:
        """Belirli bir çocuğun performans verilerini getir"""
        try:
            # Veli yetkisi kontrolü
            await self._veli_yetki_kontrolu(veli_id, ogrenci_id)

            # Performans verilerini getir (mock data - gerçek implementasyonda database'den gelecek)
            if ogrenci_id not in self.cocuk_performans_verileri:
                # Mock performans verisi oluştur
                self.cocuk_performans_verileri[
                    ogrenci_id
                ] = await self._mock_performans_verisi_olustur(ogrenci_id)

            return self.cocuk_performans_verileri[ogrenci_id]

        except Exception as e:
            raise ValueError(f"Performans verisi alınırken hata: {str(e)}")

    async def haftalik_rapor_olustur(self, veli_id: str, ogrenci_id: str) -> VeliRaporu:
        """Haftalık veli raporu oluştur"""
        try:
            # Veli yetkisi kontrolü
            await self._veli_yetki_kontrolu(veli_id, ogrenci_id)

            # Öğrenci bilgilerini getir
            ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(ogrenci_id)
            kullanici = await kullanici_servisi.kullanici_getir(
                ogrenci_profili.kullanici_id
            )

            # Rapor dönemi hesapla (son 7 gün)
            bitis_tarihi = datetime.now()
            baslangic_tarihi = bitis_tarihi - timedelta(days=7)

            # Rapor ID oluştur
            rapor_id = str(uuid.uuid4())

            # Mock rapor verisi oluştur (gerçek implementasyonda database'den hesaplanacak)
            rapor = VeliRaporu(
                rapor_id=rapor_id,
                ogrenci_id=ogrenci_id,
                ogrenci_ad_soyad=kullanici.ad_soyad,
                rapor_donemi=f"{baslangic_tarihi.strftime('%d.%m.%Y')} - {bitis_tarihi.strftime('%d.%m.%Y')}",
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi,
                toplam_calisma_suresi=420,  # 7 saat
                tamamlanan_sinav_sayisi=3,
                ortalama_basari_orani=78.5,
                en_basarili_konular=[
                    "Matematik - Fonksiyonlar",
                    "Türkçe - Anlam Bilgisi",
                ],
                gelisim_gereken_konular=["Fizik - Elektrik", "Kimya - Asit-Baz"],
                haftalik_ilerleme="İyi",
                veli_onerileri=[
                    "Fizik konularında ek çalışma yapılması önerilir",
                    "Günlük çalışma süresini 1 saat artırması faydalı olacaktır",
                    "Grup çalışması yapması motivasyonunu artırabilir",
                ],
                destek_alanlari=["Fizik", "Kimya"],
            )

            # Raporu kaydet
            self.veli_raporlari[rapor_id] = rapor

            return rapor

        except Exception as e:
            raise ValueError(f"Rapor oluşturulurken hata: {str(e)}")

    async def onay_talebi_olustur(
        self, ogrenci_id: str, talep_tipi: str, aciklama: str
    ) -> VeliOnayTalebi:
        """Veli onay talebi oluştur"""
        try:
            # Öğrenci profilini getir
            ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(ogrenci_id)
            if not ogrenci_profili or not ogrenci_profili.veli_kullanici_id:
                raise ValueError("Öğrenci profili veya veli bilgisi bulunamadı")

            # Talep ID oluştur
            talep_id = str(uuid.uuid4())

            # Onay talebi oluştur
            talep = VeliOnayTalebi(
                talep_id=talep_id,
                ogrenci_id=ogrenci_id,
                veli_id=ogrenci_profili.veli_kullanici_id,
                talep_tipi=talep_tipi,
                talep_aciklamasi=aciklama,
            )

            # Talebi kaydet
            self.veli_onay_talepleri[talep_id] = talep

            # Veliye bildirim gönder
            await self._veli_bildirimi_gonder(
                ogrenci_profili.veli_kullanici_id,
                "Onay Talebi",
                f"Çocuğunuz için yeni bir onay talebi: {talep_tipi}",
                "uyari",
            )

            return talep

        except Exception as e:
            raise ValueError(f"Onay talebi oluşturulurken hata: {str(e)}")

    async def onay_talebi_yanitla(
        self, veli_id: str, talep_id: str, onay: bool, not_: Optional[str] = None
    ) -> VeliOnayTalebi:
        """Veli onay talebini yanıtla"""
        try:
            # Talep kontrolü
            if talep_id not in self.veli_onay_talepleri:
                raise ValueError("Onay talebi bulunamadı")

            talep = self.veli_onay_talepleri[talep_id]

            # Veli yetkisi kontrolü
            if talep.veli_id != veli_id:
                raise ValueError("Bu talebi yanıtlama yetkiniz yok")

            # Talebi güncelle
            talep.durum = "onaylandi" if onay else "reddedildi"
            talep.yanit_tarihi = datetime.now()
            talep.veli_notu = not_

            # Öğrenciye bildirim gönder
            await self._ogrenci_bildirimi_gonder(
                talep.ogrenci_id,
                "Onay Yanıtı",
                f"Veli onay talebiniz {talep.durum}",
                "bilgi" if onay else "uyari",
            )

            return talep

        except Exception as e:
            raise ValueError(f"Onay talebi yanıtlanırken hata: {str(e)}")

    async def veli_bildirimlerini_getir(self, veli_id: str) -> List[Bildirim]:
        """Velinin bildirimlerini getir"""
        return self.veli_bildirimleri.get(veli_id, [])

    async def bildirim_okundu_isaretle(self, veli_id: str, bildirim_id: str) -> bool:
        """Bildirimi okundu olarak işaretle"""
        try:
            bildirimler = self.veli_bildirimleri.get(veli_id, [])
            for bildirim in bildirimler:
                if bildirim.bildirim_id == bildirim_id:
                    bildirim.okundu = True
                    return True
            return False
        except Exception:
            return False

    async def _veli_yetki_kontrolu(self, veli_id: str, ogrenci_id: str) -> bool:
        """Velinin öğrenci üzerinde yetkisi olup olmadığını kontrol et"""
        veli_profili = await kullanici_servisi.veli_profili_getir(veli_id)
        if not veli_profili:
            raise ValueError("Veli profili bulunamadı")

        if ogrenci_id not in veli_profili.cocuk_ogrenci_ids:
            raise ValueError("Bu öğrenci üzerinde yetkiniz yok")

        return True

    async def _mock_performans_verisi_olustur(self, ogrenci_id: str) -> Dict[str, Any]:
        """Mock performans verisi oluştur (gerçek implementasyonda database'den gelecek)"""
        return {
            "ogrenci_id": ogrenci_id,
            "son_30_gun": {
                "toplam_calisma_suresi": 1800,  # 30 saat
                "tamamlanan_sinav_sayisi": 12,
                "ortalama_basari_orani": 76.3,
                "en_aktif_gunler": ["Pazartesi", "Çarşamba", "Cumartesi"],
                "gunluk_ortalama": 60,  # dakika
            },
            "konu_performanslari": {
                "Matematik": {"basari_orani": 82.5, "calisma_suresi": 540},
                "Türkçe": {"basari_orani": 78.2, "calisma_suresi": 420},
                "Fizik": {"basari_orani": 65.8, "calisma_suresi": 360},
                "Kimya": {"basari_orani": 71.4, "calisma_suresi": 300},
                "Biyoloji": {"basari_orani": 79.1, "calisma_suresi": 180},
            },
            "gelisim_trendi": {
                "son_hafta": "+5.2%",
                "son_ay": "+12.8%",
                "genel_trend": "yukselme",
            },
            "zayif_konular": [
                "Fizik - Elektrik ve Manyetizma",
                "Kimya - Asit-Baz Dengesi",
                "Matematik - İntegral",
            ],
            "guclu_konular": [
                "Türkçe - Anlam Bilgisi",
                "Matematik - Fonksiyonlar",
                "Biyoloji - Hücre",
            ],
            "son_sinavlar": [
                {
                    "sinav_adi": "TYT Matematik Denemesi",
                    "tarih": "2025-01-15",
                    "net": 28.5,
                    "basari_orani": 85.7,
                },
                {
                    "sinav_adi": "AYT Fen Denemesi",
                    "tarih": "2025-01-12",
                    "net": 22.3,
                    "basari_orani": 74.3,
                },
            ],
        }

    async def _veli_bildirimi_gonder(
        self, veli_id: str, baslik: str, mesaj: str, tip: str
    ) -> None:
        """Veliye bildirim gönder"""
        bildirim = Bildirim(
            bildirim_id=str(uuid.uuid4()), baslik=baslik, mesaj=mesaj, tip=tip
        )

        if veli_id not in self.veli_bildirimleri:
            self.veli_bildirimleri[veli_id] = []

        self.veli_bildirimleri[veli_id].append(bildirim)

    async def _ogrenci_bildirimi_gonder(
        self, ogrenci_id: str, baslik: str, mesaj: str, tip: str
    ) -> None:
        """Öğrenciye bildirim gönder (öğrenci servisi ile entegre edilecek)"""
        # Bu method öğrenci bildirim servisi ile entegre edilecek


# Global servis instance
veli_servisi = VeliServisi()
