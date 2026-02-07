"""
Quick script to verify admin user exists in database
"""
import asyncio
from sqlalchemy import select
from core.database import db_manager
from models.user_models import User


async def verify_admin():
    """Verify admin user exists"""
    print("Checking for admin user...")

    await db_manager.initialize()

    async with db_manager.get_session() as session:
        result = await session.execute(
            select(User).where(User.email == 'admin@kiro2.com')
        )
        user = result.scalar_one_or_none()

        if user:
            print("\n[OK] Admin user found!")
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Role: {user.role.value}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Is Verified: {user.is_verified}")
            print(f"  ID: {user.id}")
        else:
            print("\n[ERROR] Admin user not found!")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(verify_admin())
