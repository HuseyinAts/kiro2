#!/usr/bin/env python3
"""
Basit Admin Kullanıcı Oluşturma Script'i
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text
from core.database import db_manager, get_db_session_context
from passlib.context import CryptContext

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin():
    """Admin kullanıcı oluştur"""
    print("Creating admin user...")

    try:
        await db_manager.initialize()

        async with get_db_session_context() as session:
            # Check if admin already exists
            result = await session.execute(
                text("SELECT id, email, role FROM users WHERE email = :email"),
                {"email": "admin@turkiyesinav.com"}
            )
            existing = result.fetchone()

            if existing:
                print(f"[!] Admin already exists: {existing.email}")
                print(f"    Role: {existing.role}")
                return

            # Create admin user
            password_hash = pwd_context.hash("admin123")

            await session.execute(
                text("""
                    INSERT INTO users (
                        id, email, username, password_hash,
                        first_name, last_name, role,
                        is_active, is_verified, created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :password_hash,
                        :first_name, :last_name, :role,
                        :is_active, :is_verified, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {
                    "id": "admin-001",
                    "email": "admin@turkiyesinav.com",
                    "username": "admin",
                    "password_hash": password_hash,
                    "first_name": "Platform",
                    "last_name": "Yöneticisi",
                    "role": "admin",
                    "is_active": True,
                    "is_verified": True,
                }
            )

            await session.commit()

            print("\n" + "="*60)
            print("[OK] Admin user created successfully!")
            print("="*60)
            print("\nLogin credentials:")
            print("  Email: admin@turkiyesinav.com")
            print("  Password: admin123")
            print("\nLogin at: http://localhost:3001")
            print("="*60 + "\n")

    except Exception as e:
        print(f"[ERROR] Failed to create admin: {str(e)}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(create_admin())
