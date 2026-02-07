#!/usr/bin/env python3
import asyncio
import sys
import os
from passlib.context import CryptContext

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_password():
    from core.database import db_manager
    from models.database import User
    from sqlalchemy import select

    await db_manager.initialize()

    async with db_manager.get_session() as db:
        result = await db.execute(select(User).where(User.email == 'test@kiro2.com'))
        user = result.scalar_one_or_none()

        if user:
            print(f'User found: {user.email}')
            print(f'Password hash: {user.password_hash[:50]}...')

            # Test password verification
            test_password = "Test123!"
            is_valid = pwd_context.verify(test_password, user.password_hash)
            print(f'Password "Test123!" matches: {is_valid}')

            if not is_valid:
                print('ERROR: Password does not match! Creating new hash...')
                new_hash = pwd_context.hash(test_password)
                print(f'New hash would be: {new_hash[:50]}...')
        else:
            print('User not found!')

    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_password())
