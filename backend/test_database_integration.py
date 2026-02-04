#!/usr/bin/env python3
"""
Database Integration Test
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    KullaniciRepository,
    KullaniciRolu,
    OgrenciRepository,
    SinavRepository,
    SinavTipi,
    SoruRepository,
    database_health_check,
    get_async_session_context,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_operations():
    """Database operasyonlarını test et"""
    logger.info("🧪 Database integration testleri başlatılıyor...")

    try:
        # Health check
        health = await database_health_check()
        logger.info(f"[CHART] Database sağlık durumu: {health['status']}")
        logger.info(f"[CLIPBOARD] Toplam tablo sayısı: {health['tables']}")

        # Repository testleri
        async with get_async_session_context() as session:
            kullanici_repo = KullaniciRepository(session)
            ogrenci_repo = OgrenciRepository(session)
            sinav_repo = SinavRepository(session)
            soru_repo = SoruRepository(session)

            # Kullanıcı listesi
            ogrenciler = await kullanici_repo.get_kullanicilar_by_rol(
                KullaniciRolu.OGRENCI
            )
            logger.info(f"👥 Toplam öğrenci sayısı: {len(ogrenciler)}")

            if ogrenciler:
                test_ogrenci = ogrenciler[0]
                logger.info(
                    f"[GRADUATION_CAP] Test öğrenci: {test_ogrenci.ad_soyad} ({test_ogrenci.email})"
                )

                # Öğrenci profili
                profil = await ogrenci_repo.get_by_kullanici_id(
                    test_ogrenci.kullanici_id
                )
                if profil:
                    logger.info(
                        f"[MEMO] Öğrenci profili: {profil.sinif}. sınıf, Hedef: {profil.hedef_universite}"
                    )

            # Sınav şablonları
            tyt_sablonlari = await sinav_repo.get_sablon_by_tip(SinavTipi.TYT)
            logger.info(f"[CLIPBOARD] TYT şablon sayısı: {len(tyt_sablonlari)}")

            # Soru bankası
            matematik_sorulari = await soru_repo.get_sorular_by_konu(
                "matematik", limit=10
            )
            logger.info(f"❓ Matematik soru sayısı: {len(matematik_sorulari)}")

            if matematik_sorulari:
                ornek_soru = matematik_sorulari[0]
                logger.info(f"[BOOKS] Örnek soru: {ornek_soru.soru_metni[:50]}...")
                logger.info(f"[TARGET] Zorluk: {ornek_soru.zorluk_seviyesi.value}")
                logger.info(
                    f"🧮 IRT parametreleri: a={ornek_soru.irt_a_parametresi}, b={ornek_soru.irt_b_parametresi}"
                )

        logger.info("[CHECK] Database integration testleri başarıyla tamamlandı!")
        return True

    except Exception as e:
        logger.error(f"[X] Database integration test hatası: {str(e)}")
        return False


async def main():
    """Ana test fonksiyonu"""
    success = await test_database_operations()

    if success:
        logger.info("[PARTY] Tüm testler başarılı!")
        sys.exit(0)
    else:
        logger.error("💥 Testler başarısız!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
