#!/usr/bin/env python3
"""
Soru Bankası ve IRT Analiz Test Scripti
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SoruRepository, database_health_check, get_async_session_context
from services.irt_analysis_service import irt_analysis_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_soru_bankasi_statistics():
    """Soru bankası istatistiklerini test et"""
    logger.info("[CHART] Soru bankası istatistikleri kontrol ediliyor...")

    async with get_async_session_context() as session:
        soru_repo = SoruRepository(session)

        # Toplam soru sayısı
        tum_sorular = await soru_repo.get_sorular_by_konu("matematik", limit=1000)
        matematik_sayisi = len(tum_sorular)

        tum_sorular = await soru_repo.get_sorular_by_konu("turkce", limit=1000)
        turkce_sayisi = len(tum_sorular)

        tum_sorular = await soru_repo.get_sorular_by_konu("fizik", limit=1000)
        fizik_sayisi = len(tum_sorular)

        tum_sorular = await soru_repo.get_sorular_by_konu("ingilizce", limit=1000)
        ingilizce_sayisi = len(tum_sorular)

        logger.info(f"[BOOKS] Konu bazlı soru sayıları:")
        logger.info(f"   - Matematik: {matematik_sayisi} soru")
        logger.info(f"   - Türkçe: {turkce_sayisi} soru")
        logger.info(f"   - Fizik: {fizik_sayisi} soru")
        logger.info(f"   - İngilizce: {ingilizce_sayisi} soru")

        # Zorluk seviyesi dağılımı
        matematik_sorulari = await soru_repo.get_sorular_by_konu("matematik", limit=500)

        zorluk_dagilimi = {}
        irt_istatistikleri = {"a": [], "b": [], "c": []}
        morfoloji_istatistikleri = []

        for soru in matematik_sorulari:
            # Zorluk dağılımı
            zorluk = soru.zorluk_seviyesi.value
            if zorluk not in zorluk_dagilimi:
                zorluk_dagilimi[zorluk] = 0
            zorluk_dagilimi[zorluk] += 1

            # IRT parametreleri
            if soru.irt_a_parametresi:
                irt_istatistikleri["a"].append(soru.irt_a_parametresi)
            if soru.irt_b_parametresi:
                irt_istatistikleri["b"].append(soru.irt_b_parametresi)
            if soru.irt_c_parametresi:
                irt_istatistikleri["c"].append(soru.irt_c_parametresi)

            # Morfoloji karmaşıklığı
            if soru.morfoloji_karmasikligi:
                morfoloji_istatistikleri.append(soru.morfoloji_karmasikligi)

        logger.info(f"[TARGET] Matematik soruları zorluk dağılımı:")
        for zorluk, sayi in zorluk_dagilimi.items():
            logger.info(f"   - {zorluk}: {sayi} soru")

        # IRT parametreleri istatistikleri
        if irt_istatistikleri["a"]:
            a_params = irt_istatistikleri["a"]
            b_params = irt_istatistikleri["b"]
            c_params = irt_istatistikleri["c"]

            logger.info(f"🧮 IRT Parametreleri (Matematik):")
            logger.info(
                f"   - a (ayırt edicilik): min={min(a_params):.3f}, max={max(a_params):.3f}, ort={sum(a_params)/len(a_params):.3f}"
            )
            logger.info(
                f"   - b (zorluk): min={min(b_params):.3f}, max={max(b_params):.3f}, ort={sum(b_params)/len(b_params):.3f}"
            )
            logger.info(
                f"   - c (şans): min={min(c_params):.3f}, max={max(c_params):.3f}, ort={sum(c_params)/len(c_params):.3f}"
            )

        # Morfoloji istatistikleri
        if morfoloji_istatistikleri:
            logger.info(f"🔤 Morfoloji Karmaşıklığı (Matematik):")
            logger.info(
                f"   - min={min(morfoloji_istatistikleri):.3f}, max={max(morfoloji_istatistikleri):.3f}, ort={sum(morfoloji_istatistikleri)/len(morfoloji_istatistikleri):.3f}"
            )


async def test_irt_analysis():
    """IRT analiz servisini test et"""
    logger.info("🧪 IRT analiz servisi test ediliyor...")

    async with get_async_session_context() as session:
        soru_repo = SoruRepository(session)

        # Test için bir matematik sorusu seç
        matematik_sorulari = await soru_repo.get_sorular_by_konu("matematik", limit=5)

        if not matematik_sorulari:
            logger.warning("Test için matematik sorusu bulunamadı")
            return

        test_soru = matematik_sorulari[0]
        logger.info(f"[TARGET] Test sorusu: {test_soru.soru_metni[:50]}...")

        # IRT analizi yap
        try:
            irt_result = await irt_analysis_service.analyze_soru_irt_parameters(
                test_soru.soru_id
            )

            logger.info(f"[CHART] IRT Analiz Sonuçları:")
            logger.info(f"   - Discrimination (a): {irt_result.discrimination:.3f}")
            logger.info(f"   - Difficulty (b): {irt_result.difficulty:.3f}")
            logger.info(f"   - Guessing (c): {irt_result.guessing:.3f}")
            logger.info(f"   - Morfoloji etkisi: {irt_result.morfoloji_etkisi:.3f}")
            logger.info(f"   - Kalibrasyon güveni: {irt_result.kalibrasyon_guveni:.3f}")
            logger.info(f"   - Önerilen zorluk: {irt_result.onerilen_zorluk.value}")

        except Exception as e:
            logger.error(f"[X] IRT analiz hatası: {str(e)}")


async def test_student_ability_calculation():
    """Öğrenci yetenek seviyesi hesaplama testi"""
    logger.info(
        "👨‍[GRADUATION_CAP] Öğrenci yetenek seviyesi hesaplama test ediliyor..."
    )

    try:
        # Test öğrenci ID'si
        test_ogrenci_id = "test_student_123"

        # Yetenek seviyesi hesapla
        ability_result = await irt_analysis_service.calculate_student_ability(
            test_ogrenci_id
        )

        logger.info(f"[TARGET] Öğrenci Yetenek Analizi:")
        logger.info(f"   - Öğrenci ID: {ability_result.ogrenci_id}")
        logger.info(f"   - Theta (yetenek): {ability_result.theta:.3f}")
        logger.info(f"   - Standard Error: {ability_result.standard_error:.3f}")
        logger.info(
            f"   - Güven Aralığı: ({ability_result.guven_araligi[0]:.3f}, {ability_result.guven_araligi[1]:.3f})"
        )

        logger.info(f"[BOOKS] Konu Bazlı Yetenekler:")
        for konu, yetenek in ability_result.konu_bazli_yetenekler.items():
            logger.info(f"   - {konu}: {yetenek:.3f}")

    except Exception as e:
        logger.error(f"[X] Yetenek hesaplama hatası: {str(e)}")


async def test_adaptive_test_generation():
    """Adaptif test üretimi testi"""
    logger.info("🎲 Adaptif test üretimi test ediliyor...")

    try:
        # Test parametreleri
        test_ogrenci_id = "test_student_456"
        test_konu = "matematik"
        soru_sayisi = 10

        # Adaptif test soruları üret
        adaptif_sorular = await irt_analysis_service.generate_adaptive_test_questions(
            ogrenci_id=test_ogrenci_id,
            konu=test_konu,
            soru_sayisi=soru_sayisi,
            target_theta=0.5,  # Orta seviye öğrenci
        )

        logger.info(f"[TARGET] Adaptif Test Sonuçları:")
        logger.info(f"   - Öğrenci ID: {test_ogrenci_id}")
        logger.info(f"   - Konu: {test_konu}")
        logger.info(f"   - Seçilen soru sayısı: {len(adaptif_sorular)}")

        # Zorluk dağılımını analiz et
        zorluk_dagilimi = {}
        bilgi_degerleri = []

        for soru in adaptif_sorular:
            zorluk = soru["zorluk_seviyesi"]
            if zorluk not in zorluk_dagilimi:
                zorluk_dagilimi[zorluk] = 0
            zorluk_dagilimi[zorluk] += 1

            bilgi_degerleri.append(soru["bilgi_degeri"])

        logger.info(f"[CHART] Seçilen Soruların Zorluk Dağılımı:")
        for zorluk, sayi in zorluk_dagilimi.items():
            logger.info(f"   - {zorluk}: {sayi} soru")

        if bilgi_degerleri:
            logger.info(f"[BULB] Bilgi Değeri İstatistikleri:")
            logger.info(
                f"   - min={min(bilgi_degerleri):.3f}, max={max(bilgi_degerleri):.3f}, ort={sum(bilgi_degerleri)/len(bilgi_degerleri):.3f}"
            )

        # İlk 3 soruyu detaylı göster
        logger.info(f"[MAG] İlk 3 Seçilen Soru:")
        for i, soru in enumerate(adaptif_sorular[:3]):
            logger.info(f"   {i+1}. {soru['soru_metni'][:60]}...")
            logger.info(
                f"      Zorluk: {soru['zorluk_seviyesi']}, Bilgi: {soru['bilgi_degeri']:.3f}"
            )

    except Exception as e:
        logger.error(f"[X] Adaptif test üretim hatası: {str(e)}")


async def test_difficulty_calibration():
    """Zorluk kalibrasyonu testi"""
    logger.info("⚖️ Zorluk kalibrasyonu test ediliyor...")

    async with get_async_session_context() as session:
        soru_repo = SoruRepository(session)

        # Test için bir soru seç
        matematik_sorulari = await soru_repo.get_sorular_by_konu("matematik", limit=3)

        if not matematik_sorulari:
            logger.warning("Test için matematik sorusu bulunamadı")
            return

        test_soru = matematik_sorulari[0]
        logger.info(f"[TARGET] Kalibrasyon test sorusu: {test_soru.soru_metni[:50]}...")

        try:
            # Mevcut parametreleri göster
            logger.info(f"[CHART] Mevcut IRT Parametreleri:")
            logger.info(f"   - a: {test_soru.irt_a_parametresi}")
            logger.info(f"   - b: {test_soru.irt_b_parametresi}")
            logger.info(f"   - c: {test_soru.irt_c_parametresi}")
            logger.info(f"   - Zorluk seviyesi: {test_soru.zorluk_seviyesi.value}")

            # Zorluk kalibrasyonu yap
            target_difficulty = 1.0  # Zor seviye

            kalibrasyon_result = await irt_analysis_service.calibrate_soru_difficulty(
                soru_id=test_soru.soru_id,
                target_difficulty=target_difficulty,
                morphology_adjustment=True,
            )

            logger.info(f"⚖️ Kalibrasyon Sonuçları:")
            logger.info(f"   - Hedef zorluk: {target_difficulty}")
            logger.info(
                f"   - Eski parametreler: {kalibrasyon_result['old_parameters']}"
            )
            logger.info(
                f"   - Yeni parametreler: {kalibrasyon_result['new_parameters']}"
            )
            logger.info(
                f"   - Yeni zorluk seviyesi: {kalibrasyon_result['new_difficulty_level']}"
            )
            logger.info(
                f"   - Morfoloji ayarlaması: {kalibrasyon_result['morphology_adjusted']}"
            )

        except Exception as e:
            logger.error(f"[X] Kalibrasyon hatası: {str(e)}")


async def main():
    """Ana test fonksiyonu"""
    logger.info("[ROCKET] Soru bankası ve IRT analiz testleri başlatılıyor...")

    try:
        # Database sağlık kontrolü
        health = await database_health_check()
        logger.info(f"[CHART] Database durumu: {health['status']}")

        if health["status"] != "healthy":
            logger.error("[X] Database bağlantısı sağlıklı değil!")
            return

        # Testleri çalıştır
        await test_soru_bankasi_statistics()
        await test_irt_analysis()
        await test_student_ability_calculation()
        await test_adaptive_test_generation()
        await test_difficulty_calibration()

        logger.info("[CHECK] Tüm testler başarıyla tamamlandı!")

    except Exception as e:
        logger.error(f"[X] Test hatası: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
