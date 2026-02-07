#!/usr/bin/env python3
"""Check what values are in the PostgreSQL userrole enum"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_enum():
    from core.database import db_manager
    from sqlalchemy import text

    await db_manager.initialize()

    async with db_manager.get_session() as db:
        # Query PostgreSQL to see enum values
        query = text("""
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'userrole'
            ORDER BY e.enumsortorder;
        """)

        result = await db.execute(query)
        values = result.fetchall()

        print("Current PostgreSQL userrole enum values:")
        for row in values:
            print(f"  - {row[0]}")

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_enum())
