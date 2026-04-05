import psycopg2, json

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2', user='postgres', password='postgres')
cur = conn.cursor()

# C1CELL Deneme kitabindan ornek kayitlar
cur.execute("""
    SELECT id, source_page, 
           LEFT(question_text, 80) as qtext,
           option_a, option_b, correct_answer, is_calibrated
    FROM question_bank
    WHERE source_book ILIKE '%C1CELL%Deneme%'
    ORDER BY source_page LIMIT 8
""")
rows = cur.fetchall()
print(f"C1CELL Deneme rows: {len(rows)}")
for r in rows:
    print(f"  page={r[1]} correct={r[5]} calib={r[6]} opt_a={r[3]} qtext={r[2]}")

# Genel istatistik: kac satirda option_a dolu vs bos
cur.execute("""
    SELECT 
        COUNT(*) FILTER(WHERE option_a IS NOT NULL AND option_a != '') as has_options,
        COUNT(*) FILTER(WHERE option_a IS NULL OR option_a = '') as no_options,
        COUNT(*) as total
    FROM question_bank
    WHERE source_book IS NOT NULL
""")
r = cur.fetchone()
print(f"\nOptions stats: has={r[0]}, no_options={r[1]}, total={r[2]}")

# source_page dolu mu?
cur.execute("""
    SELECT COUNT(*) FILTER(WHERE source_page IS NOT NULL) as has_page,
           COUNT(*) as total
    FROM question_bank WHERE source_book IS NOT NULL
""")
r = cur.fetchone()
print(f"source_page dolu: {r[0]}/{r[1]}")

cur.close(); conn.close()
