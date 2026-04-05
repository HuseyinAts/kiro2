import asyncio
import asyncpg

async def check_tables():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/turkiye_sinav_db')
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Existing tables:")
        for t in tables:
            print(f"  - {t['table_name']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check_tables())
