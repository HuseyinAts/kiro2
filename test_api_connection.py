"""Test API database connection"""
import asyncpg
import asyncio

async def test_connection():
    try:
        # Connect to database
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5434/kiro2')
        
        # Test queries
        total = await conn.fetchval('SELECT COUNT(*) FROM questions')
        tyt = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE exam_type = 'tyt'")
        ayt = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE exam_type = 'ayt'")
        
        print(f"API Baglanti Testi Basarili!")
        print(f"  Toplam Soru: {total:,}")
        print(f"  TYT Sorulari: {tyt:,}")
        print(f"  AYT Sorulari: {ayt:,}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Baglanti hatasi: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())