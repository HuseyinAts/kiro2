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
            SELECT
                con.conname AS constraint_name,
                pg_get_constraintdef(con.oid) AS constraint_definition
            FROM pg_constraint con
            INNER JOIN pg_class rel ON rel.oid = con.conrelid
            WHERE rel.relname = 'sorular'
            AND con.contype = 'c'
        """))

        print("CHECK CONSTRAINTS:")
        print("-" * 80)
        for row in r:
            print(f"Name: {row[0]}")
            print(f"Def:  {row[1]}")
            print()

    await db_manager.close()

asyncio.run(check())
