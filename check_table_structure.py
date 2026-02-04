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
        # Get table structure
        r = await s.execute(text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'sorular'
            ORDER BY ordinal_position
        """))
        print("SORULAR TABLE STRUCTURE:")
        print("-" * 60)
        for row in r:
            print(f"{row[0]:30s} | {row[1]:15s} | {row[2]}")
    await db_manager.close()

asyncio.run(check())
