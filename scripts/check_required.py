"""emergency content loader - sadece zorunlu kolonlarla insert"""
import psycopg2, uuid

conn = psycopg2.connect(
    host='localhost', port=5434, dbname='kiro2',
    user='postgres', password='changeme_strong_password_here'
)
cur = conn.cursor()

# Zorunlu kolonlari kesfet
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name='question_bank'
      AND is_nullable='NO'
      AND column_default IS NULL
    ORDER BY ordinal_position
""")
required = [r[0] for r in cur.fetchall()]
print("Zorunlu kolonlar:", required)
conn.close()
