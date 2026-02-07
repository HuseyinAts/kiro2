#!/usr/bin/env python3
"""Fix test user role to uppercase 'STUDENT'"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_user_role():
    from core.database import db_manager
    from sqlalchemy import text

    await db_manager.initialize()

    async with db_manager.get_session() as db:
        # Update the test user's role to uppercase
        query = text("""
            UPDATE users
            SET role = 'STUDENT'::userrole
            WHERE email = 'test@kiro2.com'
        """)

        await db.execute(query)
        await db.commit()

        print("✅ User role updated to 'STUDENT' (uppercase)")

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(fix_user_role())
