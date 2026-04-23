"""
Zone of Proximal Development + MEB Maarif Servisi - DEVRİMSEL
Türk eğitim kültürüne uyarlanmış ZPD hesaplama servisi

Bu servis Vygotsky'nin ZPD teorisini MEB Maarif modeli ile birleştirerek
Türk öğrenci psikolojisine özel optimal zorluk seviyesi belirleme sistemi sunar.

DEVRİMSEL ÖZELLİKLER:
- Türk kültürü faktörleri entegrasyonu
- MEB Maarif değerleri uyum sistemi
- Grup vs bireysel öğrenme dengeleme
- Kültürel bağlam farkındalıklı ZPD hesaplama
"""

import logging
from datetime import datetime
from typing import Any

# Yeni devrimsel algoritma entegrasyonu
from algorithms.turkish_zpd_maarif_system import (
    MaarifAlignment,
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
    TurkishZPDRange,
    ZPDRecommendation,
)

# PERFORMANCE: Cache integration for ZPD calculations
from core.cache import cache_manager
from models.zpd_maarif import (
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    TurkZPDAraligi,
    ZPDHesaplamaGecmisi,
    ZPDHesaplamaParametreleri,
    ZPDOptimizasyonSonucu,
)

logger = logging.getLogger(__name__)


class ZPDMaarifService:
    """
    Türk eğitim kültürüne uyarlanmış ZPD hesaplama servisi - DEVRİMSEL

    Bu servis şu devrimsel özellikleri sunar:
    1. Vygotsky ZPD + MEB Maarif değerleri entegrasyonu
    2. Türk öğrenci kültürü faktörleri analizi
    3. Kültürel bağlam farkındalıklı ZPD hesaplama
    4. Grup çalışması ve bireysel öğrenme dengeleme
    5. Gerçek zamanlı kültürel adaptasyon
    """

    def __init__(self) -> None:
        """ZPD Maarif servisini başlat."""
        self.default_parametreler: ZPDHesaplamaParametreleri = (
            ZPDHesaplamaParametreleri()
        )
        self.hesaplama_gecmisi: dict[str, list[ZPDHesaplamaGecmisi]] = {}

        # DEVRİMSEL: Yeni algoritma sistemi
        self.turkish_zpd_system = TurkishZPDMaarifSystem()

        # Türk kültürü varsayılan değerleri
        self.varsayilan_kulturel_profil = {
            "grup_calismasi_tercihi": 0.8,
            "ogretmene_saygi_seviyesi": 0.9,
            "aile_katilim_derecesi": 0.7,
            "akran_rekabet_egilimi": 0.6,
            "otorite_kabul_seviyesi": 0.8,
            "toplumsal_onay_ihtiyaci": 0.6,
            "basari_odaklilik": 0.8,
            "kolektif_kimlik_gucu": 0.7,
        }

        # MEB Maarif varsayılan değerleri
        self.varsayilan_maarif_profili = {
            # Milli değerler
            "vatan_sevgisi": 0.8,
            "millet_bilinci": 0.7,
            "aile_birligi": 0.9,
            "bayrak_sevgisi": 0.8,
            "istiklal_ruhu": 0.7,
            # Evrensel değerler
            "adalet": 0.8,
            "dostluk": 0.9,
            "durustluk": 0.8,
            "ozgurluk": 0.7,
            "esitlik": 0.8,
            "baris": 0.9,
            # Kök değerler
            "sabir": 0.7,
            "saygi": 0.9,
            "sevgi": 0.8,
            "sorumluluk": 0.8,
            "duyarlilik": 0.7,
            "hosgoru": 0.8,
        }

    async def hesapla_turk_zpd(
        self,
        ogrenci_id: str,
        konu: str,
        mevcut_seviye: float,
        kulturel_profil: KulturelBaglamProfili | None = None,
        maarif_profili: MaarifDegerleriProfili | None = None,
        parametreler: ZPDHesaplamaParametreleri | None = None,
    ) -> TurkZPDAraligi:
        """
        Türk eğitim kültürüne uyarlanmış ZPD aralığı hesapla

        Args:
            ogrenci_id: Öğrenci kimliği
            konu: Konu adı
            mevcut_seviye: Öğrencinin mevcut seviyesi (0-10)
            kulturel_profil: Kültürel bağlam profili
            maarif_profili: MEB Maarif değerleri profili
            parametreler: Hesaplama parametreleri

        Returns:
            TurkZPDAraligi: Hesaplanmış ZPD aralığı
        """
        try:
            # Input validation
            if not ogrenci_id:
                ogrenci_id = "anonymous_student"

            if not konu:
                konu = "genel"

            # Mevcut seviye sınırlarını kontrol et ve düzelt
            if mevcut_seviye < 0.0:
                logger.warning(
                    f"Mevcut seviye negatif ({mevcut_seviye}), 0.0 olarak ayarlandı"
                )
                mevcut_seviye = 0.0
            elif mevcut_seviye > 10.0:
                logger.warning(
                    f"Mevcut seviye çok yüksek ({mevcut_seviye}), 10.0 olarak ayarlandı"
                )
                mevcut_seviye = 10.0

            # PERFORMANCE: Cache check
            cache_key = f"zpd_maarif:{ogrenci_id}:{konu}:{mevcut_seviye}"
            cached_zpd = await cache_manager.get(cache_key)
            if cached_zpd:
                logger.info(f"ZPD cache hit: {ogrenci_id}/{konu}")
                return (
                    TurkZPDAraligi(**cached_zpd)
                    if isinstance(cached_zpd, dict)
                    else cached_zpd
                )
            # Varsayılan profilleri kullan
            if kulturel_profil is None:
                kulturel_profil = await self._olustur_varsayilan_kulturel_profil(
                    ogrenci_id
                )

            if maarif_profili is None:
                maarif_profili = await self._olustur_varsayilan_maarif_profili(
                    ogrenci_id
                )

            if parametreler is None:
                parametreler = self.default_parametreler

            # Temel ZPD aralığını hesapla
            temel_zpd_genisligi = mevcut_seviye * parametreler.temel_zpd_genisligi

            # Kültürel ayarlamaları hesapla
            kulturel_carpan = await self._hesapla_kulturel_carpan(
                kulturel_profil, parametreler
            )

            # MEB Maarif uyum katsayısını hesapla
            maarif_uyum = await self._hesapla_maarif_uyum_katsayisi(
                maarif_profili, konu, parametreler
            )

            # Grup çalışması bonusunu hesapla
            grup_bonusu = await self._hesapla_grup_calismasi_bonusu(
                kulturel_profil, parametreler
            )

            # Öğretmen rehberlik faktörünü hesapla
            ogretmen_faktoru = await self._hesapla_ogretmen_rehberlik_faktoru(
                kulturel_profil, parametreler
            )

            # ZPD sınırlarını hesapla
            ayarlanmis_genislik = temel_zpd_genisligi * kulturel_carpan
            alt_sinir = max(0.0, mevcut_seviye - 0.5)
            ust_sinir = min(10.0, mevcut_seviye + ayarlanmis_genislik)
            optimal_zorluk = mevcut_seviye + (
                ayarlanmis_genislik * parametreler.optimal_zorluk_orani
            )

            # Grup çalışması ve öğretmen rehberlik bonuslarını uygula
            if grup_bonusu > 0:
                ust_sinir = min(10.0, ust_sinir + grup_bonusu)
                optimal_zorluk = min(ust_sinir, optimal_zorluk + grup_bonusu * 0.7)

            if ogretmen_faktoru > 0:
                ust_sinir = min(10.0, ust_sinir + ogretmen_faktoru)
                optimal_zorluk = min(ust_sinir, optimal_zorluk + ogretmen_faktoru * 0.8)

            # Güven seviyelerini hesapla
            hesaplama_guveni = await self._hesapla_hesaplama_guveni(
                kulturel_profil, maarif_profili
            )
            kulturel_uyum_guveni = await self._hesapla_kulturel_uyum_guveni(
                kulturel_profil
            )

            # ZPD aralığını oluştur
            zpd_araligi = TurkZPDAraligi(
                ogrenci_id=ogrenci_id,
                konu=konu,
                mevcut_seviye=mevcut_seviye,
                alt_sinir=alt_sinir,
                ust_sinir=ust_sinir,
                optimal_zorluk=optimal_zorluk,
                kulturel_carpan=kulturel_carpan,
                maarif_uyum_katsayisi=maarif_uyum,
                grup_calismasi_bonusu=grup_bonusu,
                ogretmen_rehberlik_faktoru=ogretmen_faktoru,
                hesaplama_guveni=hesaplama_guveni,
                kulturel_uyum_guveni=kulturel_uyum_guveni,
            )

            # Hesaplama geçmişine kaydet
            await self._kaydet_hesaplama_gecmisi(
                zpd_araligi, parametreler, kulturel_profil, maarif_profili
            )

            # PERFORMANCE: Save to cache (30 min TTL)
            zpd_dict = {
                "ogrenci_id": zpd_araligi.ogrenci_id,
                "konu": zpd_araligi.konu,
                "mevcut_seviye": zpd_araligi.mevcut_seviye,
                "alt_sinir": zpd_araligi.alt_sinir,
                "ust_sinir": zpd_araligi.ust_sinir,
                "optimal_zorluk": zpd_araligi.optimal_zorluk,
                "kulturel_carpan": zpd_araligi.kulturel_carpan,
                "maarif_uyum_katsayisi": zpd_araligi.maarif_uyum_katsayisi,
                "grup_calismasi_bonusu": zpd_araligi.grup_calismasi_bonusu,
                "ogretmen_rehberlik_faktoru": zpd_araligi.ogretmen_rehberlik_faktoru,
                "hesaplama_guveni": zpd_araligi.hesaplama_guveni,
                "kulturel_uyum_guveni": zpd_araligi.kulturel_uyum_guveni,
            }
            await cache_manager.set(cache_key, zpd_dict, ttl=1800)

            logger.info(
                f"ZPD hesaplandı - Öğrenci: {ogrenci_id}, Konu: {konu}, "
                f"Optimal: {optimal_zorluk:.2f}, Güven: {hesaplama_guveni:.2f}"
            )

            return zpd_araligi

        except Exception as e:
            logger.error(
                f"ZPD hesaplama hatası - Öğrenci: {ogrenci_id}, Hata: {e!s}"
            )
            raise

    async def optimize_zpd_parametreleri(
        self, ogrenci_id: str, konu: str, performans_verileri: list[dict[str, Any]]
    ) -> ZPDOptimizasyonSonucu:
        """
        Performans verilerine göre ZPD parametrelerini optimize et

        Args:
            ogrenci_id: Öğrenci kimliği
            konu: Konu adı
            performans_verileri: Geçmiş performans verileri

        Returns:
            ZPDOptimizasyonSonucu: Optimizasyon önerileri
        """
        try:
            # Geçmiş performansı analiz et
            basari_trendi = await self._analiz_et_basari_trendi(performans_verileri)
            zorluk_uyumu = await self._analiz_et_zorluk_uyumu(performans_verileri)
            ogrenme_hizi = await self._hesapla_ogrenme_hizi(performans_verileri)

            # Mevcut ZPD'yi al
            mevcut_zpd = await self._get_mevcut_zpd(ogrenci_id, konu)

            # Optimizasyon önerilerini hesapla
            onerilen_zorluk = await self._hesapla_onerilen_zorluk(
                mevcut_zpd, basari_trendi, zorluk_uyumu
            )

            ogrenme_yontemi = await self._belirle_optimal_ogrenme_yontemi(
                ogrenci_id, performans_verileri
            )

            grup_calismasi_onerisi = await self._degerlendirme_grup_calismasi(
                ogrenci_id, performans_verileri
            )

            ogretmen_rehberlik_ihtiyaci = await self._degerlendirme_ogretmen_rehberlik(
                ogrenci_id, performans_verileri
            )

            # İçerik türü önerilerini belirle
            icerik_onerileri = await self._oneriler_icerik_turu(
                ogrenci_id, konu, performans_verileri
            )

            # Motivasyon stratejilerini belirle
            motivasyon_stratejileri = await self._belirle_motivasyon_stratejileri(
                ogrenci_id, performans_verileri
            )

            # Güven metriklerini hesapla
            oneri_guveni = await self._hesapla_oneri_guveni(performans_verileri)
            beklenen_basari_artisi = await self._tahmin_et_basari_artisi(
                performans_verileri, onerilen_zorluk
            )

            optimizasyon_sonucu = ZPDOptimizasyonSonucu(
                ogrenci_id=ogrenci_id,
                konu=konu,
                onerilen_zorluk_seviyesi=onerilen_zorluk,
                onerilen_ogrenme_yontemi=ogrenme_yontemi,
                grup_calismasi_onerisi=grup_calismasi_onerisi,
                ogretmen_rehberlik_ihtiyaci=ogretmen_rehberlik_ihtiyaci,
                icerik_turu_onerileri=icerik_onerileri,
                ogrenme_hizi_ayarlama=ogrenme_hizi,
                motivasyon_stratejileri=motivasyon_stratejileri,
                oneri_guveni=oneri_guveni,
                beklenen_basari_artisi=beklenen_basari_artisi,
            )

            logger.info(
                f"ZPD optimizasyonu tamamlandı - Öğrenci: {ogrenci_id}, "
                f"Önerilen zorluk: {onerilen_zorluk:.2f}"
            )

            return optimizasyon_sonucu

        except Exception as e:
            logger.error(
                f"ZPD optimizasyon hatası - Öğrenci: {ogrenci_id}, Hata: {e!s}"
            )
            raise

    # Yardımcı metodlar
    async def _olustur_varsayilan_kulturel_profil(
        self, ogrenci_id: str
    ) -> KulturelBaglamProfili:
        """Varsayılan kültürel profil oluştur"""
        return KulturelBaglamProfili(
            ogrenci_id=ogrenci_id, **self.varsayilan_kulturel_profil
        )

    async def _olustur_varsayilan_maarif_profili(
        self, ogrenci_id: str
    ) -> MaarifDegerleriProfili:
        """Varsayılan MEB Maarif profili oluştur"""
        return MaarifDegerleriProfili(
            ogrenci_id=ogrenci_id, **self.varsayilan_maarif_profili
        )

    async def _hesapla_kulturel_carpan(
        self,
        kulturel_profil: KulturelBaglamProfili,
        parametreler: ZPDHesaplamaParametreleri,
    ) -> float:
        """Kültürel faktörlere göre çarpan hesapla"""
        carpan = 1.0

        # Grup çalışması tercihi
        if kulturel_profil.grup_calismasi_tercihi > 0.7:
            carpan += (
                parametreler.grup_calismasi_agirligi
                * kulturel_profil.grup_calismasi_tercihi
            )

        # Öğretmene saygı
        if kulturel_profil.ogretmene_saygi_seviyesi > 0.8:
            carpan += (
                parametreler.ogretmen_saygi_agirligi
                * kulturel_profil.ogretmene_saygi_seviyesi
            )

        # Aile katılımı
        carpan += (
            parametreler.aile_katilim_agirligi * kulturel_profil.aile_katilim_derecesi
        )

        # Akran rekabeti
        carpan += (
            parametreler.akran_rekabet_agirligi * kulturel_profil.akran_rekabet_egilimi
        )

        return min(2.0, max(0.5, carpan))  # 0.5-2.0 arası sınırla

    async def _hesapla_maarif_uyum_katsayisi(
        self,
        maarif_profili: MaarifDegerleriProfili,
        konu: str,
        parametreler: ZPDHesaplamaParametreleri,
    ) -> float:
        """MEB Maarif değerlerine göre uyum katsayısı hesapla"""

        # Konu bazlı değer ağırlıkları
        konu_deger_agirliklari = await self._get_konu_deger_agirliklari(konu)

        # Milli değerler uyumu
        milli_uyum = maarif_profili.get_milli_degerler_ortalamasi()
        milli_uyum *= konu_deger_agirliklari.get("milli", 1.0)

        # Evrensel değerler uyumu
        evrensel_uyum = maarif_profili.get_evrensel_degerler_ortalamasi()
        evrensel_uyum *= konu_deger_agirliklari.get("evrensel", 1.0)

        # Kök değerler uyumu
        kok_uyum = maarif_profili.get_kok_degerler_ortalamasi()
        kok_uyum *= konu_deger_agirliklari.get("kok", 1.0)

        # Ağırlıklı ortalama
        toplam_uyum = (
            milli_uyum * parametreler.milli_degerler_agirligi
            + evrensel_uyum * parametreler.evrensel_degerler_agirligi
            + kok_uyum * parametreler.kok_degerler_agirligi
        )

        return min(1.0, max(0.0, toplam_uyum))

    async def _get_konu_deger_agirliklari(self, konu: str) -> dict[str, float]:
        """Konu bazlı değer ağırlıklarını getir"""
        # Tarih konularında milli değerler daha önemli
        if "tarih" in konu.lower() or "atatürk" in konu.lower():
            return {"milli": 1.3, "evrensel": 1.0, "kok": 1.1}

        # Matematik/Fen konularında evrensel değerler önemli
        if any(
            x in konu.lower() for x in ["matematik", "fizik", "kimya", "biyoloji"]
        ):
            return {"milli": 1.0, "evrensel": 1.2, "kok": 1.0}

        # Türkçe/Edebiyat konularında kök değerler önemli
        if any(x in konu.lower() for x in ["türkçe", "edebiyat", "dil"]):
            return {"milli": 1.1, "evrensel": 1.0, "kok": 1.3}

        # Varsayılan ağırlıklar
        return {"milli": 1.0, "evrensel": 1.0, "kok": 1.0}

    async def _hesapla_grup_calismasi_bonusu(
        self,
        kulturel_profil: KulturelBaglamProfili,
        parametreler: ZPDHesaplamaParametreleri,
    ) -> float:
        """Grup çalışması bonusunu hesapla"""
        if kulturel_profil.grup_calismasi_tercihi > 0.7:
            bonus = kulturel_profil.grup_calismasi_tercihi * 0.2
            # Kolektif kimlik gücü de bonus artırır
            bonus *= 1 + kulturel_profil.kolektif_kimlik_gucu * 0.1
            return min(0.5, bonus)
        return 0.0

    async def _hesapla_ogretmen_rehberlik_faktoru(
        self,
        kulturel_profil: KulturelBaglamProfili,
        parametreler: ZPDHesaplamaParametreleri,
    ) -> float:
        """Öğretmen rehberlik faktörünü hesapla"""
        if kulturel_profil.ogretmene_saygi_seviyesi > 0.8:
            faktor = kulturel_profil.ogretmene_saygi_seviyesi * 0.15
            # Otorite kabul seviyesi de faktörü artırır
            faktor *= 1 + kulturel_profil.otorite_kabul_seviyesi * 0.1
            return min(0.3, faktor)
        return 0.0

    async def _hesapla_hesaplama_guveni(
        self,
        kulturel_profil: KulturelBaglamProfili,
        maarif_profili: MaarifDegerleriProfili,
    ) -> float:
        """Hesaplama güvenini hesapla"""
        # Basit güven hesaplama
        return 0.8

    async def _hesapla_kulturel_uyum_guveni(
        self, kulturel_profil: KulturelBaglamProfili
    ) -> float:
        """Kültürel uyum güvenini hesapla"""
        # Basit uyum güveni hesaplama
        return 0.75

    async def _kaydet_hesaplama_gecmisi(
        self,
        zpd_araligi: TurkZPDAraligi,
        parametreler: ZPDHesaplamaParametreleri,
        kulturel_profil: KulturelBaglamProfili,
        maarif_profili: MaarifDegerleriProfili,
    ) -> None:
        """Hesaplama geçmişini kaydet."""
        gecmis = ZPDHesaplamaGecmisi(
            ogrenci_id=zpd_araligi.ogrenci_id,
            konu=zpd_araligi.konu,
            hesaplama_tarihi=datetime.now(),
            zpd_araligi=zpd_araligi,
            kullanilan_parametreler=parametreler,
            kulturel_profil=kulturel_profil,
            maarif_profili=maarif_profili,
        )

        # Bellek içi geçmiş (gerçek uygulamada veritabanına kaydedilir)
        anahtar = f"{zpd_araligi.ogrenci_id}_{zpd_araligi.konu}"
        if anahtar not in self.hesaplama_gecmisi:
            self.hesaplama_gecmisi[anahtar] = []

        self.hesaplama_gecmisi[anahtar].append(gecmis)

        # Son 10 hesaplamayı tut
        if len(self.hesaplama_gecmisi[anahtar]) > 10:
            self.hesaplama_gecmisi[anahtar] = self.hesaplama_gecmisi[anahtar][-10:]

    # Optimizasyon yardımcı metodları
    async def _analiz_et_basari_trendi(self, performans_verileri: list[dict]) -> float:
        """Başarı trendini analiz et"""
        if len(performans_verileri) < 2:
            return 0.0

        # Son 5 performansın trendini hesapla
        son_performanslar = performans_verileri[-5:]
        basari_oranlari = [p.get("basari_orani", 0.5) for p in son_performanslar]

        # Basit trend hesaplama
        if len(basari_oranlari) >= 2:
            trend = basari_oranlari[-1] - basari_oranlari[0]
            return max(-0.5, min(0.5, trend))

        return 0.0

    async def _analiz_et_zorluk_uyumu(self, performans_verileri: list[dict]) -> float:
        """Zorluk uyumunu analiz et"""
        if not performans_verileri:
            return 0.5

        # Ortalama zorluk ve başarı oranı ilişkisi
        toplam_uyum = 0.0
        for veri in performans_verileri[-10:]:  # Son 10 veri
            zorluk = veri.get("zorluk_seviyesi", 5.0)
            basari = veri.get("basari_orani", 0.5)

            # İdeal uyum: zorluk 7-8 iken başarı 0.6-0.8
            if 7 <= zorluk <= 8 and 0.6 <= basari <= 0.8:
                toplam_uyum += 1.0
            elif 5 <= zorluk <= 9 and 0.4 <= basari <= 0.9:
                toplam_uyum += 0.7
            else:
                toplam_uyum += 0.3

        return toplam_uyum / len(performans_verileri[-10:])

    async def _hesapla_ogrenme_hizi(self, performans_verileri: list[dict]) -> float:
        """Öğrenme hızını hesapla"""
        if len(performans_verileri) < 3:
            return 1.0

        # Son 3 performanstaki gelişim hızı
        son_performanslar = performans_verileri[-3:]
        gelisim_hizi = 0.0

        for i in range(1, len(son_performanslar)):
            onceki = son_performanslar[i - 1].get("basari_orani", 0.5)
            mevcut = son_performanslar[i].get("basari_orani", 0.5)
            gelisim_hizi += mevcut - onceki

        # Normalize et (0.5 - 2.0 arası)
        hiz = 1.0 + gelisim_hizi
        return max(0.5, min(2.0, hiz))

    async def _get_mevcut_zpd(
        self, ogrenci_id: str, konu: str
    ) -> TurkZPDAraligi | None:
        """Mevcut ZPD'yi getir"""
        anahtar = f"{ogrenci_id}_{konu}"
        gecmis_listesi = self.hesaplama_gecmisi.get(anahtar, [])

        if gecmis_listesi:
            son_gecmis = gecmis_listesi[-1]
            if son_gecmis.zpd_araligi.is_gecerli():
                return son_gecmis.zpd_araligi

        return None

    async def _hesapla_onerilen_zorluk(
        self,
        mevcut_zpd: TurkZPDAraligi | None,
        basari_trendi: float,
        zorluk_uyumu: float,
    ) -> float:
        """Önerilen zorluk seviyesini hesapla"""
        if mevcut_zpd is None:
            return 5.0  # Varsayılan orta seviye

        onerilen = mevcut_zpd.optimal_zorluk

        # Başarı trendine göre ayarla
        if basari_trendi > 0.2:  # İyi trend
            onerilen += 0.5
        elif basari_trendi < -0.2:  # Kötü trend
            onerilen -= 0.5

        # Zorluk uyumuna göre ayarla
        if zorluk_uyumu < 0.5:  # Uyum düşük
            onerilen -= 0.3
        elif zorluk_uyumu > 0.8:  # Uyum yüksek
            onerilen += 0.2

        return max(1.0, min(10.0, onerilen))

    async def _belirle_optimal_ogrenme_yontemi(
        self, ogrenci_id: str, performans_verileri: list[dict]
    ) -> str:
        """Optimal öğrenme yöntemini belirle"""
        # Performans verilerine göre en başarılı yöntemi bul
        yontem_basarilari = {}

        for veri in performans_verileri:
            yontem = veri.get("ogrenme_yontemi", "bireysel")
            basari = veri.get("basari_orani", 0.5)

            if yontem not in yontem_basarilari:
                yontem_basarilari[yontem] = []
            yontem_basarilari[yontem].append(basari)

        # En yüksek ortalama başarıya sahip yöntemi seç
        en_iyi_yontem = "bireysel"
        en_yuksek_ortalama = 0.0

        for yontem, basarilar in yontem_basarilari.items():
            ortalama = sum(basarilar) / len(basarilar)
            if ortalama > en_yuksek_ortalama:
                en_yuksek_ortalama = ortalama
                en_iyi_yontem = yontem

        return en_iyi_yontem

    async def _degerlendirme_grup_calismasi(
        self, ogrenci_id: str, performans_verileri: list[dict]
    ) -> bool:
        """Grup çalışması önerisini değerlendir"""
        # Grup çalışması verilerini analiz et
        grup_basarilari = []
        bireysel_basarilari = []

        for veri in performans_verileri:
            yontem = veri.get("ogrenme_yontemi", "bireysel")
            basari = veri.get("basari_orani", 0.5)

            if "grup" in yontem.lower():
                grup_basarilari.append(basari)
            else:
                bireysel_basarilari.append(basari)

        # Grup çalışması daha başarılıysa öner
        if grup_basarilari and bireysel_basarilari:
            grup_ortalama = sum(grup_basarilari) / len(grup_basarilari)
            bireysel_ortalama = sum(bireysel_basarilari) / len(bireysel_basarilari)
            return grup_ortalama > bireysel_ortalama + 0.1

        # Varsayılan olarak Türk kültürü grup çalışmasını destekler
        return True

    async def _degerlendirme_ogretmen_rehberlik(
        self, ogrenci_id: str, performans_verileri: list[dict]
    ) -> bool:
        """Öğretmen rehberlik ihtiyacını değerlendir"""
        if not performans_verileri:
            return False

        # Son performanslara bak
        son_basarilar = [p.get("basari_orani", 0.5) for p in performans_verileri[-5:]]
        ortalama_basari = sum(son_basarilar) / len(son_basarilar)

        # Başarı düşükse rehberlik öner
        return ortalama_basari < 0.6

    async def _oneriler_icerik_turu(
        self, ogrenci_id: str, konu: str, performans_verileri: list[dict]
    ) -> list[str]:
        """İçerik türü önerilerini belirle"""
        oneriler = []

        # Performans verilerine göre başarılı içerik türlerini bul
        icerik_basarilari = {}
        for veri in performans_verileri:
            icerik_turu = veri.get("icerik_turu", "metin")
            basari = veri.get("basari_orani", 0.5)

            if icerik_turu not in icerik_basarilari:
                icerik_basarilari[icerik_turu] = []
            icerik_basarilari[icerik_turu].append(basari)

        # Başarılı içerik türlerini öner
        for icerik_turu, basarilar in icerik_basarilari.items():
            ortalama = sum(basarilar) / len(basarilar)
            if ortalama > 0.6:
                oneriler.append(icerik_turu)

        # Varsayılan öneriler
        if not oneriler:
            oneriler = ["video", "interaktif", "metin"]

        return oneriler[:3]  # En fazla 3 öneri

    async def _belirle_motivasyon_stratejileri(
        self, ogrenci_id: str, performans_verileri: list[dict]
    ) -> list[str]:
        """Motivasyon stratejilerini belirle"""
        stratejiler = []

        if not performans_verileri:
            return ["pozitif_pekistirme", "hedef_belirleme"]

        # Son performansa göre strateji belirle
        son_basari = performans_verileri[-1].get("basari_orani", 0.5)

        if son_basari < 0.4:
            stratejiler.extend(
                ["kucuk_hedefler", "basari_kutlamasi", "sabir_gelistirme"]
            )
        elif son_basari < 0.6:
            stratejiler.extend(
                ["pozitif_pekistirme", "akran_destegi", "ilerleme_takibi"]
            )
        else:
            stratejiler.extend(
                ["zorluk_artirma", "liderlik_rolleri", "yaratici_projeler"]
            )

        # Türk kültürüne özel stratejiler
        stratejiler.extend(
            ["aile_katilimi", "toplumsal_onay", "milli_degerler_vurgusu"]
        )

        return stratejiler[:5]  # En fazla 5 strateji

    async def _hesapla_oneri_guveni(self, performans_verileri: list[dict]) -> float:
        """Öneri güvenini hesapla"""
        if len(performans_verileri) < 3:
            return 0.6  # Düşük güven
        if len(performans_verileri) < 10:
            return 0.8  # Orta güven
        return 0.9  # Yüksek güven

    async def _tahmin_et_basari_artisi(
        self, performans_verileri: list[dict], onerilen_zorluk: float
    ) -> float:
        """Beklenen başarı artışını tahmin et"""
        if not performans_verileri:
            return 0.1  # %10 artış beklentisi

        # Mevcut ortalama başarı
        mevcut_ortalama = sum(
            p.get("basari_orani", 0.5) for p in performans_verileri[-5:]
        ) / min(5, len(performans_verileri))

        # Zorluk seviyesine göre artış tahmini
        if 6 <= onerilen_zorluk <= 8:  # Optimal zorluk
            beklenen_artis = 0.15  # %15 artış
        elif 4 <= onerilen_zorluk <= 6:  # Kolay
            beklenen_artis = 0.10  # %10 artış
        else:  # Çok kolay veya çok zor
            beklenen_artis = 0.05  # %5 artış

        # Mevcut başarı seviyesine göre ayarla
        if mevcut_ortalama < 0.5:
            beklenen_artis *= 1.5  # Düşük başarıda daha fazla artış potansiyeli
        elif mevcut_ortalama > 0.8:
            beklenen_artis *= 0.7  # Yüksek başarıda daha az artış potansiyeli

        return min(0.3, max(0.05, beklenen_artis))  # %5-30 arası sınırla

    # DEVRİMSEL YENİ METODLAR

    async def detect_cultural_context_revolutionary(
        self,
        student_id: str,
        behavioral_data: dict[str, Any],
        family_survey: dict[str, Any] | None = None,
    ) -> TurkishCulturalContext:
        """
        DEVRİMSEL: Türk öğrenci kültürel bağlamını tespit et
        Yeni algoritma ile gelişmiş kültürel analiz
        """
        logger.info(f"DEVRİMSEL kültürel bağlam tespiti - Öğrenci: {student_id}")

        return await self.turkish_zpd_system.detect_cultural_context(
            student_id=student_id,
            behavioral_data=behavioral_data,
            family_survey=family_survey,
        )

    async def calculate_revolutionary_zpd(
        self,
        student_id: str,
        subject: str,
        current_level: float,
        behavioral_data: dict[str, Any],
        content_description: str = "",
        family_survey: dict[str, Any] | None = None,
    ) -> TurkishZPDRange:
        """
        DEVRİMSEL: Türk kültürüne uyarlanmış ZPD hesaplama
        Vygotsky + MEB Maarif + Türk kültürü entegrasyonu
        """
        logger.info(
            f"DEVRİMSEL ZPD hesaplama başlatıldı - Öğrenci: {student_id}, Konu: {subject}"
        )

        try:
            # Kültürel bağlamı tespit et
            cultural_context = await self.detect_cultural_context_revolutionary(
                student_id=student_id,
                behavioral_data=behavioral_data,
                family_survey=family_survey,
            )

            # DEVRİMSEL ZPD hesaplama
            zpd_range = await self.turkish_zpd_system.calculate_turkish_zpd(
                student_id=student_id,
                subject=subject,
                current_level=current_level,
                cultural_context=cultural_context,
                content_description=content_description,
            )

            logger.info(
                f"DEVRİMSEL ZPD hesaplandı - Optimal zorluk: {zpd_range.optimal_challenge:.2f}"
            )
            return zpd_range

        except Exception as e:
            logger.error(
                f"DEVRİMSEL ZPD hesaplama hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    async def generate_revolutionary_recommendation(
        self,
        student_id: str,
        subject: str,
        current_level: float,
        behavioral_data: dict[str, Any],
        learning_objective: str,
        content_description: str = "",
        family_survey: dict[str, Any] | None = None,
    ) -> ZPDRecommendation:
        """
        DEVRİMSEL: ZPD tabanlı kişiselleştirilmiş öğrenme önerisi
        Türk kültürü faktörleri ile optimize edilmiş öneriler
        """
        logger.info(
            f"DEVRİMSEL öneri oluşturma - Öğrenci: {student_id}, Hedef: {learning_objective}"
        )

        try:
            # ZPD aralığını hesapla
            zpd_range = await self.calculate_revolutionary_zpd(
                student_id=student_id,
                subject=subject,
                current_level=current_level,
                behavioral_data=behavioral_data,
                content_description=content_description,
                family_survey=family_survey,
            )

            # Kişiselleştirilmiş öneri oluştur
            recommendation = await self.turkish_zpd_system.generate_zpd_recommendation(
                zpd_range=zpd_range, learning_objective=learning_objective
            )

            logger.info(
                f"DEVRİMSEL öneri oluşturuldu - Mod: {recommendation.learning_mode}, "
                f"Zorluk: {recommendation.recommended_difficulty:.2f}"
            )

            return recommendation

        except Exception as e:
            logger.error(
                f"DEVRİMSEL öneri oluşturma hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    async def adapt_difficulty_culturally_revolutionary(
        self,
        student_id: str,
        current_difficulty: float,
        student_performance: dict[str, float],
        behavioral_data: dict[str, Any],
    ) -> float:
        """
        DEVRİMSEL: Kültürel faktörlere göre zorluk seviyesi adaptasyonu
        Türk öğrenci davranış kalıplarına göre dinamik ayarlama
        """
        logger.info(f"DEVRİMSEL zorluk adaptasyonu - Öğrenci: {student_id}")

        try:
            # Kültürel bağlamı tespit et
            cultural_context = await self.detect_cultural_context_revolutionary(
                student_id=student_id, behavioral_data=behavioral_data
            )

            # Kültürel adaptasyon uygula
            adapted_difficulty = (
                await self.turkish_zpd_system.adapt_difficulty_culturally(
                    current_difficulty=current_difficulty,
                    student_performance=student_performance,
                    cultural_context=cultural_context,
                )
            )

            logger.info(
                f"DEVRİMSEL zorluk adaptasyonu tamamlandı: {current_difficulty:.2f} → {adapted_difficulty:.2f}"
            )
            return adapted_difficulty

        except Exception as e:
            logger.error(
                f"DEVRİMSEL zorluk adaptasyon hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    async def monitor_cultural_learning_patterns_revolutionary(
        self, student_id: str, learning_sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        DEVRİMSEL: Kültürel öğrenme kalıplarını izle ve analiz et
        Türk öğrenci davranış kalıplarının derinlemesine analizi
        """
        logger.info(f"DEVRİMSEL kültürel kalıp analizi - Öğrenci: {student_id}")

        try:
            patterns = await self.turkish_zpd_system.monitor_cultural_learning_patterns(
                student_id=student_id, learning_sessions=learning_sessions
            )

            logger.info(
                f"DEVRİMSEL kültürel kalıp analizi tamamlandı - {len(patterns)} kalıp tespit edildi"
            )
            return patterns

        except Exception as e:
            logger.error(
                f"DEVRİMSEL kalıp analizi hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    async def calculate_maarif_alignment_revolutionary(
        self, subject: str, content_description: str
    ) -> MaarifAlignment:
        """
        DEVRİMSEL: İçeriğin MEB Maarif değerleri ile uyumunu hesapla
        Gelişmiş değer eşleştirme algoritması
        """
        logger.info(f"DEVRİMSEL Maarif uyum analizi - Konu: {subject}")

        try:
            alignment = await self.turkish_zpd_system.calculate_maarif_alignment(
                subject=subject, content_description=content_description
            )

            logger.info(
                f"DEVRİMSEL Maarif uyumu hesaplandı - Genel uyum: {alignment.overall_alignment:.2f}"
            )
            return alignment

        except Exception as e:
            logger.error(
                f"DEVRİMSEL Maarif uyum hatası - Konu: {subject}, Hata: {e!s}"
            )
            raise

    async def get_revolutionary_learning_balance(
        self, student_id: str, behavioral_data: dict[str, Any]
    ) -> dict[str, float]:
        """
        DEVRİMSEL: Grup vs bireysel öğrenme dengesini hesapla
        Türk kültürü faktörleri ile optimize edilmiş denge analizi
        """
        logger.info(f"DEVRİMSEL öğrenme dengesi analizi - Öğrenci: {student_id}")

        try:
            # Kültürel bağlamı tespit et
            cultural_context = await self.detect_cultural_context_revolutionary(
                student_id=student_id, behavioral_data=behavioral_data
            )

            # ZPD hesapla (örnek değerlerle)
            zpd_range = await self.turkish_zpd_system.calculate_turkish_zpd(
                student_id=student_id,
                subject="genel",
                current_level=5.0,
                cultural_context=cultural_context,
            )

            balance_info = {
                "group_individual_balance": zpd_range.group_individual_balance,
                "group_preference": cultural_context.group_learning_preference,
                "individual_preference": 1.0
                - cultural_context.group_learning_preference,
                "recommended_mode": "group"
                if zpd_range.group_individual_balance > 0.6
                else "individual"
                if zpd_range.group_individual_balance < 0.4
                else "mixed",
                "cultural_factors": {
                    "collective_success": cultural_context.collective_success,
                    "social_harmony": cultural_context.social_harmony,
                    "peer_competition": cultural_context.peer_competition,
                },
            }

            logger.info(
                f"DEVRİMSEL öğrenme dengesi: {balance_info['recommended_mode']} "
                f"(Denge: {zpd_range.group_individual_balance:.2f})"
            )

            return balance_info

        except Exception as e:
            logger.error(
                f"DEVRİMSEL öğrenme dengesi hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise
