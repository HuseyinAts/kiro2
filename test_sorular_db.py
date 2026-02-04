#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from core.database import db_manager
from sqlalchemy import text

async def test():
    await db_manager.initialize()
    async with db_manager.get_session() as s:
        # PROD sorularını getir
        r = await s.execute(text("""
            SELECT kod, konu, alt_konu, zorluk, LEFT(metin, 50) as soru_baslik
            FROM sorular
            WHERE kod LIKE 'PROD_%'
            ORDER BY olusturma_tarihi DESC
            LIMIT 5
        """))

        print("DATABASE'DEN SON 5 PROD SORULARI:")
        print("-" * 80)
        for row in r:
            print(f"{row[0]:20s} | {row[3]:5s} | {row[1][:30]:30s} | {row[4]}...")

        # Toplam sayı
        r2 = await s.execute(text("SELECT COUNT(*) FROM sorular WHERE kod LIKE 'PROD_%'"))
        total = r2.scalar()
        print()
        print(f"Toplam PROD soruları: {total}")

    await db_manager.close()

asyncio.run(test())
