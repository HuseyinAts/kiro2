import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

# Exam questions - hangi gunlerde questions vs question_bank kullanilmis?
cur.execute("""
    SELECT DATE(es.created_at) as dt,
        COUNT(CASE WHEN qb.id IS NOT NULL THEN 1 END) as from_qbank,
        COUNT(CASE WHEN q.id IS NOT NULL THEN 1 END) as from_questions,
        COUNT(es.id) as sessions
    FROM exam_sessions es
    JOIN exam_questions eq ON eq.exam_session_id = es.id
    LEFT JOIN question_bank qb ON eq.question_id::text = qb.id::text
    LEFT JOIN questions q ON eq.question_id::text = q.id::text
    GROUP BY DATE(es.created_at)
    ORDER BY dt
""")
print("date        qbank  questions  sessions")
for r in cur.fetchall():
    print(str(r[0]), r[1], r[2], r[3])

# Hangi sinav turu questions tablosundan geliyor?
print("\n--- sinav_turu bazinda ---")
cur.execute("""
    SELECT es.sinav_turu,
        COUNT(CASE WHEN qb.id IS NOT NULL THEN 1 END) as from_qbank,
        COUNT(CASE WHEN q.id IS NOT NULL THEN 1 END) as from_questions
    FROM exam_sessions es
    JOIN exam_questions eq ON eq.exam_session_id = es.id
    LEFT JOIN question_bank qb ON eq.question_id::text = qb.id::text
    LEFT JOIN questions q ON eq.question_id::text = q.id::text
    GROUP BY es.sinav_turu
""")
for r in cur.fetchall():
    print(r)

# Hangi API endpoint'i exam session yaratmis olabilir?
# user_agent / metadata varsa kontrol et
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='exam_sessions'")
cols = [r[0] for r in cur.fetchall()]
print("\nexam_sessions kolonlari:", cols)
