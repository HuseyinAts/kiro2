"""
Database table checker script.
SECURITY FIX: SQL Injection önleme - whitelist validation eklendi.
"""
import re
import sqlite3

# SECURITY: Sadece izin verilen tablo isimleri (whitelist)
ALLOWED_TABLE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def is_valid_table_name(table_name: str) -> bool:
    """Tablo isminin güvenli olduğunu doğrula."""
    return bool(ALLOWED_TABLE_PATTERN.match(table_name))


conn = sqlite3.connect("turkiye_sinav.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"TOTAL TABLES: {len(tables)}")
for table in tables:
    # SECURITY FIX: Whitelist validation ile SQL Injection önleme
    if not is_valid_table_name(table):
        print(f"  - {table}: SKIPPED (invalid table name)")
        continue
    # Parameterized query kullanılamadığı için (tablo isimleri parametre olamaz)
    # whitelist validation ile güvenlik sağlanır
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]
    print(f"  - {table}: {count} rows")
conn.close()
