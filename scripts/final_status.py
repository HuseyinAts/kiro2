import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = psycopg2.connect(host='localhost',port=5434,dbname='kiro2',
                        user='postgres',password='changeme_strong_password_here')
cur = conn.cursor()

print("=== KIRO2 SISTEM DURUMU ===\n")

# 1. question_bank istatistikleri
cur.execute("SELECT COUNT(*), SUM(times_asked), SUM(times_correct) FROM question_bank WHERE times_asked > 0")
cnt, asked, correct = cur.fetchone()
print(f"question_bank gerçek veri: {cnt} soru, {asked} yanıt ({correct} doğru)")

# 2. Exam kaynağı - Mart 8+
cur.execute("""
    SELECT COUNT(*), COUNT(CASE WHEN qb.id IS NOT NULL THEN 1 END)
    FROM exam_questions eq
    JOIN exam_sessions es ON es.id = eq.exam_session_id
    LEFT JOIN question_bank qb ON eq.question_id::text = qb.id::text
    WHERE es.created_at >= '2026-03-08'
""")
total, from_qbank = cur.fetchone()
print(f"Mart 8+ exam_questions: {from_qbank}/{total} = %{int(100*from_qbank/total) if total else 0} question_bank")

# 3. Trigger'lar
cur.execute("SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public'")
triggers = cur.fetchall()
print(f"\nAktif trigger'lar ({len(triggers)}):")
for t in triggers:
    print(f"  {t[0]} -> {t[1]}")

# 4. Celery daily_plans
try:
    cur.execute("SELECT COUNT(*), MAX(created_at) FROM daily_plans")
    cnt2, last = cur.fetchone()
    print(f"\ndaily_plans: {cnt2} kayıt, son: {last}")
except:
    print("\ndaily_plans tablosu yok veya hata")

# 5. Docker servis durumu
import subprocess
result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}', '--filter', 'name=kiro2'],
    capture_output=True, text=True)
print("\nDocker servisleri:")
print(result.stdout.strip())

# 6. Backend port kontrolü
import socket
for port, name in [(8000,'Docker BE'), (8001,'Local BE'), (3000,'Frontend'), (5434,'PostgreSQL'), (6379,'Redis')]:
    s = socket.socket()
    s.settimeout(1)
    ok = s.connect_ex(('localhost', port)) == 0
    s.close()
    print(f"  {'UP' if ok else 'DOWN':4} {name}:{port}")
