#!/usr/bin/env python3
"""
Database Management CLI
Türkiye Üniversite Sınavları Hazırlık Platformu için database yönetim aracı
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database yönetim sınıfı"""

    def __init__(self):
        self.backend_path = Path(__file__).parent.parent

    async def create_migration(self, message: str):
        """Yeni migration oluştur"""
        logger.info(f"[MEMO] Yeni migration oluşturuluyor: {message}")

        try:
            # Alembic revision komutunu çalıştır
            cmd = [
                sys.executable,
                "-m",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                message,
            ]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHECK] Migration başarıyla oluşturuldu")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Migration oluşturma hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Migration oluşturma hatası: {str(e)}")
            return False

    async def run_migrations(self):
        """Migration'ları çalıştır"""
        logger.info("[ROCKET] Migration'lar çalıştırılıyor...")

        try:
            cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHECK] Migration'lar başarıyla çalıştırıldı")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Migration çalıştırma hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Migration çalıştırma hatası: {str(e)}")
            return False

    async def rollback_migration(self, revision: str = None):
        """Migration'ı geri al"""
        target = revision or "-1"
        logger.info(f"⏪ Migration geri alınıyor: {target}")

        try:
            cmd = [sys.executable, "-m", "alembic", "downgrade", target]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHECK] Migration başarıyla geri alındı")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Migration geri alma hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Migration geri alma hatası: {str(e)}")
            return False

    async def show_current_revision(self):
        """Mevcut revision'ı göster"""
        logger.info("[MAG] Mevcut database revision'ı kontrol ediliyor...")

        try:
            cmd = [sys.executable, "-m", "alembic", "current"]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHART] Mevcut Revision:")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Revision kontrol hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Revision kontrol hatası: {str(e)}")
            return False

    async def show_migration_history(self):
        """Migration geçmişini göster"""
        logger.info("📜 Migration geçmişi gösteriliyor...")

        try:
            cmd = [sys.executable, "-m", "alembic", "history", "--verbose"]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHART] Migration Geçmişi:")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Migration geçmişi hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Migration geçmişi hatası: {str(e)}")
            return False

    async def seed_development_data(self):
        """Development verilerini seed et"""
        logger.info("🌱 Development verileri seed ediliyor...")

        try:
            # seed_database.py script'ini çalıştır
            seed_script = self.backend_path / "scripts" / "seed_database.py"

            if not seed_script.exists():
                logger.error("[X] Seed script bulunamadı")
                return False

            cmd = [sys.executable, str(seed_script)]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHECK] Development verileri başarıyla seed edildi")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Development seed hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Development seed hatası: {str(e)}")
            return False

    async def seed_production_data(self):
        """Production verilerini seed et"""
        logger.info("🏭 Production verileri seed ediliyor...")

        if settings.environment != "production":
            logger.error("[X] Bu komut sadece production ortamında çalışır")
            return False

        try:
            # production_seed.py script'ini çalıştır
            seed_script = self.backend_path / "scripts" / "production_seed.py"

            if not seed_script.exists():
                logger.error("[X] Production seed script bulunamadı")
                return False

            cmd = [sys.executable, str(seed_script)]

            result = subprocess.run(
                cmd, cwd=self.backend_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("[CHECK] Production verileri başarıyla seed edildi")
                logger.info(result.stdout)
                return True
            else:
                logger.error("[X] Production seed hatası")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"[X] Production seed hatası: {str(e)}")
            return False

    async def backup_database(self, backup_path: str = None):
        """Database backup al"""
        if not backup_path:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.sql"

        logger.info(f"[FLOPPY] Database backup alınıyor: {backup_path}")

        # SQLite için basit backup
        if "sqlite" in settings.database_url:
            try:
                import shutil

                db_file = settings.database_url.replace("sqlite+aiosqlite:///", "")
                shutil.copy2(db_file, backup_path)
                logger.info(f"[CHECK] SQLite backup başarılı: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"[X] SQLite backup hatası: {str(e)}")
                return False

        # PostgreSQL için pg_dump
        elif "postgresql" in settings.database_url:
            logger.info("PostgreSQL backup için pg_dump kullanın")
            return False

        else:
            logger.error("[X] Desteklenmeyen database türü")
            return False


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Database Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # Migration komutları
    migration_parser = subparsers.add_parser("migration", help="Migration işlemleri")
    migration_subparsers = migration_parser.add_subparsers(dest="migration_action")

    # Create migration
    create_parser = migration_subparsers.add_parser(
        "create", help="Yeni migration oluştur"
    )
    create_parser.add_argument("message", help="Migration mesajı")

    # Run migrations
    migration_subparsers.add_parser("run", help="Migration'ları çalıştır")

    # Rollback migration
    rollback_parser = migration_subparsers.add_parser(
        "rollback", help="Migration'ı geri al"
    )
    rollback_parser.add_argument("--revision", help="Geri alınacak revision")

    # Show current
    migration_subparsers.add_parser("current", help="Mevcut revision'ı göster")

    # Show history
    migration_subparsers.add_parser("history", help="Migration geçmişini göster")

    # Seed komutları
    seed_parser = subparsers.add_parser("seed", help="Veri seed işlemleri")
    seed_subparsers = seed_parser.add_subparsers(dest="seed_action")

    seed_subparsers.add_parser("dev", help="Development verilerini seed et")
    seed_subparsers.add_parser("prod", help="Production verilerini seed et")

    # Backup komutları
    backup_parser = subparsers.add_parser("backup", help="Database backup")
    backup_parser.add_argument("--path", help="Backup dosya yolu")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    db_mgr = DatabaseManager()

    # Migration komutları
    if args.command == "migration":
        if args.migration_action == "create":
            success = asyncio.run(db_mgr.create_migration(args.message))
        elif args.migration_action == "run":
            success = asyncio.run(db_mgr.run_migrations())
        elif args.migration_action == "rollback":
            success = asyncio.run(db_mgr.rollback_migration(args.revision))
        elif args.migration_action == "current":
            success = asyncio.run(db_mgr.show_current_revision())
        elif args.migration_action == "history":
            success = asyncio.run(db_mgr.show_migration_history())
        else:
            migration_parser.print_help()
            return

    # Seed komutları
    elif args.command == "seed":
        if args.seed_action == "dev":
            success = asyncio.run(db_mgr.seed_development_data())
        elif args.seed_action == "prod":
            success = asyncio.run(db_mgr.seed_production_data())
        else:
            seed_parser.print_help()
            return

    # Backup komutları
    elif args.command == "backup":
        success = asyncio.run(db_mgr.backup_database(args.path))

    else:
        parser.print_help()
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
