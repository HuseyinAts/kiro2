import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

# question_bank'teki mevcut subject_area degerleri
cur.execute("SELECT DISTINCT subject_area, COUNT(*) FROM question_bank GROUP BY subject_area ORDER BY COUNT(*) DESC")
print("question_bank subject_area degerler:")
for r in cur.fetchall():
    print(f"  '{r[0]}': {r[1]} soru")

# topics tablosu var mi?
cur.execute("SELECT to_regclass('public.topics')")
print("\ntopics table:", cur.fetchone()[0])
cur.execute("SELECT to_regclass('public.topic_hierarchy')")
print("topic_hierarchy table:", cur.fetchone()[0])
