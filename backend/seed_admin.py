"""
Admin User Seed Script for KIRO2 Platform

Creates an initial admin user in the database if no admin exists.
This script should be run once during initial setup.

Usage:
    python seed_admin.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (from .env)

Security:
    - Password is hashed with bcrypt
    - Only creates admin if no admin exists
    - Uses strong password policy
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import db_manager
from models.enums_db import UserRole
from models.user_models import User


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Encode password to bytes and hash with bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


async def check_admin_exists(session: AsyncSession) -> bool:
    """
    Check if any admin user exists in the database.

    Args:
        session: Database session

    Returns:
        True if admin exists, False otherwise
    """
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    admin = result.scalars().first()
    return admin is not None


async def create_admin_user(session: AsyncSession) -> User:
    """
    Create an admin user in the database.

    Args:
        session: Database session

    Returns:
        Created User object
    """
    # Admin credentials
    admin_email = "admin@kiro2.com"
    admin_username = "admin"
    admin_password = "Admin123!"  # Strong password that meets policy

    # Hash the password
    password_hash = hash_password(admin_password)

    # Create admin user
    admin_user = User(
        email=admin_email,
        username=admin_username,
        password_hash=password_hash,
        role=UserRole.ADMIN,
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        # Gamification defaults
        total_xp=0,
        level=1,
        # 2FA disabled by default
        is_2fa_enabled=False,
        # Premium disabled by default
        is_premium=False,
    )

    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)

    return admin_user


async def seed_admin():
    """
    Main function to seed admin user.

    Creates an admin user if no admin exists in the database.
    """
    print("=" * 70)
    print("KIRO2 Admin User Seed Script")
    print("=" * 70)
    print()

    # Check database URL
    print(f"Database URL: {settings.database_url}")
    print()

    try:
        # Initialize database connection
        print("Initializing database connection...")
        await db_manager.initialize()
        print("[OK] Database connection established")
        print()

        # Get database session
        async with db_manager.get_session() as session:
            # Check if admin exists
            print("Checking for existing admin users...")
            admin_exists = await check_admin_exists(session)

            if admin_exists:
                print("[WARNING] Admin user already exists. Skipping creation.")
                print()
                print("If you need to reset the admin password, please use a")
                print("password reset tool or delete the existing admin first.")
                return

            print("[OK] No admin user found. Creating admin user...")
            print()

            # Create admin user
            admin = await create_admin_user(session)

            print("=" * 70)
            print("[SUCCESS] Admin user created successfully!")
            print("=" * 70)
            print()
            print("Admin Credentials:")
            print("  Email:    admin@kiro2.com")
            print("  Username: admin")
            print("  Password: Admin123!")
            print()
            print("IMPORTANT: Change the password after first login!")
            print()
            print("User Details:")
            print(f"  ID:       {admin.id}")
            print(f"  Role:     {admin.role.value}")
            print(f"  Active:   {admin.is_active}")
            print(f"  Verified: {admin.is_verified}")
            print(f"  Created:  {admin.created_at}")
            print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] Failed to create admin user")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close database connection
        await db_manager.close()
        print()
        print("Database connection closed.")


if __name__ == "__main__":
    # Run async main function
    asyncio.run(seed_admin())
