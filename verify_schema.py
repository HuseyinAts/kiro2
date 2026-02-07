import asyncio
import asyncpg

async def verify_schema():
    output = []
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='1470',
        database='kiro2'
    )
    
    # Check if exam_type column exists
    columns = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'questions'
    """)
    
    column_names = [col['column_name'] for col in columns]
    
    output.append("=== COLUMN CHECK ===")
    output.append(f"exam_type exists: {'exam_type' in column_names}")
    output.append(f"subject exists: {'subject' in column_names}")
    output.append(f"topic exists: {'topic' in column_names}")
    output.append(f"\nAll columns: {column_names}")
    
    # Test the exact query that's failing
    output.append("\n=== TESTING QUERY ===")
    try:
        result = await conn.fetch(
            "SELECT exam_type, COUNT(*) as count FROM questions WHERE exam_type IS NOT NULL GROUP BY exam_type"
        )
        output.append(f"Query SUCCESS: {list(result)}")
    except Exception as e:
        output.append(f"Query FAILED: {e}")
    
    await conn.close()
    
    with open("verify_schema.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print("Check verify_schema.txt")

asyncio.run(verify_schema())
