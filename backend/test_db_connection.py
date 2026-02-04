"""Test database connection"""
import asyncio
from core.database import db_manager


async def test():
    try:
        print("Testing database connection...")
        health = await db_manager.health_check()
        print(f"Database health: {health}")

        if health.get("healthy"):
            print("✓ Database connection successful!")
        else:
            print("✗ Database connection failed!")
            print(f"Error: {health.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
