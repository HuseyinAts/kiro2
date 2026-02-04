"""Test asyncpg connection with password"""
import asyncio
import asyncpg


async def test():
    try:
        print("Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            "postgresql://postgres:changeme_strong_password_here@localhost:5432/turkiye_sinav_db"
        )
        result = await conn.fetchval("SELECT 1")
        print(f"SUCCESS! Result: {result}")
        await conn.close()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
