#!/usr/bin/env python3
"""
Test password verification with same pwd_context as auth.py
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from core.database import db_manager
from models.database import User

# Import the SAME pwd_context from auth.py
from api.auth import pwd_context


async def test_verify():
    """Test password verification"""
    await db_manager.initialize()

    async with db_manager.get_session() as db:
        result = await db.execute(select(User).where(User.email == 'test@kiro2.com'))
        user = result.scalar_one_or_none()

        if not user:
            print("User not found!")
            return

        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print(f"Hash exists: {bool(user.password_hash)}")
        print(f"Hash length: {len(user.password_hash)}")
        print(f"Hash format: {user.password_hash[:10]}...")

        # Test with Test123!
        test_password = "Test123!"
        result = pwd_context.verify(test_password, user.password_hash)
        print(f"\nPassword '{test_password}' verification: {result}")

        # Also try to see what password would match
        if not result:
            print("\nTrying to debug...")
            print(f"Password being tested: {repr(test_password)}")
            print(f"Password length: {len(test_password)}")
            print(f"Password bytes: {test_password.encode('utf-8')}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_verify())
