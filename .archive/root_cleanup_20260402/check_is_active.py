#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from core.database import db_manager
from sqlalchemy import text

async def check():
    await db_manager.initialize()
    async with db_manager.get_session() as s:
        r = await s.execute(text("""
            SELECT kod, is_active, status, sinav_tipi
            FROM sorular
            WHERE kod LIKE 'PROD_%'
            LIMIT 5
        """))

        print("PROD SORULARININ is_active ve status DEĞERLERİ:")
        print("-" * 80)
        for row in r:
            print(f"{row[0]:20s} | is_active: {row[1]} | status: {row[2]} | sinav_tipi: {row[3]}")

    await db_manager.close()

asyncio.run(check())
