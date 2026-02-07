import asyncio
import asyncpg

async def check_schema():
    output = []
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='1470',
        database='kiro2'
    )
    
    # Get questions table columns
    columns = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'questions' 
        ORDER BY ordinal_position
    """)
    
    output.append("=== QUESTIONS TABLE COLUMNS ===")
    for col in columns:
        output.append(f"  {col['column_name']}: {col['data_type']}")
    
    # Get sample data
    sample = await conn.fetch("SELECT * FROM questions LIMIT 1")
    output.append("\n=== SAMPLE DATA ===")
    if sample:
        for key, value in sample[0].items():
            output.append(f"  {key}: {value}")
    else:
        output.append("  No data in questions table")
    
    # Count
    count = await conn.fetchval("SELECT COUNT(*) FROM questions")
    output.append(f"\n=== TOTAL QUESTIONS: {count} ===")
    
    await conn.close()
    
    # Write to file
    with open("schema_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print("Output written to schema_output.txt")

asyncio.run(check_schema())
