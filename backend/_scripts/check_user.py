#!/usr/bin/env python3
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_user():
    from core.database import db_manager
    from models.database import User
    from sqlalchemy import select

    await db_manager.initialize()

    async with db_manager.get_session() as db:
        result = await db.execute(select(User).where(User.email == 'test@kiro2.com'))
        user = result.scalar_one_or_none()

        print(f'User exists: {user is not None}')
        if user:
            print(f'User ID: {user.id}')
            print(f'Email: {user.email}')
            print(f'Role: {user.role}')
            print(f'Active: {user.is_active}')
        else:
            print('Test user NOT FOUND in database!')

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_user())
