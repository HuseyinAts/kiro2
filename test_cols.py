import asyncio
import asyncpg
import sys

async def test():
    try:
        conn = await asyncpg.connect(host='localhost', port=5434, user='postgres', password='1470', database='kiro2')
        cols = await conn.fetch("""SELECT column_name FROM information_schema.columns WHERE table_name = 'questions'""")
        result = [c['column_name'] for c in cols]
        
        # Write to file
        with open("cols.txt", "w") as f:
            f.write(str(result))
        
        await conn.close()
    except Exception as e:
        with open("cols.txt", "w") as f:
            f.write(f"ERROR: {e}")

asyncio.run(test())
