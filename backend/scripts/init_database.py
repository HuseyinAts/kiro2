#!/usr/bin/env python3
"""
Database Initialization Script
Türkiye Üniversite Sınavları Hazırlık Platformu için database başlatma
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from core.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_database():
    """Database'i başlat ve tabloları oluştur"""
    logger.info("[ROCKET] Database initialization başlatılıyor...")

    try:
        # Database manager'ı başlat
        await db_manager.initialize()
        logger.info("[CHECK] Database bağlantısı kuruldu")

        # Tabloları oluştur
        await db_manager.create_tables()
        logger.info("[CHECK] Database tabloları oluşturuldu")

        # Health check
        health = await db_manager.health_check()
        if health["healthy"]:
            logger.info("[CHECK] Database sağlık kontrolü başarılı")
            logger.info(f"[CHART] Database URL: {settings.database_url}")
            logger.info(f"[CHART] Pool Size: {health.get('pool_size', 'N/A')}")
            logger.info(f"[CHART] Checked Out: {health.get('checked_out', 'N/A')}")
        else:
            logger.error("[X] Database sağlık kontrolü başarısız")
            return False

        logger.info("[PARTY] Database initialization tamamlandı!")
        return True

    except Exception as e:
        logger.error(f"[X] Database initialization hatası: {e!s}")
        return False
    finally:
        await db_manager.close()


async def reset_database():
    """Database'i sıfırla (DİKKATLİ KULLAN!)"""
    logger.warning("⚠️ Database reset işlemi başlatılıyor...")
    logger.warning("⚠️ Bu işlem TÜM VERİLERİ SİLECEK!")

    # Güvenlik kontrolü
    if settings.environment == "production":
        logger.error("[X] Production ortamında database reset yapılamaz!")
        return False

    try:
        await db_manager.initialize()

        # Tabloları sil
        await db_manager.drop_tables()
        logger.info("[CHECK] Tüm tablolar silindi")

        # Tabloları yeniden oluştur
        await db_manager.create_tables()
        logger.info("[CHECK] Tablolar yeniden oluşturuldu")

        logger.info("[PARTY] Database reset tamamlandı!")
        return True

    except Exception as e:
        logger.error(f"[X] Database reset hatası: {e!s}")
        return False
    finally:
        await db_manager.close()


async def check_database_status():
    """Database durumunu kontrol et"""
    logger.info("[MAG] Database durumu kontrol ediliyor...")

    try:
        await db_manager.initialize()

        health = await db_manager.health_check()

        logger.info("[CHART] DATABASE DURUM RAPORU")
        logger.info("=" * 40)
        logger.info(
            f"Durum: {'[CHECK] Sağlıklı' if health['healthy'] else '[X] Sorunlu'}"
        )
        logger.info(f"Database URL: {settings.database_url}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug Mode: {settings.debug}")

        if health["healthy"]:
            logger.info(f"Pool Size: {health.get('pool_size', 'N/A')}")
            logger.info(f"Checked Out: {health.get('checked_out', 'N/A')}")
            logger.info(f"Overflow: {health.get('overflow', 'N/A')}")
            logger.info(f"Checked In: {health.get('checked_in', 'N/A')}")
        else:
            logger.error(f"Hata: {health.get('error', 'Bilinmeyen hata')}")

        logger.info("=" * 40)
        return health["healthy"]

    except Exception as e:
        logger.error(f"[X] Database durum kontrolü hatası: {e!s}")
        return False
    finally:
        await db_manager.close()


def main():
    """Ana fonksiyon"""
    import argparse

    parser = argparse.ArgumentParser(description="Database Management Script")
    parser.add_argument(
        "action", choices=["init", "reset", "status"], help="Yapılacak işlem"
    )
    parser.add_argument(
        "--force", action="store_true", help="Reset işlemi için onay gerektirmez"
    )

    args = parser.parse_args()

    if args.action == "init":
        success = asyncio.run(init_database())
        sys.exit(0 if success else 1)

    elif args.action == "reset":
        if not args.force:
            response = input(
                "⚠️ TÜM VERİLER SİLİNECEK! Devam etmek istiyor musunuz? (yes/no): "
            )
            if response.lower() != "yes":
                logger.info("[X] İşlem iptal edildi")
                sys.exit(0)

        success = asyncio.run(reset_database())
        sys.exit(0 if success else 1)

    elif args.action == "status":
        success = asyncio.run(check_database_status())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
