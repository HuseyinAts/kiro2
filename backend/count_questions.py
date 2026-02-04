"""Count questions in database"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_db_session
from sqlalchemy import text


async def count():
    async for db in get_db_session():
        result = await db.execute(
            text(
                """
            SELECT COUNT(*)
            FROM sorular
            WHERE dogru_cevap IS NOT NULL
            AND metin IS NOT NULL
            AND LENGTH(metin) BETWEEN 50 AND 600
        """
            )
        )
        total = result.scalar()
        print(f"Toplam soru (cevap anahtarlı): {total}")

        # Tüm sorular
        result2 = await db.execute(text("SELECT COUNT(*) FROM sorular"))
        all_total = result2.scalar()
        print(f"Toplam soru (tümü): {all_total}")
        break


asyncio.run(count())
