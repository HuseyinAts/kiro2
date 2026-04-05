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
        # Check if table exists
        r = await s.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='sorular'"
        ))
        if r.scalar():
            print("[OK] sorular table EXISTS")
            # Count rows
            r2 = await s.execute(text("SELECT COUNT(*) FROM sorular"))
            count = r2.scalar()
            print(f"[OK] Current row count: {count}")
        else:
            print("[WARN] sorular table NOT FOUND - need to create it")
    await db_manager.close()

asyncio.run(check())
