"""
ÖSYM uyumlu sınav motoru servisi
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models import (
    KonuPerformansi, SinavCevabi, SinavDurumu, SinavOturumu,
    SinavSonucu, SinavSorusu, SinavTipi
)

from .soru_bankasi_service import soru_bankasi_servisi


class SinavMotoruServisi:
    """ÖSYM uyumlu sınav motoru servisi"""
    
    def __init__(self):
        self.aktif_oturumlar: Dict[str, SinavOturumu] = {}
        self.sinav_cevaplari: Dict[str, List[SinavCevabi]] = {}
        self.sinav_sonuclari: Dict[str, SinavSonucu] = {}
        
        # ÖSYM sınav konfigürasyonları
        self.sinav_konfigurasyonlari = {
            SinavTipi.TYT: {
                "toplam_soru": 120,
                "sure_dakika": 165,
                "konu_dagilimi": {
                    "Türkçe": 40,
                    "Matematik": 40,
                    "Fen Bilimleri": 20,
                    "Sosyal Bilimler": 20
                }
            },
            SinavTipi.AYT: {
                "toplam_soru": 80,
                "sure_dakika": 180,
                "konu_dagilimi": {
                    "Matematik": 40,
                    "Fizik": 14,
                    "Kimya": 13,
                    "Biyoloji": 13
                }
            },
            SinavTipi.YDT: {
                "toplam_soru": 80,
                "sure_dakika": 180,
                "konu_dagilimi": {"İngilizce": 80}
            }
        }
    
    async def sinav_olustur(
        self, ogrenci_id: str, sinav_tipi: SinavTipi,
        ozel_konfigurasyonlar: Optional[Dict] = None
    ) -> SinavOturumu:
        """Yeni sınav oturumu oluştur"""
        sinav_id = str(uuid.uuid4())
        config = self.sinav_konfigurasyonlari[sinav_tipi].copy()
        
        if ozel_konfigurasyonlar:
            config.update(ozel_konfigurasyonlar)
        
        # Soruları seç
        sorular = await soru_bankasi_servisi.rastgele_sorular_sec(
            sinav_tipi=sinav_tipi,
            soru_sayisi=config["toplam_soru"],
            konu_dagilimi=config.get("konu_dagilimi")
        )
        
        # Sınav oturumu oluştur
        sinav_oturumu = SinavOturumu(
            sinav_id=sinav_id,
            ogrenci_id=ogrenci_id,
            sinav_tipi=sinav_tipi,
            toplam_soru_sayisi=len(sorular),
            sure_dakika=config["sure_dakika"],
            soru_listesi=[soru.soru_id for soru in sorular],
            durum=SinavDurumu.HAZIR
        )
        
        self.aktif_oturumlar[sinav_id] = sinav_oturumu
        self.sinav_cevaplari[sinav_id] = []
        
        return sinav_oturumu
    
    async def sinav_baslat(self, sinav_id: str) -> SinavOturumu:
        """Sınavı başlat"""
        oturum = self.aktif_oturumlar.get(sinav_id)
        if not oturum:
            raise ValueError("Sınav oturumu bulunamadı")
        
        if oturum.durum != SinavDurumu.HAZIR:
            raise ValueError("Sınav zaten başlatılmış veya tamamlanmış")
        
        oturum.durum = SinavDurumu.DEVAM_EDIYOR
        oturum.baslangic_zamani = datetime.now()
        oturum.bitis_zamani = oturum.baslangic_zamani + timedelta(minutes=oturum.sure_dakika)
        oturum.kalan_sure = oturum.sure_dakika * 60
        
        # Otomatik tamamlama task'ı başlat
        asyncio.create_task(self._otomatik_tamamlama_task(sinav_id))
        
        return oturum
    
    async def sinav_tamamla(self, sinav_id: str) -> SinavSonucu:
        """Sınavı tamamla ve sonuçları hesapla"""
        oturum = self.aktif_oturumlar.get(sinav_id)
        if not oturum:
            raise ValueError("Sınav oturumu bulunamadı")
        
        oturum.durum = SinavDurumu.TAMAMLANDI
        oturum.bitis_zamani = datetime.now()
        
        # Sonuçları hesapla
        sonuc = await self._sonuclari_hesapla(sinav_id)
        self.sinav_sonuclari[sinav_id] = sonuc
        
        return sonuc
    
    async def _sonuclari_hesapla(self, sinav_id: str) -> SinavSonucu:
        """Sınav sonuçlarını hesapla"""
        oturum = self.aktif_oturumlar[sinav_id]
        
        dogru_sayisi = 0
        yanlis_sayisi = 0
        bos_sayisi = 0
        konu_performanslari = {}
        
        # Her soru için kontrol
        for soru_id in oturum.soru_listesi:
            soru = await soru_bankasi_servisi.soru_getir(soru_id)
            if not soru:
                continue
            
            konu = soru.konu
            if konu not in konu_performanslari:
                konu_performanslari[konu] = {
                    "toplam": 0, "dogru": 0, "yanlis": 0, "bos": 0
                }
            
            konu_performanslari[konu]["toplam"] += 1
            ogrenci_cevabi = oturum.cevaplanan_sorular.get(soru_id)
            
            if not ogrenci_cevabi:
                bos_sayisi += 1
                konu_performanslari[konu]["bos"] += 1
            elif ogrenci_cevabi == soru.dogru_cevap:
                dogru_sayisi += 1
                konu_performanslari[konu]["dogru"] += 1
            else:
                yanlis_sayisi += 1
                konu_performanslari[konu]["yanlis"] += 1
        
        # ÖSYM net hesaplama
        net_sayisi = dogru_sayisi - (yanlis_sayisi / 4)
        ham_puan = (dogru_sayisi / oturum.toplam_soru_sayisi) * 100
        
        return SinavSonucu(
            sonuc_id=str(uuid.uuid4()),
            sinav_id=sinav_id,
            ogrenci_id=oturum.ogrenci_id,
            sinav_tipi=oturum.sinav_tipi,
            toplam_soru=oturum.toplam_soru_sayisi,
            dogru_sayisi=dogru_sayisi,
            yanlis_sayisi=yanlis_sayisi,
            bos_sayisi=bos_sayisi,
            net_sayisi=net_sayisi,
            ham_puan=ham_puan
        )
    
    async def _otomatik_tamamlama_task(self, sinav_id: str):
        """Otomatik sınav tamamlama"""
        try:
            oturum = self.aktif_oturumlar.get(sinav_id)
            if not oturum or not oturum.bitis_zamani:
                return
            
            kalan_sure = (oturum.bitis_zamani - datetime.now()).total_seconds()
            if kalan_sure > 0:
                await asyncio.sleep(kalan_sure)
            
            if oturum.durum == SinavDurumu.DEVAM_EDIYOR:
                await self.sinav_tamamla(sinav_id)
        except Exception as e:
            print(f"Otomatik tamamlama hatası: {e}")


# Global servis instance
sinav_motoru_servisi = SinavMotoruServisi()