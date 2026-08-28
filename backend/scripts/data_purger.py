import asyncio
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# Backend modüllerini import edebilmek için path ekle
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import delete, select, text

from core.database import db_manager, get_db_session_context
from models.database import User

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def purge_future_profiles():
    """L9 (Future Dates) çöp datalarını temizle"""
    async with get_db_session_context() as session:
        now = datetime.now(UTC)

        # 1. Gelecek tarihli kayıt tarihine sahip Users tespit ve sil
        future_users = await session.execute(
            select(User.id).where(User.created_at > now)
        )
        future_user_ids = [u[0] for u in future_users.all()]

        if future_user_ids:
            logger.info(
                f"Gelecek tarihli {len(future_user_ids)} User bulundu. Siliniyor..."
            )
            await session.execute(delete(User).where(User.id.in_(future_user_ids)))

        # 2. L6 (Dummy Data) - test_, dummy_ vb ile başlayan e-postalar
        dummy_users = await session.execute(
            select(User.id)
            .where(User.email.ilike("test_%"))
            .where(User.email.ilike("dummy_%"))
        )
        dummy_user_ids = [u[0] for u in dummy_users.all()]

        # Daha geniş dummy taraması
        dummy_users2 = await session.execute(
            select(User.id).where(
                User.email.like("test@%")
                | User.email.like("dummy@%")
                | User.username.like("testuser%")
            )
        )
        dummy_user_ids.extend([u[0] for u in dummy_users2.all()])

        dummy_user_ids = list(set(dummy_user_ids))
        if dummy_user_ids:
            logger.info(f"Test/Çöp {len(dummy_user_ids)} User bulundu. Siliniyor...")
            # Cleanup foreign keys before deleting user
            await session.execute(
                text("DELETE FROM api_keys WHERE user_id = ANY(:user_ids)"),
                {"user_ids": dummy_user_ids},
            )
            await session.execute(
                text("DELETE FROM refresh_tokens WHERE user_id = ANY(:user_ids)"),
                {"user_ids": dummy_user_ids},
            )
            await session.execute(
                text(
                    "DELETE FROM fsrs_study_sessions WHERE student_id = ANY(:user_ids)"
                ),
                {"user_ids": dummy_user_ids},
            )
            await session.execute(
                text("DELETE FROM student_profiles WHERE user_id = ANY(:user_ids)"),
                {"user_ids": dummy_user_ids},
            )
            await session.execute(delete(User).where(User.id.in_(dummy_user_ids)))

        await session.commit()
        logger.info("Kullanıcı temizliği tamamlandı.")


async def patch_html_leaks():
    """L2 (HTML Leak) soru metinlerindeki HTML sızıntılarını temizle"""
    async with get_db_session_context() as session:
        # Basit HTML tag'leri olan soruları bul
        # Not: Gerçek uygulamada daha karmaşık regex veya BeautifulSoup kullanılabilir,
        # burada SQL tarafında like ile basit tagleri tespit edip Python'da temizleyeceğiz.

        # Soru bankasını çek
        from models.question_bank import QuestionBankItem

        result = await session.execute(
            select(QuestionBankItem).where(
                QuestionBankItem.soru_metni.like("%<p>%")
                | QuestionBankItem.soru_metni.like("%<br>%")
                | QuestionBankItem.soru_metni.like("%<b>%")
                | QuestionBankItem.soru_metni.like("%<span>%")
            )
        )
        questions = result.scalars().all()

        cleaned_count = 0
        html_cleaner = re.compile("<.*?>")

        for q in questions:
            if q.soru_metni:
                clean_text = re.sub(html_cleaner, "", q.soru_metni)
                if clean_text != q.soru_metni:
                    q.soru_metni = clean_text
                    cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"{cleaned_count} sorudaki HTML sızıntıları temizlendi.")
            await session.commit()
        else:
            logger.info("HTML sızıntısı bulunan soru tespit edilmedi.")


async def main():
    await db_manager.initialize()
    try:
        logger.info("Veritabanı temizleme (Purge & Patch) işlemi başlıyor...")
        await purge_future_profiles()
        await patch_html_leaks()
        logger.info("Veritabanı temizleme işlemi başarıyla tamamlandı.")
    except Exception as e:
        logger.error(f"Hata oluştu: {e}")
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
