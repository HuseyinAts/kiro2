"""Create kiro2_db database"""
import asyncio
import asyncpg
import sys

async def create_database():
    try:
        # Connect to postgres default database
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            user='postgres',
            password='postgres',
            database='postgres'
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'kiro2_db'"
        )

        if exists:
            print("[OK] Database 'kiro2_db' already exists")
        else:
            # Create database (cannot be done in transaction)
            await conn.execute('CREATE DATABASE kiro2_db')
            print("[OK] Database 'kiro2_db' created successfully")

        await conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create database: {e}")
        return False

if __name__ == '__main__':
    success = asyncio.run(create_database())
    sys.exit(0 if success else 1)
