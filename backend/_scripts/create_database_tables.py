#!/usr/bin/env python3
"""
Create all database tables using SQLAlchemy
"""
import asyncio
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_tables():
    """Create all database tables"""
    print("🔧 Creating database tables...")

    from core.database import db_manager
    from models.base import Base

    # Import all models to register them with Base
    import models.database
    from models.user_badge import UserBadge
    from models.user_achievement import UserAchievement
    from models.point_transaction import PointTransaction
    from models.student_goal import StudentGoal
    from models.notification import Notification
    from models.student_learning_profile import StudentLearningProfile

    try:
        await db_manager.initialize()

        # Drop all existing tables first (development only!)
        print("⚠️  Dropping all existing tables...")
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("✅ Existing tables dropped")

        # Create all tables
        print("🔨 Creating fresh tables...")
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ All database tables created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
