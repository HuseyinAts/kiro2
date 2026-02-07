"""Verify performance indexes were created"""
import os
from sqlalchemy import create_engine, text

db_password = os.getenv("DATABASE_PASSWORD", "")
engine = create_engine(f'postgresql://postgres:{db_password}@localhost:5434/turkiye_sinav_db')
conn = engine.connect()

# Get all indexes starting with idx_
result = conn.execute(text("""
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
    ORDER BY tablename, indexname
"""))

print("PERFORMANCE INDEXES CREATED:")
print("=" * 80)

current_table = None
count = 0

for row in result:
    table, index, definition = row
    if table != current_table:
        if current_table is not None:
            print()
        current_table = table
        print(f"\n{table.upper()}:")

    print(f"  - {index}")
    count += 1

print("\n" + "=" * 80)
print(f"Total indexes: {count}")

conn.close()
