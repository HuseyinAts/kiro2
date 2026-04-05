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
        # Get column names
        r = await s.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'sorular'
            ORDER BY ordinal_position
        """))

        print("SORULAR TABLOSU KOLONLARI:")
        print("-" * 100)
        print(f"{'Column Name':<30} | {'Data Type':<20} | {'Nullable':<10} | {'Default':<20}")
        print("-" * 100)
        for row in r:
            print(f"{row[0]:<30} | {row[1]:<20} | {row[2]:<10} | {str(row[3])[:20]:<20}")

    await db_manager.close()

asyncio.run(check())
