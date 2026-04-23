#!/usr/bin/env python3
"""
Production Data Seeding Script
Production ortamı için güvenli veri seeding
"""

import asyncio
import hashlib
import logging
import os
import secrets
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from core.config import settings
from core.database import db_manager, get_db_session_context
from models.database import (
    ExamType,
    Question,
    QuestionDifficulty,
    SubjectArea,
    SystemConfiguration,
    User,
    UserRole,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionSeeder:
    """Production ortamı için güvenli seeding"""

    def __init__(self):
        self.seeded_counts = {"system_configs": 0, "admin_users": 0, "questions": 0}

    async def seed_production_data(self):
        """Production için gerekli minimum veriyi seed et"""
        logger.info("🏭 Production data seeding başlatılıyor...")

        # Production kontrolü
        if settings.environment != "production":
            logger.warning("⚠️ Bu script sadece production ortamında çalışır")
            return False

        try:
            await db_manager.initialize()

            # Kritik sistem konfigürasyonları
            await self.seed_critical_system_configs()

            # Admin kullanıcısı (eğer yoksa)
            await self.seed_admin_user()

            # Minimum soru bankası (eğer yoksa)
            await self.seed_minimum_questions()

            # Özet rapor
            await self.print_production_summary()

            logger.info("[CHECK] Production data seeding tamamlandı!")
            return True

        except Exception as e:
            logger.error(f"[X] Production seeding hatası: {e!s}")
            return False
        finally:
            await db_manager.close()

    async def seed_critical_system_configs(self):
        """Kritik sistem konfigürasyonları"""
        logger.info("[GEAR] Kritik sistem konfigürasyonları ekleniyor...")

        configs = [
            {
                "config_key": "platform_name",
                "config_value": "Türkiye Üniversite Sınavları Hazırlık Platformu",
                "config_type": "string",
                "description": "Platform adı",
            },
            {
                "config_key": "platform_version",
                "config_value": "1.0.0",
                "config_type": "string",
                "description": "Platform versiyonu",
            },
            {
                "config_key": "maintenance_mode",
                "config_value": "false",
                "config_type": "boolean",
                "description": "Bakım modu",
            },
            {
                "config_key": "max_concurrent_users",
                "config_value": "10000",
                "config_type": "integer",
                "description": "Maksimum eşzamanlı kullanıcı sayısı",
            },
            {
                "config_key": "session_timeout_minutes",
                "config_value": "60",
                "config_type": "integer",
                "description": "Oturum zaman aşımı (dakika)",
            },
            {
                "config_key": "enable_revolutionary_features",
                "config_value": "true",
                "config_type": "boolean",
                "description": "Devrimsel özellikleri etkinleştir",
            },
            {
                "config_key": "backup_retention_days",
                "config_value": "30",
                "config_type": "integer",
                "description": "Yedek saklama süresi (gün)",
            },
            {
                "config_key": "log_level",
                "config_value": "INFO",
                "config_type": "string",
                "description": "Log seviyesi",
            },
        ]

        async with get_db_session_context() as session:
            for config_data in configs:
                # Mevcut konfigürasyon kontrolü
                result = await session.execute(
                    select(SystemConfiguration).where(
                        SystemConfiguration.config_key == config_data["config_key"]
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    config = SystemConfiguration(**config_data)
                    session.add(config)
                    self.seeded_counts["system_configs"] += 1

            await session.commit()

        logger.info(
            f"[CHECK] {self.seeded_counts['system_configs']} sistem konfigürasyonu eklendi"
        )

    async def seed_admin_user(self):
        """Production admin kullanıcısı"""
        logger.info("👤 Production admin kullanıcısı kontrol ediliyor...")

        async with get_db_session_context() as session:
            # Mevcut admin kontrolü
            result = await session.execute(
                select(func.count(User.id)).where(User.role == UserRole.ADMIN)
            )
            admin_count = result.scalar()

            if admin_count == 0:
                # Güvenli şifre oluştur
                admin_password = secrets.token_urlsafe(16)

                admin_user = User(
                    email="admin@turkiyesinav.com",
                    username="admin",
                    password_hash=self._hash_password(admin_password),
                    first_name="Platform",
                    last_name="Yöneticisi",
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )

                session.add(admin_user)
                await session.commit()

                self.seeded_counts["admin_users"] += 1

                # Şifreyi güvenli bir şekilde logla (sadece bir kez)
                logger.info("[LOCKED_KEY] YENİ ADMIN KULLANICISI OLUŞTURULDU!")
                logger.info("[EMAIL] Email: admin@turkiyesinav.com")
                logger.info(f"🔑 Şifre: {admin_password}")
                logger.info(
                    "⚠️ Bu şifreyi güvenli bir yerde saklayın ve hemen değiştirin!"
                )

            else:
                logger.info(f"[CHECK] {admin_count} admin kullanıcısı zaten mevcut")

    async def seed_minimum_questions(self):
        """Minimum soru bankası"""
        logger.info("❓ Minimum soru bankası kontrol ediliyor...")

        async with get_db_session_context() as session:
            # Mevcut soru sayısını kontrol et
            result = await session.execute(select(func.count(Question.id)))
            question_count = result.scalar()

            if question_count < 10:  # Minimum 10 soru
                logger.info("[MEMO] Minimum soru bankası ekleniyor...")

                # Temel sorular
                basic_questions = [
                    {
                        "question_text": "Bir sayının %20'si 40 ise, bu sayının %30'u kaçtır?",
                        "option_a": "50",
                        "option_b": "60",
                        "option_c": "70",
                        "option_d": "80",
                        "correct_answer": "B",
                        "explanation": "Sayı x olsun. x'in %20'si = 40 ise x = 200. x'in %30'u = 200 × 0.3 = 60",
                        "exam_type": ExamType.TYT,
                        "subject_area": SubjectArea.MATEMATIK,
                        "topic": "Yüzdeler",
                        "difficulty": QuestionDifficulty.EASY,
                        "irt_difficulty": -0.5,
                        "irt_discrimination": 1.2,
                        "irt_guessing": 0.25,
                    },
                    {
                        "question_text": "Türkiye'nin başkenti neresidir?",
                        "option_a": "İstanbul",
                        "option_b": "İzmir",
                        "option_c": "Ankara",
                        "option_d": "Bursa",
                        "correct_answer": "C",
                        "explanation": "Türkiye Cumhuriyeti'nin başkenti Ankara'dır.",
                        "exam_type": ExamType.TYT,
                        "subject_area": SubjectArea.SOSYAL,
                        "topic": "Coğrafya",
                        "difficulty": QuestionDifficulty.EASY,
                        "irt_difficulty": -1.0,
                        "irt_discrimination": 2.0,
                        "irt_guessing": 0.25,
                    },
                    {
                        "question_text": "Aşağıdaki kelimelerden hangisi doğru yazılmıştır?",
                        "option_a": "gelmişim",
                        "option_b": "gelmiştim",
                        "option_c": "gelmişdim",
                        "option_d": "gelmiştım",
                        "correct_answer": "B",
                        "explanation": 'Geçmiş zaman eki "-miş" ten sonra gelen kişi eki "-tim" şeklinde yazılır.',
                        "exam_type": ExamType.TYT,
                        "subject_area": SubjectArea.TURKCE,
                        "topic": "Yazım Kuralları",
                        "difficulty": QuestionDifficulty.MEDIUM,
                        "irt_difficulty": 0.2,
                        "irt_discrimination": 1.4,
                        "irt_guessing": 0.25,
                    },
                ]

                for question_data in basic_questions:
                    question = Question(**question_data)
                    session.add(question)
                    self.seeded_counts["questions"] += 1

                await session.commit()
                logger.info(
                    f"[CHECK] {self.seeded_counts['questions']} temel soru eklendi"
                )
            else:
                logger.info(f"[CHECK] {question_count} soru zaten mevcut")

    async def print_production_summary(self):
        """Production seeding özeti"""
        logger.info("\n" + "=" * 50)
        logger.info("🏭 PRODUCTION SEEDING ÖZETİ")
        logger.info("=" * 50)

        async with get_db_session_context() as session:
            # Toplam sayıları al
            user_count = await session.scalar(select(func.count(User.id)))
            admin_count = await session.scalar(
                select(func.count(User.id)).where(User.role == UserRole.ADMIN)
            )
            question_count = await session.scalar(select(func.count(Question.id)))
            config_count = await session.scalar(
                select(func.count(SystemConfiguration.id))
            )

        logger.info(f"👤 Toplam Kullanıcı: {user_count}")
        logger.info(f"👑 Admin Kullanıcı: {admin_count}")
        logger.info(f"❓ Toplam Soru: {question_count}")
        logger.info(f"[GEAR] Sistem Konfigürasyonu: {config_count}")
        logger.info("🌱 Bu Seeding'de Eklenen:")
        logger.info(
            f"   - Sistem Konfigürasyonu: {self.seeded_counts['system_configs']}"
        )
        logger.info(f"   - Admin Kullanıcı: {self.seeded_counts['admin_users']}")
        logger.info(f"   - Soru: {self.seeded_counts['questions']}")
        logger.info("=" * 50)

    def _hash_password(self, password: str) -> str:
        """Şifre hash'le"""
        return hashlib.sha256(password.encode()).hexdigest()


async def main():
    """Ana fonksiyon"""
    seeder = ProductionSeeder()
    success = await seeder.seed_production_data()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
