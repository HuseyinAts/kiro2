#!/usr/bin/env python3
"""
Create test user for authentication testing
"""
import asyncio
import sys
import os
import io
from passlib.context import CryptContext

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from core.database import db_manager, get_db_session_context

# Import all models to ensure proper SQLAlchemy relationship configuration
import models.database
from models.database import User, UserRole, StudentProfile

# Use bcrypt for password hashing (same as backend user_service.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt (matches backend authentication)"""
    return pwd_context.hash(password)


async def create_test_user():
    """Create test user for authentication testing"""
    print("🔧 Creating test user...")

    try:
        await db_manager.initialize()

        # Test user data
        test_user_data = {
            "email": "test@kiro2.com",
            "username": "test_user",
            "password_hash": hash_password("Test123!"),
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.STUDENT,
            "is_active": True,
            "is_verified": True,
        }

        async with get_db_session_context() as session:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == test_user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⚠️  User {test_user_data['email']} already exists!")
                print(f"   User ID: {existing.id}")
                print(f"   Username: {existing.username}")
                print(f"   Role: {existing.role.value}")
                return existing.id

            # Create user
            user = User(**test_user_data)
            session.add(user)
            await session.flush()  # Get the ID

            print(f"✅ User created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role.value}")
            print(f"   User ID: {user.id}")

            # Create student profile
            student_profile_data = {
                "user_id": user.id,
                "grade_level": 12,
                "school_name": "Test Lisesi",
                "target_university": "Test Üniversitesi",
                "target_department": "Test Bölümü",
                "current_level": 5.0,
                "study_hours_per_day": 4,
                "preferred_study_time": "evening",
            }

            profile = StudentProfile(**student_profile_data)
            session.add(profile)

            await session.commit()

            print(f"✅ Student profile created successfully!")
            print(f"\n{'='*50}")
            print("🎉 Test user is ready!")
            print(f"{'='*50}")
            print(f"\n📝 Login credentials:")
            print(f"   Email: test@kiro2.com")
            print(f"   Password: Test123!")
            print(f"\n🌐 Test at: http://localhost:3001")
            print(f"{'='*50}\n")

            return user.id

    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(create_test_user())
