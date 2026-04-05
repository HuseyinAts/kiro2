import psycopg2, sys, os
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2', user='postgres', password='postgres')
cur = conn.cursor()

queries = {
    'question_bank (toplam)': 'SELECT COUNT(*) FROM question_bank',
    'question_bank (correct_answer dolu)': "SELECT COUNT(*) FROM question_bank WHERE correct_answer IS NOT NULL AND correct_answer != ''",
    'question_bank (hic yanitlanmamis)': 'SELECT COUNT(*) FROM question_bank WHERE times_asked = 0',
    'gercek yanitlanan soru': 'SELECT COUNT(*) FROM question_bank WHERE times_asked > 0',
    'aktif kullanici': 'SELECT COUNT(*) FROM users WHERE is_active = true',
    'ogrenci': "SELECT COUNT(*) FROM users WHERE role::text = 'STUDENT' AND is_active = true",
    'bugunun plani': 'SELECT COUNT(*) FROM daily_plans WHERE plan_date = CURRENT_DATE',
    'gercek learning event': "SELECT COUNT(*) FROM kiro2_learning_events WHERE event_type IN ('exam_answer','cat_answer')",
    'sintetik event': "SELECT COUNT(*) FROM kiro2_learning_events WHERE event_type = 'synthetic_response'",
    'tamamlanan sinav': "SELECT COUNT(*) FROM exam_sessions WHERE status = 'completed'",
    'refresh_tokens': 'SELECT COUNT(*) FROM refresh_tokens',
}

print("=== PLATFORM DURUMU ===\n")
for label, sql in queries.items():
    cur.execute(sql)
    print(f"  {label}: {cur.fetchone()[0]}")

# emergency_content.sql var mi?
paths = [
    r'C:\Users\husey\kiro2\emergency_content.sql',
    r'C:\Users\husey\kiro2\emergency_content_v2.sql',
    r'C:\Users\husey\kiro2\backend\emergency_content.sql',
]
print('\n=== YÜKLENMEYI BEKLEYEN DOSYALAR ===')
for p in paths:
    exists = os.path.exists(p)
    size = round(os.path.getsize(p)/1024/1024, 1) if exists else 0
    print(f"  {'VAR' if exists else 'YOK':4} {p.split(chr(92))[-1]} ({size}MB)")

conn.close()
