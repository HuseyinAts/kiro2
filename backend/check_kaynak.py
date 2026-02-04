import asyncio
from core.database import get_db_session
from sqlalchemy import text


async def main():
    async for db in get_db_session():
        result = await db.execute(
            text(
                """
            SELECT DISTINCT kaynak, COUNT(*)
            FROM sorular
            WHERE dogru_cevap IS NOT NULL
            GROUP BY kaynak
        """
            )
        )

        print("Cevaplı soruların kaynak dağılımı:")
        for row in result.fetchall():
            print(f"  {row[0]}: {row[1]} soru")

        # Toplam
        total = await db.execute(
            text("SELECT COUNT(*) FROM sorular WHERE dogru_cevap IS NOT NULL")
        )
        print(f"\nToplam cevaplı soru: {total.scalar()}")
        break


asyncio.run(main())
