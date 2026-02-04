"""
IRT + Türkçe Morfoloji Ana Servisi
ÖSYM ve ETS standartlarını aşan soru analizi ve zorluk belirleme sistemi

Bu servis Zemberek-NLP morfoloji analizi ile IRT modelini birleştirerek
dünya çapında benzersiz bir soru kalitesi değerlendirme sistemi sunar.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

# PERFORMANCE: Redis cache integration
from core.cache import cache_manager

from models.irt_morfoloji import (
    OgrenciMorfolojiProfili,
    SoruMorfolojiAnalizi,
    TurkceIRTSoruAnalizi,
)
from services.irt_service import IRTService
from services.zemberek_morfoloji_service import ZemberekMorfolojiService

logger = logging.getLogger(__name__)


class IRTMorfolojiService:
    """
    IRT + Türkçe Morfoloji ana koordinasyon servisi

    Bu servis şu devrimsel özellikleri koordine eder:
    1. Zemberek-NLP ile Türkçe morfolojik analiz
    2. 4 Parametreli IRT model kalibrasyonu
    3. Morfoloji faktörlü zorluk hesaplama
    4. ÖSYM/ETS standartlarını aşan soru analizi
    5. Öğrenci morfoloji farkındalığı profilleme
    6. Adaptif soru önerisi sistemi
    """

    def __init__(self):
        """IRT Morfoloji servisini başlat"""
        self.zemberek_service = ZemberekMorfolojiService()
        self.irt_service = IRTService()

        # Soru analizleri cache
        self.soru_analizleri: Dict[str, TurkceIRTSoruAnalizi] = {}

        # Performans metrikleri
        self.analiz_sayisi = 0
        self.basarili_kalibrasyon_sayisi = 0
        self.ortalama_analiz_suresi = 0.0

        # Kalite eşikleri
        self.minimum_kalite_skoru = 60.0
        self.minimum_ayirt_edicilik = 0.8
        self.maksimum_morfoloji_faktoru = 1.5

    async def tam_soru_analizi(
        self,
        soru_id: str,
        soru_metni: str,
        cevap_verileri: List[Dict[str, Any]],
        konu: str = "Genel",
        sinav_tipi: str = "TYT",
    ) -> TurkceIRTSoruAnalizi:
        """
        Soru için tam kapsamlı analiz yap

        Args:
            soru_id: Soru kimliği
            soru_metni: Soru metni
            cevap_verileri: Öğrenci cevap verileri
            konu: Soru konusu
            sinav_tipi: Sınav tipi (TYT, AYT, YDT)

        Returns:
            TurkceIRTSoruAnalizi: Kapsamlı soru analiz raporu
        """
        try:
            baslangic_zamani = datetime.now()

            # PERFORMANCE: Cache check for complete analysis
            cache_key = f"irt_morfoloji:soru:{soru_id}:{konu}:{sinav_tipi}"
            cached_analiz = await cache_manager.get(cache_key)
            if cached_analiz:
                logger.info(f"IRT Morfoloji cache hit: {soru_id}")
                return (
                    TurkceIRTSoruAnalizi(**cached_analiz)
                    if isinstance(cached_analiz, dict)
                    else cached_analiz
                )

            logger.info(f"Tam soru analizi başlıyor - ID: {soru_id}")

            # 1. Morfolojik analiz
            morfoloji_analizi = await self.zemberek_service.analiz_et_soru_metni(
                soru_metni, soru_id
            )

            # 2. IRT kalibrasyon
            kalibrasyon_sonucu = await self.irt_service.hesapla_irt_parametreleri(
                soru_id, cevap_verileri, morfoloji_analizi
            )

            # 3. Soru kalitesi analizi
            soru_analizi = await self.irt_service.analiz_et_soru_kalitesi(
                soru_id,
                kalibrasyon_sonucu.yeni_parametreler,
                morfoloji_analizi,
                cevap_verileri,
            )

            # 4. Konu ve sınav tipi bilgilerini güncelle
            soru_analizi.konu = konu
            soru_analizi.sinav_tipi = sinav_tipi
            soru_analizi.kalibrasyon_sonucu = kalibrasyon_sonucu

            # 5. Local cache'e kaydet
            self.soru_analizleri[soru_id] = soru_analizi

            # PERFORMANCE: Save to Redis cache (1 hour TTL for question analysis)
            analiz_dict = {
                "soru_id": soru_analizi.soru_id,
                "soru_metni": soru_analizi.soru_metni,
                "konu": soru_analizi.konu,
                "sinav_tipi": soru_analizi.sinav_tipi,
                "morfoloji_analizi": soru_analizi.morfoloji_analizi.__dict__
                if hasattr(soru_analizi.morfoloji_analizi, "__dict__")
                else soru_analizi.morfoloji_analizi,
                "irt_parametreleri": soru_analizi.irt_parametreleri.__dict__
                if hasattr(soru_analizi.irt_parametreleri, "__dict__")
                else soru_analizi.irt_parametreleri,
                "kalite_skoru": soru_analizi.get_soru_kalite_skoru(),
            }
            await cache_manager.set(cache_key, analiz_dict, ttl=3600)

            # 6. Performans metriklerini güncelle
            await self._guncelle_performans_metrikleri(baslangic_zamani, True)

            logger.info(
                f"Tam soru analizi tamamlandı - ID: {soru_id}, "
                f"Kalite skoru: {soru_analizi.get_soru_kalite_skoru():.1f}/100, "
                f"Morfoloji faktörü: {soru_analizi.irt_parametreleri.morfoloji_faktoru:.3f}"
            )

            return soru_analizi

        except Exception as e:
            logger.error(f"Tam soru analizi hatası - ID: {soru_id}, Hata: {str(e)}")
            await self._guncelle_performans_metrikleri(baslangic_zamani, False)
            raise

    async def hizli_soru_degerlendirmesi(
        self,
        soru_metni: str,
        hedef_zorluk: float = 0.0,
        hedef_ogrenci_seviyesi: str = "orta",
    ) -> Dict[str, Any]:
        """
        Soru için hızlı ön değerlendirme yap

        Args:
            soru_metni: Soru metni
            hedef_zorluk: Hedef zorluk seviyesi (-4 ile +4 arası)
            hedef_ogrenci_seviyesi: Hedef öğrenci seviyesi

        Returns:
            Dict: Hızlı değerlendirme sonuçları
        """
        try:
            # Morfolojik analiz
            morfoloji_analizi = await self.zemberek_service.analiz_et_soru_metni(
                soru_metni, f"hizli_{datetime.now().timestamp()}"
            )

            # Morfoloji faktörünü hesapla
            morfoloji_faktoru = morfoloji_analizi.hesapla_soru_morfoloji_faktoru()

            # Tahmini zorluk hesapla
            tahmini_zorluk = hedef_zorluk + morfoloji_faktoru

            # Uygunluk değerlendirmesi
            uygunluk_skoru = await self._hesapla_uygunluk_skoru(
                morfoloji_analizi, tahmini_zorluk, hedef_ogrenci_seviyesi
            )

            # Öneriler oluştur
            oneriler = await self._olustur_hizli_oneriler(
                morfoloji_analizi, tahmini_zorluk
            )

            return {
                "morfoloji_skoru": morfoloji_analizi.ortalama_morfoloji_skoru,
                "morfoloji_faktoru": morfoloji_faktoru,
                "tahmini_zorluk": tahmini_zorluk,
                "uygunluk_skoru": uygunluk_skoru,
                "kelime_sayisi": morfoloji_analizi.toplam_kelime_sayisi,
                "ortalama_ek_sayisi": morfoloji_analizi.ortalama_ek_sayisi,
                "karmasiklik_profili": morfoloji_analizi.get_karmasiklik_profili(),
                "oneriler": oneriler,
                "analiz_suresi_ms": morfoloji_analizi.analiz_suresi_ms,
            }

        except Exception as e:
            logger.error(f"Hızlı değerlendirme hatası: {str(e)}")
            raise

    async def ogrenci_uyumlu_soru_onerisi(
        self,
        ogrenci_id: str,
        konu: str,
        hedef_basari_orani: float = 0.7,
        soru_havuzu: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Öğrenci profiline uygun soru önerisi yap

        Args:
            ogrenci_id: Öğrenci kimliği
            konu: Konu adı
            hedef_basari_orani: Hedef başarı oranı (0-1 arası)
            soru_havuzu: Öneri yapılacak soru ID'leri

        Returns:
            List[Dict]: Önerilen sorular ve uygunluk skorları
        """
        try:
            # Öğrenci morfoloji profilini al
            ogrenci_profili = self.irt_service.ogrenci_profilleri.get(
                ogrenci_id, OgrenciMorfolojiProfili(ogrenci_id=ogrenci_id)
            )

            # Öğrenci theta'sını hesapla
            ogrenci_theta = ogrenci_profili.hesapla_morfoloji_theta()

            # Soru havuzunu değerlendir
            oneriler = []

            if soru_havuzu:
                for soru_id in soru_havuzu:
                    if soru_id in self.soru_analizleri:
                        soru_analizi = self.soru_analizleri[soru_id]

                        # Başarı olasılığını hesapla
                        basari_olasiligi = (
                            await self.irt_service.hesapla_cevap_olasiligi(
                                ogrenci_theta,
                                soru_analizi.irt_parametreleri,
                                ogrenci_profili,
                            )
                        )

                        # Uygunluk skorunu hesapla
                        uygunluk_skoru = await self._hesapla_soru_ogrenci_uygunlugu(
                            basari_olasiligi,
                            hedef_basari_orani,
                            soru_analizi,
                            ogrenci_profili,
                        )

                        oneriler.append(
                            {
                                "soru_id": soru_id,
                                "basari_olasiligi": basari_olasiligi,
                                "uygunluk_skoru": uygunluk_skoru,
                                "morfoloji_uyumu": await self._hesapla_morfoloji_uyumu(
                                    soru_analizi.morfoloji_analizi, ogrenci_profili
                                ),
                                "zorluk_seviyesi": soru_analizi.zorluk_seviyesi,
                                "kalite_skoru": soru_analizi.get_soru_kalite_skoru(),
                            }
                        )

            # Uygunluk skoruna göre sırala
            oneriler.sort(key=lambda x: x["uygunluk_skoru"], reverse=True)

            logger.info(
                f"Öğrenci soru önerisi tamamlandı - ID: {ogrenci_id}, "
                f"Öneri sayısı: {len(oneriler)}"
            )

            return oneriler[:10]  # En iyi 10 öneri

        except Exception as e:
            logger.error(f"Soru önerisi hatası - Öğrenci: {ogrenci_id}, Hata: {str(e)}")
            raise

    async def toplu_soru_kalite_analizi(
        self, soru_listesi: List[Dict[str, Any]], kalite_esigi: float = None
    ) -> Dict[str, Any]:
        """
        Birden fazla soru için toplu kalite analizi

        Args:
            soru_listesi: [{"soru_id": str, "soru_metni": str, "cevap_verileri": List}]
            kalite_esigi: Minimum kalite eşiği

        Returns:
            Dict: Toplu analiz raporu
        """
        try:
            if kalite_esigi is None:
                kalite_esigi = self.minimum_kalite_skoru

            # Paralel analiz
            analiz_tasks = []
            for soru_info in soru_listesi:
                task = self.tam_soru_analizi(
                    soru_info["soru_id"],
                    soru_info["soru_metni"],
                    soru_info["cevap_verileri"],
                    soru_info.get("konu", "Genel"),
                    soru_info.get("sinav_tipi", "TYT"),
                )
                analiz_tasks.append(task)

            # Analizleri bekle
            analiz_sonuclari = await asyncio.gather(
                *analiz_tasks, return_exceptions=True
            )

            # Sonuçları kategorize et
            basarili_analizler = []
            basarisiz_analizler = []
            yuksek_kalite_sorular = []
            dusuk_kalite_sorular = []

            for i, sonuc in enumerate(analiz_sonuclari):
                if isinstance(sonuc, Exception):
                    basarisiz_analizler.append(
                        {"soru_id": soru_listesi[i]["soru_id"], "hata": str(sonuc)}
                    )
                else:
                    basarili_analizler.append(sonuc)

                    kalite_skoru = sonuc.get_soru_kalite_skoru()
                    if kalite_skoru >= kalite_esigi:
                        yuksek_kalite_sorular.append(sonuc)
                    else:
                        dusuk_kalite_sorular.append(sonuc)

            # İstatistikleri hesapla
            istatistikler = await self._hesapla_toplu_istatistikler(basarili_analizler)

            return {
                "toplam_soru_sayisi": len(soru_listesi),
                "basarili_analiz_sayisi": len(basarili_analizler),
                "basarisiz_analiz_sayisi": len(basarisiz_analizler),
                "yuksek_kalite_sayisi": len(yuksek_kalite_sorular),
                "dusuk_kalite_sayisi": len(dusuk_kalite_sorular),
                "kalite_esigi": kalite_esigi,
                "istatistikler": istatistikler,
                "yuksek_kalite_sorular": [s.soru_id for s in yuksek_kalite_sorular],
                "dusuk_kalite_sorular": [s.soru_id for s in dusuk_kalite_sorular],
                "basarisiz_analizler": basarisiz_analizler,
            }

        except Exception as e:
            logger.error(f"Toplu analiz hatası: {str(e)}")
            raise

    async def osym_ets_karsilastirma_raporu(self, soru_id: str) -> Dict[str, Any]:
        """
        ÖSYM ve ETS standartları ile detaylı karşılaştırma raporu

        Args:
            soru_id: Soru kimliği

        Returns:
            Dict: Karşılaştırma raporu
        """
        try:
            if soru_id not in self.soru_analizleri:
                raise ValueError(f"Soru analizi bulunamadı: {soru_id}")

            soru_analizi = self.soru_analizleri[soru_id]
            irt_params = soru_analizi.irt_parametreleri

            # ÖSYM standartları
            osym_standartlari = {
                "ayirt_edicilik_min": 0.3,
                "ayirt_edicilik_ideal": 1.0,
                "zorluk_araligi": (-2.0, 2.0),
                "sans_faktoru_max": 0.25,
            }

            # ETS standartları
            ets_standartlari = {
                "ayirt_edicilik_min": 0.4,
                "ayirt_edicilik_ideal": 1.2,
                "zorluk_araligi": (-2.5, 2.5),
                "sans_faktoru_max": 0.2,
            }

            # Karşılaştırma hesapla
            osym_karsilastirma = {
                "ayirt_edicilik_durumu": self._karsilastir_ayirt_edicilik(
                    irt_params.discrimination, osym_standartlari
                ),
                "zorluk_durumu": self._karsilastir_zorluk(
                    irt_params.difficulty, osym_standartlari
                ),
                "sans_faktoru_durumu": self._karsilastir_sans_faktoru(
                    irt_params.guessing, osym_standartlari
                ),
                "genel_uyum_skoru": 0.0,
            }

            ets_karsilastirma = {
                "ayirt_edicilik_durumu": self._karsilastir_ayirt_edicilik(
                    irt_params.discrimination, ets_standartlari
                ),
                "zorluk_durumu": self._karsilastir_zorluk(
                    irt_params.difficulty, ets_standartlari
                ),
                "sans_faktoru_durumu": self._karsilastir_sans_faktoru(
                    irt_params.guessing, ets_standartlari
                ),
                "genel_uyum_skoru": 0.0,
            }

            # Genel uyum skorlarını hesapla
            osym_karsilastirma["genel_uyum_skoru"] = self._hesapla_genel_uyum_skoru(
                osym_karsilastirma
            )
            ets_karsilastirma["genel_uyum_skoru"] = self._hesapla_genel_uyum_skoru(
                ets_karsilastirma
            )

            # Türkçe morfoloji avantajı
            morfoloji_avantaji = {
                "morfoloji_faktoru": irt_params.morfoloji_faktoru,
                "kelime_karmasikligi": soru_analizi.morfoloji_analizi.ortalama_morfoloji_skoru,
                "ek_cesitliligi": soru_analizi.morfoloji_analizi.ek_tipi_cesitliligi,
                "avantaj_aciklamasi": "Türkçe morfolojik analiz ile ÖSYM/ETS'nin sunmadığı detaylı dil analizi",
            }

            return {
                "soru_id": soru_id,
                "analiz_tarihi": datetime.now().isoformat(),
                "osym_karsilastirma": osym_karsilastirma,
                "ets_karsilastirma": ets_karsilastirma,
                "morfoloji_avantaji": morfoloji_avantaji,
                "sonuc": self._belirle_karsilastirma_sonucu(
                    osym_karsilastirma, ets_karsilastirma
                ),
                "oneriler": await self._olustur_karsilastirma_onerileri(soru_analizi),
            }

        except Exception as e:
            logger.error(
                f"ÖSYM/ETS karşılaştırma hatası - Soru: {soru_id}, Hata: {str(e)}"
            )
            raise

    # Yardımcı metodlar
    async def _guncelle_performans_metrikleri(
        self, baslangic_zamani: datetime, basarili: bool
    ):
        """Performans metriklerini güncelle"""
        sure = (datetime.now() - baslangic_zamani).total_seconds()

        self.analiz_sayisi += 1
        if basarili:
            self.basarili_kalibrasyon_sayisi += 1

        # Ortalama süreyi güncelle
        self.ortalama_analiz_suresi = (
            self.ortalama_analiz_suresi * (self.analiz_sayisi - 1) + sure
        ) / self.analiz_sayisi

    async def _hesapla_uygunluk_skoru(
        self,
        morfoloji_analizi: SoruMorfolojiAnalizi,
        tahmini_zorluk: float,
        hedef_ogrenci_seviyesi: str,
    ) -> float:
        """Uygunluk skorunu hesapla"""
        skor = 100.0

        # Morfoloji karmaşıklığı kontrolü
        if morfoloji_analizi.ortalama_morfoloji_skoru > 8.0:
            skor -= 20.0
        elif morfoloji_analizi.ortalama_morfoloji_skoru > 6.0:
            skor -= 10.0

        # Zorluk uygunluğu
        hedef_zorluk_araliklari = {
            "temel": (-2.0, -0.5),
            "orta": (-0.5, 0.5),
            "ileri": (0.5, 2.0),
        }

        if hedef_ogrenci_seviyesi in hedef_zorluk_araliklari:
            min_z, max_z = hedef_zorluk_araliklari[hedef_ogrenci_seviyesi]
            if not (min_z <= tahmini_zorluk <= max_z):
                skor -= 15.0

        # Kelime sayısı kontrolü
        if morfoloji_analizi.toplam_kelime_sayisi < 5:
            skor -= 10.0
        elif morfoloji_analizi.toplam_kelime_sayisi > 50:
            skor -= 15.0

        return max(0.0, skor)

    async def _olustur_hizli_oneriler(
        self, morfoloji_analizi: SoruMorfolojiAnalizi, tahmini_zorluk: float
    ) -> List[str]:
        """Hızlı öneriler oluştur"""
        oneriler = []

        if morfoloji_analizi.ortalama_morfoloji_skoru > 7.0:
            oneriler.append(
                "Morfolojik karmaşıklık yüksek - daha basit kelimeler kullanın"
            )

        if morfoloji_analizi.ortalama_ek_sayisi > 3.0:
            oneriler.append(
                "Ortalama ek sayısı yüksek - daha az ekli kelimeler tercih edin"
            )

        if abs(tahmini_zorluk) > 2.0:
            oneriler.append("Tahmini zorluk aşırı - soru metnini gözden geçirin")

        if morfoloji_analizi.toplam_kelime_sayisi < 5:
            oneriler.append("Soru çok kısa - daha detaylı açıklama ekleyin")

        return oneriler

    async def _hesapla_soru_ogrenci_uygunlugu(
        self,
        basari_olasiligi: float,
        hedef_basari_orani: float,
        soru_analizi: TurkceIRTSoruAnalizi,
        ogrenci_profili: OgrenciMorfolojiProfili,
    ) -> float:
        """Soru-öğrenci uygunluğunu hesapla"""
        # Hedef başarı oranına yakınlık
        basari_yakinligi = 1.0 - abs(basari_olasiligi - hedef_basari_orani)

        # Soru kalitesi faktörü
        kalite_faktoru = soru_analizi.get_soru_kalite_skoru() / 100.0

        # Morfoloji uyumu
        morfoloji_uyumu = await self._hesapla_morfoloji_uyumu(
            soru_analizi.morfoloji_analizi, ogrenci_profili
        )

        # Ağırlıklı kombinasyon
        uygunluk = basari_yakinligi * 0.4 + kalite_faktoru * 0.3 + morfoloji_uyumu * 0.3

        return uygunluk

    async def _hesapla_morfoloji_uyumu(
        self,
        soru_morfoloji: SoruMorfolojiAnalizi,
        ogrenci_profili: OgrenciMorfolojiProfili,
    ) -> float:
        """Morfoloji uyumunu hesapla"""
        # Öğrenci genel morfoloji yetkinliği
        ogrenci_yetkinlik = ogrenci_profili.hesapla_genel_morfoloji_yetkinligi()

        # Soru morfoloji zorluğu (0-1 arası normalize)
        soru_zorlugu = soru_morfoloji.ortalama_morfoloji_skoru / 10.0

        # Uyum hesaplama (öğrenci yetkinliği ile soru zorluğu arasındaki uyum)
        uyum = 1.0 - abs(ogrenci_yetkinlik - soru_zorlugu)

        return max(0.0, min(1.0, uyum))

    async def _hesapla_toplu_istatistikler(
        self, analiz_sonuclari: List[TurkceIRTSoruAnalizi]
    ) -> Dict[str, Any]:
        """Toplu istatistikleri hesapla"""
        if not analiz_sonuclari:
            return {}

        # Kalite skorları
        kalite_skorlari = [
            analiz.get_soru_kalite_skoru() for analiz in analiz_sonuclari
        ]

        # IRT parametreleri
        discrimination_values = [
            analiz.irt_parametreleri.discrimination for analiz in analiz_sonuclari
        ]
        difficulty_values = [
            analiz.irt_parametreleri.difficulty for analiz in analiz_sonuclari
        ]
        morfoloji_faktorleri = [
            analiz.irt_parametreleri.morfoloji_faktoru for analiz in analiz_sonuclari
        ]

        # Morfoloji skorları
        morfoloji_skorlari = [
            analiz.morfoloji_analizi.ortalama_morfoloji_skoru
            for analiz in analiz_sonuclari
        ]

        return {
            "ortalama_kalite_skoru": sum(kalite_skorlari) / len(kalite_skorlari),
            "ortalama_ayirt_edicilik": sum(discrimination_values)
            / len(discrimination_values),
            "ortalama_zorluk": sum(difficulty_values) / len(difficulty_values),
            "ortalama_morfoloji_faktoru": sum(morfoloji_faktorleri)
            / len(morfoloji_faktorleri),
            "ortalama_morfoloji_skoru": sum(morfoloji_skorlari)
            / len(morfoloji_skorlari),
            "kalite_standart_sapma": self._hesapla_standart_sapma(kalite_skorlari),
            "zorluk_standart_sapma": self._hesapla_standart_sapma(difficulty_values),
            "morfoloji_standart_sapma": self._hesapla_standart_sapma(
                morfoloji_skorlari
            ),
        }

    def _hesapla_standart_sapma(self, degerler: List[float]) -> float:
        """Standart sapma hesapla"""
        if len(degerler) < 2:
            return 0.0

        ortalama = sum(degerler) / len(degerler)
        varyans = sum((x - ortalama) ** 2 for x in degerler) / len(degerler)
        return varyans**0.5

    def _karsilastir_ayirt_edicilik(
        self, deger: float, standartlar: Dict
    ) -> Dict[str, Any]:
        """Ayırt edicilik karşılaştırması"""
        if deger >= standartlar["ayirt_edicilik_ideal"]:
            durum = "ideal"
            skor = 100.0
        elif deger >= standartlar["ayirt_edicilik_min"]:
            durum = "kabul_edilebilir"
            skor = 70.0
        else:
            durum = "yetersiz"
            skor = 30.0

        return {"durum": durum, "skor": skor, "deger": deger}

    def _karsilastir_zorluk(self, deger: float, standartlar: Dict) -> Dict[str, Any]:
        """Zorluk karşılaştırması"""
        min_z, max_z = standartlar["zorluk_araligi"]

        if min_z <= deger <= max_z:
            durum = "uygun"
            skor = 100.0
        elif min_z - 0.5 <= deger <= max_z + 0.5:
            durum = "kabul_edilebilir"
            skor = 70.0
        else:
            durum = "uygun_degil"
            skor = 30.0

        return {"durum": durum, "skor": skor, "deger": deger}

    def _karsilastir_sans_faktoru(
        self, deger: float, standartlar: Dict
    ) -> Dict[str, Any]:
        """Şans faktörü karşılaştırması"""
        if deger <= standartlar["sans_faktoru_max"]:
            durum = "uygun"
            skor = 100.0
        elif deger <= standartlar["sans_faktoru_max"] + 0.1:
            durum = "kabul_edilebilir"
            skor = 70.0
        else:
            durum = "yuksek"
            skor = 30.0

        return {"durum": durum, "skor": skor, "deger": deger}

    def _hesapla_genel_uyum_skoru(self, karsilastirma: Dict) -> float:
        """Genel uyum skorunu hesapla"""
        skorlar = [
            karsilastirma["ayirt_edicilik_durumu"]["skor"],
            karsilastirma["zorluk_durumu"]["skor"],
            karsilastirma["sans_faktoru_durumu"]["skor"],
        ]
        return sum(skorlar) / len(skorlar)

    def _belirle_karsilastirma_sonucu(
        self, osym_karsilastirma: Dict, ets_karsilastirma: Dict
    ) -> str:
        """Karşılaştırma sonucunu belirle"""
        osym_skor = osym_karsilastirma["genel_uyum_skoru"]
        ets_skor = ets_karsilastirma["genel_uyum_skoru"]

        if osym_skor >= 90 and ets_skor >= 90:
            return "Her iki standardı da aşıyor"
        elif osym_skor >= 70 and ets_skor >= 70:
            return "Her iki standarda da uygun"
        elif osym_skor >= 70 or ets_skor >= 70:
            return "Bir standarda uygun"
        else:
            return "Standartların altında"

    async def _olustur_karsilastirma_onerileri(
        self, soru_analizi: TurkceIRTSoruAnalizi
    ) -> List[str]:
        """Karşılaştırma önerileri oluştur"""
        oneriler = []

        # Mevcut iyileştirme önerilerini al
        oneriler.extend(soru_analizi.iyilestirme_onerileri)

        # Morfoloji avantajı vurgusu
        oneriler.append(
            "Türkçe morfoloji analizi ile ÖSYM/ETS'nin sunmadığı detaylı dil analizi avantajı"
        )

        return oneriler

    def get_servis_istatistikleri(self) -> Dict[str, Any]:
        """Servis istatistiklerini döndür"""
        basari_orani = (
            self.basarili_kalibrasyon_sayisi / max(1, self.analiz_sayisi) * 100
        )

        return {
            "toplam_analiz_sayisi": self.analiz_sayisi,
            "basarili_kalibrasyon_sayisi": self.basarili_kalibrasyon_sayisi,
            "basari_orani": basari_orani,
            "ortalama_analiz_suresi_saniye": self.ortalama_analiz_suresi,
            "cache_boyutu": len(self.soru_analizleri),
            "zemberek_istatistikleri": self.zemberek_service.get_morfoloji_istatistikleri(),
            "minimum_kalite_skoru": self.minimum_kalite_skoru,
            "minimum_ayirt_edicilik": self.minimum_ayirt_edicilik,
            "maksimum_morfoloji_faktoru": self.maksimum_morfoloji_faktoru,
        }
