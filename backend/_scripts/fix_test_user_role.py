#!/usr/bin/env python3
"""Fix test user role from 'student' to 'ogrenci'"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_user_role():
    from core.database import db_manager
    from models.database import User
    from sqlalchemy import select, update

    await db_manager.initialize()

    async with db_manager.get_session() as db:
        # Find the test user
        result = await db.execute(select(User).where(User.email == 'test@kiro2.com'))
        user = result.scalar_one_or_none()

        if user:
            print(f'Found user: {user.email}')
            print(f'Current role: {user.role}')

            # Update role to 'ogrenci'
            user.role = 'ogrenci'
            await db.commit()

            print(f'Updated role to: ogrenci')
            print('SUCCESS: User role fixed!')
        else:
            print('ERROR: User not found!')

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(fix_user_role())
