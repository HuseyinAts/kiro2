import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

# student_abilities tablosu yoksa hangi tablo theta/ability veriyi tutuyor?
ability_tables = ['student_abilities', 'irt_parameters', 'user_abilities',
                  'user_item_fsrs', 'kiro2_learning_events',
                  'cat_sessions', 'cat_session_items']
for t in ability_tables:
    cur.execute(f"SELECT to_regclass('public.{t}')")
    exists = cur.fetchone()[0]
    if exists:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position LIMIT 8")
        cols = [r[0] for r in cur.fetchall()]
        print(f"{t:30} {count:6} rows  cols: {cols}")
    else:
        print(f"{t:30}  NOT EXISTS")
