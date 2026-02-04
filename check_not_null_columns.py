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
            SELECT column_name, is_nullable, column_default, data_type
            FROM information_schema.columns
            WHERE table_name = 'sorular' AND is_nullable = 'NO'
            ORDER BY ordinal_position
        """))

        print("NOT NULL KOLONLAR:")
        print("-" * 80)
        for row in r:
            print(f"{row[0]:30s} | Type: {row[3]:20s} | Default: {row[2]}")

    await db_manager.close()

asyncio.run(check())
