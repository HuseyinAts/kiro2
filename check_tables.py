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
        # Check if tables exist
        tables = ["questions", "sorular", "question_bank"]

        for table in tables:
            r = await s.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """))
            exists = r.scalar()

            if exists:
                r2 = await s.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = r2.scalar()
                print(f"[OK] Table '{table}' EXISTS - {count} rows")
            else:
                print(f"[NO] Table '{table}' DOES NOT EXIST")

    await db_manager.close()

asyncio.run(check())
