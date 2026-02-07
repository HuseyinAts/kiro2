"""
SQLite schema checker script.
SECURITY FIX: SQL Injection önleme - whitelist validation eklendi.
"""
import re
import sqlite3

# SECURITY: Sadece izin verilen tablo isimleri (whitelist)
ALLOWED_TABLE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def is_valid_table_name(table_name: str) -> bool:
    """Tablo isminin güvenli olduğunu doğrula."""
    return bool(ALLOWED_TABLE_PATTERN.match(table_name))


conn = sqlite3.connect('kiro2.db')
cursor = conn.cursor()

print("===== EXISTING DATABASE TABLES =====\n")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]

    # SECURITY FIX: Whitelist validation ile SQL Injection önleme
    if not is_valid_table_name(table_name):
        print(f"⚠️ Table: {table_name} - SKIPPED (invalid table name)")
        continue

    print(f"📊 Table: {table_name}")

    # Get column info - tablo ismi whitelist ile doğrulandı
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    columns = cursor.fetchall()

    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        pk_marker = " 🔑 PK" if pk else ""
        print(f"   - {col_name}: {col_type}{pk_marker}")
    print("")

conn.close()
print("✅ Schema check complete")
