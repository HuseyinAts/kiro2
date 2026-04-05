import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='student_abilities' ORDER BY ordinal_position")
print("student_abilities schema:", cur.fetchall())

# subjects tablosu var mi?
cur.execute("SELECT to_regclass('public.subjects')")
print("subjects table:", cur.fetchone()[0])
cur.execute("SELECT id, name FROM subjects LIMIT 10")
print("subjects sample:", cur.fetchall())
