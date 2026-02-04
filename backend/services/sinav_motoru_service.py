"""
ÖSYM uyumlu sınav motoru servisi
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models import (
    KonuPerformansi,
    SinavCevabi,
    SinavDurumu,
    SinavOturumu,
    SinavSonucu,
    SinavSorusu,
    SinavTipi,
)

# Import soru_bankasi_servisi lazily to avoid circular dependencies
try:
    from .soru_bankasi_service import soru_bankasi_servisi
except ImportError:
    soru_bankasi_servisi = None


class SinavMotoruServisi:
    """ÖSYM uyumlu sınav motoru servisi"""

    def __init__(self):
        # In-memory veri saklama
        self.aktif_oturumlar: Dict[str, SinavOturumu] = {}
        self.sinav_cevaplari: Dict[str, List[SinavCevabi]] = {}  # sinav_id -> cevaplar
        self.sinav_sonuclari: Dict[str, SinavSonucu] = {}
        self.zaman_takip: Dict[str, Dict] = {}  # sinav_id -> zaman bilgileri

        # ÖSYM sınav konfigürasyonları
        self.sinav_konfigurasyonlari = {
            SinavTipi.TYT: {
                "toplam_soru": 120,
                "sure_dakika": 165,
                "konu_dagilimi": {
                    "Türkçe": 40,
                    "Matematik": 40,
                    "Fen Bilimleri": 20,
                    "Sosyal Bilimler": 20,
                },
            },
            SinavTipi.AYT: {
                "toplam_soru": 80,  # Temel AYT (Matematik, Fen, Türk Dili ve Edebiyatı, Tarih, Coğrafya)
                "sure_dakika": 180,
                "konu_dagilimi": {
                    "Matematik": 40,
                    "Fizik": 14,
                    "Kimya": 13,
                    "Biyoloji": 13,
                },
            },
            SinavTipi.YDT: {
                "toplam_soru": 80,
                "sure_dakika": 180,
                "konu_dagilimi": {"İngilizce": 80},
            },
        }

    async def sinav_olustur(
        self,
        ogrenci_id: str,
        sinav_tipi: SinavTipi,
        ozel_konfigurasyonlar: Optional[Dict] = None,
    ) -> SinavOturumu:
        """Yeni sınav oturumu oluştur"""
        sinav_id = str(uuid.uuid4())

        # Sınav konfigürasyonunu al
        config = self.sinav_konfigurasyonlari[sinav_tipi].copy()

        # Özel konfigürasyonları uygula
        if ozel_konfigurasyonlar:
            config.update(ozel_konfigurasyonlar)

        # Soruları seç
        sorular = await soru_bankasi_servisi.rastgele_sorular_sec(
            sinav_tipi=sinav_tipi,
            soru_sayisi=config["toplam_soru"],
            konu_dagilimi=config.get("konu_dagilimi"),
        )

        if len(sorular) < config["toplam_soru"]:
            raise ValueError(
                f"Yeterli soru bulunamadı. Gerekli: {config['toplam_soru']}, Mevcut: {len(sorular)}"
            )

        # Sınav oturumu oluştur
        sinav_oturumu = SinavOturumu(
            sinav_id=sinav_id,
            ogrenci_id=ogrenci_id,
            sinav_tipi=sinav_tipi,
            toplam_soru_sayisi=len(sorular),
            sure_dakika=config["sure_dakika"],
            soru_listesi=[soru.soru_id for soru in sorular],
            durum=SinavDurumu.HAZIR,
        )

        # Oturumu kaydet
        self.aktif_oturumlar[sinav_id] = sinav_oturumu
        self.sinav_cevaplari[sinav_id] = []

        return sinav_oturumu

    async def sinav_baslat(self, sinav_id: str) -> SinavOturumu:
        """Sınavı başlat"""
        if sinav_id not in self.aktif_oturumlar:
            raise ValueError("Sınav oturumu bulunamadı")

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.HAZIR:
            raise ValueError("Sınav zaten başlatılmış veya tamamlanmış")

        # Sınavı başlat
        oturum.durum = SinavDurumu.DEVAM_EDIYOR
        oturum.baslangic_zamani = datetime.now()
        oturum.bitis_zamani = oturum.baslangic_zamani + timedelta(
            minutes=oturum.sure_dakika
        )
        oturum.kalan_sure = oturum.sure_dakika * 60  # saniye cinsinden
        oturum.son_guncelleme = datetime.now()

        # Zaman takibi başlat
        self.zaman_takip[sinav_id] = {
            "baslangic": oturum.baslangic_zamani,
            "son_aktivite": datetime.now(),
            "duraklatma_suresi": 0,
        }

        # Otomatik tamamlama task'ı başlat
        asyncio.create_task(self._otomatik_tamamlama_task(sinav_id))

        # WebSocket bildirimi gönder
        await self._send_websocket_update(
            sinav_id,
            {
                "type": "exam_started",
                "message": "Sınav başlatıldı",
                "remaining_time": oturum.kalan_sure,
                "status": oturum.durum.value,
            },
        )

        return oturum

    async def mevcut_soru_getir(self, sinav_id: str) -> Optional[SinavSorusu]:
        """Mevcut soruyu getir"""
        if sinav_id not in self.aktif_oturumlar:
            return None

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.DEVAM_EDIYOR:
            return None

        if oturum.mevcut_soru_index >= len(oturum.soru_listesi):
            return None

        soru_id = oturum.soru_listesi[oturum.mevcut_soru_index]
        return await soru_bankasi_servisi.soru_getir(soru_id)

    async def cevap_kaydet(
        self,
        sinav_id: str,
        soru_id: str,
        cevap: Optional[str],
        cevap_suresi: Optional[int] = None,
    ) -> bool:
        """Cevap kaydet"""
        if sinav_id not in self.aktif_oturumlar:
            return False

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.DEVAM_EDIYOR:
            return False

        # Cevap oluştur
        sinav_cevabi = SinavCevabi(
            sinav_id=sinav_id,
            soru_id=soru_id,
            ogrenci_cevabi=cevap,
            cevap_zamani=datetime.now(),
            cevap_suresi=cevap_suresi,
        )

        # Cevabı kaydet
        self.sinav_cevaplari[sinav_id].append(sinav_cevabi)

        # Oturum bilgilerini güncelle
        if cevap:
            oturum.cevaplanan_sorular[soru_id] = cevap

        oturum.son_guncelleme = datetime.now()

        # Zaman takibini güncelle
        if sinav_id in self.zaman_takip:
            self.zaman_takip[sinav_id]["son_aktivite"] = datetime.now()

        return True

    async def sonraki_soru(self, sinav_id: str) -> Optional[SinavSorusu]:
        """Sonraki soruya geç"""
        if sinav_id not in self.aktif_oturumlar:
            return None

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.DEVAM_EDIYOR:
            return None

        # Sonraki soruya geç
        oturum.mevcut_soru_index += 1
        oturum.son_guncelleme = datetime.now()

        return await self.mevcut_soru_getir(sinav_id)

    async def onceki_soru(self, sinav_id: str) -> Optional[SinavSorusu]:
        """Önceki soruya dön"""
        if sinav_id not in self.aktif_oturumlar:
            return None

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.DEVAM_EDIYOR:
            return None

        if oturum.mevcut_soru_index > 0:
            oturum.mevcut_soru_index -= 1
            oturum.son_guncelleme = datetime.now()

        return await self.mevcut_soru_getir(sinav_id)

    async def soru_isaretleme(
        self, sinav_id: str, soru_id: str, isaretli: bool
    ) -> bool:
        """Soru işaretleme/işaret kaldırma"""
        if sinav_id not in self.aktif_oturumlar:
            return False

        oturum = self.aktif_oturumlar[sinav_id]

        if isaretli:
            if soru_id not in oturum.isaretlenen_sorular:
                oturum.isaretlenen_sorular.append(soru_id)
        else:
            if soru_id in oturum.isaretlenen_sorular:
                oturum.isaretlenen_sorular.remove(soru_id)

        oturum.son_guncelleme = datetime.now()
        return True

    async def kalan_sure_getir(self, sinav_id: str) -> Optional[int]:
        """Kalan süreyi getir (saniye)"""
        if sinav_id not in self.aktif_oturumlar:
            return None

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum != SinavDurumu.DEVAM_EDIYOR or not oturum.bitis_zamani:
            return None

        kalan = (oturum.bitis_zamani - datetime.now()).total_seconds()
        return max(0, int(kalan))

    async def sinav_tamamla(
        self, sinav_id: str, manuel_tamamlama: bool = True
    ) -> SinavSonucu:
        """Sınavı tamamla ve sonuçları hesapla"""
        if sinav_id not in self.aktif_oturumlar:
            raise ValueError("Sınav oturumu bulunamadı")

        oturum = self.aktif_oturumlar[sinav_id]

        if oturum.durum == SinavDurumu.TAMAMLANDI:
            # Zaten tamamlanmış, mevcut sonucu döndür
            return self.sinav_sonuclari.get(sinav_id)

        # Oturum durumunu güncelle
        oturum.durum = SinavDurumu.TAMAMLANDI
        if not oturum.bitis_zamani or manuel_tamamlama:
            oturum.bitis_zamani = datetime.now()
        oturum.son_guncelleme = datetime.now()

        # Sonuçları hesapla
        sonuc = await self._sonuclari_hesapla(sinav_id)

        # Sonucu kaydet
        self.sinav_sonuclari[sinav_id] = sonuc

        # WebSocket bildirimi gönder
        await self._send_websocket_update(
            sinav_id,
            {
                "type": "exam_completed",
                "message": "Sınav tamamlandı",
                "status": oturum.durum.value,
                "score": sonuc.ham_puan,
                "net": sonuc.net_sayisi,
            },
        )

        return sonuc

    async def _sonuclari_hesapla(self, sinav_id: str) -> SinavSonucu:
        """Sınav sonuçlarını hesapla"""
        oturum = self.aktif_oturumlar[sinav_id]
        cevaplar = self.sinav_cevaplari.get(sinav_id, [])

        # Temel istatistikler
        dogru_sayisi = 0
        yanlis_sayisi = 0
        bos_sayisi = 0
        konu_performanslari = {}

        # Her soru için kontrol
        for soru_id in oturum.soru_listesi:
            soru = await soru_bankasi_servisi.soru_getir(soru_id)
            if not soru:
                continue

            # Konu performansı için hazırlık
            konu = soru.konu
            if konu not in konu_performanslari:
                konu_performanslari[konu] = {
                    "toplam": 0,
                    "dogru": 0,
                    "yanlis": 0,
                    "bos": 0,
                }

            konu_performanslari[konu]["toplam"] += 1

            # Cevabı bul
            ogrenci_cevabi = oturum.cevaplanan_sorular.get(soru_id)

            if not ogrenci_cevabi:
                # Boş cevap
                bos_sayisi += 1
                konu_performanslari[konu]["bos"] += 1
            elif ogrenci_cevabi == soru.dogru_cevap:
                # Doğru cevap
                dogru_sayisi += 1
                konu_performanslari[konu]["dogru"] += 1
            else:
                # Yanlış cevap
                yanlis_sayisi += 1
                konu_performanslari[konu]["yanlis"] += 1

        # Net hesaplama (ÖSYM sistemine göre: doğru - (yanlış/4))
        net_sayisi = dogru_sayisi - (yanlis_sayisi / 4)
        ham_puan = (dogru_sayisi / oturum.toplam_soru_sayisi) * 100

        # Konu performanslarını oluştur
        konu_performans_listesi = []
        zayif_konular = []
        guclu_konular = []

        for konu, stats in konu_performanslari.items():
            basari_yuzdesi = (
                (stats["dogru"] / stats["toplam"]) * 100 if stats["toplam"] > 0 else 0
            )

            konu_performansi = KonuPerformansi(
                konu=konu,
                toplam_soru=stats["toplam"],
                dogru_sayisi=stats["dogru"],
                yanlis_sayisi=stats["yanlis"],
                bos_sayisi=stats["bos"],
                basari_yuzdesi=basari_yuzdesi,
            )

            konu_performans_listesi.append(konu_performansi)

            # Zayıf ve güçlü konuları belirle
            if basari_yuzdesi < 50:
                zayif_konular.append(konu)
            elif basari_yuzdesi > 80:
                guclu_konular.append(konu)

        # Çalışma önerileri oluştur
        calisma_onerileri = []
        if zayif_konular:
            calisma_onerileri.append(
                f"Bu konularda daha fazla çalışmanız önerilir: {', '.join(zayif_konular)}"
            )
        if guclu_konular:
            calisma_onerileri.append(
                f"Bu konularda başarılısınız, pekiştirme çalışmaları yapabilirsiniz: {', '.join(guclu_konular)}"
            )

        # Sonuç oluştur
        sonuc = SinavSonucu(
            sonuc_id=str(uuid.uuid4()),
            sinav_id=sinav_id,
            ogrenci_id=oturum.ogrenci_id,
            sinav_tipi=oturum.sinav_tipi,
            toplam_soru=oturum.toplam_soru_sayisi,
            dogru_sayisi=dogru_sayisi,
            yanlis_sayisi=yanlis_sayisi,
            bos_sayisi=bos_sayisi,
            net_sayisi=net_sayisi,
            ham_puan=ham_puan,
            konu_performanslari=konu_performans_listesi,
            zayif_konular=zayif_konular,
            guclu_konular=guclu_konular,
            calisma_onerileri=calisma_onerileri,
        )

        return sonuc

    async def _otomatik_tamamlama_task(self, sinav_id: str):
        """Otomatik sınav tamamlama task'ı"""
        try:
            oturum = self.aktif_oturumlar.get(sinav_id)
            if not oturum or not oturum.bitis_zamani:
                return

            # Bitiş zamanına kadar bekle
            kalan_sure = (oturum.bitis_zamani - datetime.now()).total_seconds()
            if kalan_sure > 0:
                await asyncio.sleep(kalan_sure)

            # Sınavı otomatik tamamla
            if oturum.durum == SinavDurumu.DEVAM_EDIYOR:
                await self.sinav_tamamla(sinav_id, manuel_tamamlama=False)

        except Exception as e:
            print(f"Otomatik tamamlama hatası: {e}")

    async def sinav_iptal_et(self, sinav_id: str) -> bool:
        """Sınavı iptal et"""
        if sinav_id not in self.aktif_oturumlar:
            return False

        oturum = self.aktif_oturumlar[sinav_id]
        oturum.durum = SinavDurumu.IPTAL_EDILDI
        oturum.son_guncelleme = datetime.now()

        return True

    async def oturum_getir(self, sinav_id: str) -> Optional[SinavOturumu]:
        """Sınav oturumu bilgilerini getir"""
        return self.aktif_oturumlar.get(sinav_id)

    async def sonuc_getir(self, sinav_id: str) -> Optional[SinavSonucu]:
        """Sınav sonucunu getir"""
        return self.sinav_sonuclari.get(sinav_id)

    async def ogrenci_sinavlari(self, ogrenci_id: str) -> List[SinavOturumu]:
        """Öğrencinin tüm sınavlarını getir"""
        return [
            oturum
            for oturum in self.aktif_oturumlar.values()
            if oturum.ogrenci_id == ogrenci_id
        ]

    async def _send_websocket_update(self, sinav_id: str, data: dict):
        """WebSocket güncellemesi gönder"""
        try:
            # WebSocket manager'a erişim için global import
            # Bu import döngüsel bağımlılığı önlemek için burada yapılıyor
            from main import manager

            await manager.broadcast_to_exam(sinav_id, data)
        except Exception as e:
            print(f"WebSocket güncelleme hatası: {e}")


# Global servis instance
sinav_motoru_servisi = SinavMotoruServisi()
