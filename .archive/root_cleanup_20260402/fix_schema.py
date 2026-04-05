import asyncio
import asyncpg

async def fix_schema():
    output = []
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='1470',
        database='kiro2'
    )
    
    try:
        # 1. Add exam_type column
        output.append("1. Adding exam_type column...")
        try:
            await conn.execute("ALTER TABLE questions ADD COLUMN exam_type VARCHAR(10)")
            output.append("   ✅ exam_type added")
        except Exception as e:
            if "already exists" in str(e):
                output.append("   ⚪ exam_type already exists")
            else:
                output.append(f"   ❌ Error: {e}")
        
        # 2. Add subject column
        output.append("2. Adding subject column...")
        try:
            await conn.execute("ALTER TABLE questions ADD COLUMN subject VARCHAR(100)")
            output.append("   ✅ subject added")
        except Exception as e:
            if "already exists" in str(e):
                output.append("   ⚪ subject already exists")
            else:
                output.append(f"   ❌ Error: {e}")
        
        # 3. Add topic column
        output.append("3. Adding topic column...")
        try:
            await conn.execute("ALTER TABLE questions ADD COLUMN topic VARCHAR(200)")
            output.append("   ✅ topic added")
        except Exception as e:
            if "already exists" in str(e):
                output.append("   ⚪ topic already exists")
            else:
                output.append(f"   ❌ Error: {e}")
        
        # 4. Update subject from subjects table
        output.append("4. Updating subject names from subjects table...")
        result = await conn.execute("""
            UPDATE questions q 
            SET subject = s.name 
            FROM subjects s 
            WHERE q.subject_id = s.id AND q.subject IS NULL
        """)
        output.append(f"   ✅ Updated: {result}")
        
        # 5. Set default exam_type
        output.append("5. Setting default exam_type = 'TYT'...")
        result = await conn.execute("UPDATE questions SET exam_type = 'TYT' WHERE exam_type IS NULL")
        output.append(f"   ✅ Updated: {result}")
        
        # 6. Verify
        output.append("\n=== UPDATED SCHEMA ===")
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'questions' 
            ORDER BY ordinal_position
        """)
        for col in columns:
            output.append(f"  {col['column_name']}: {col['data_type']}")
        
        # 7. Show sample data
        output.append("\n=== SAMPLE DATA ===")
        sample = await conn.fetch("SELECT id, stem, subject, exam_type, source FROM questions LIMIT 3")
        for row in sample:
            output.append(f"  {row['id']}: subject={row['subject']}, exam_type={row['exam_type']}, source={row['source']}")
        
        output.append("\n✅ SCHEMA FIX COMPLETE!")
        
    finally:
        await conn.close()
    
    with open("fix_schema_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print("Done! Check fix_schema_output.txt")

asyncio.run(fix_schema())
