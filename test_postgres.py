import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/turkiye_sinav_db')
        await conn.execute('SELECT 1')
        await conn.close()
        print('[OK] PostgreSQL connection successful!')
        return True
    except Exception as e:
        print(f'[ERROR] Connection failed: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(test())
    exit(0 if success else 1)
