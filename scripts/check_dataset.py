import psycopg2, sys, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()

print("=== GERÇEK SORUN ANALİZİ ===\n")

# 1. question_bank durumu
cur.execute("SELECT COUNT(*) FROM question_bank WHERE correct_answer IS NOT NULL AND correct_answer != ''")
qb_with_answer = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated = true")
calibrated = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_active = true")
active = cur.fetchone()[0]
print(f"question_bank:")
print(f"  Toplam: 77356")
print(f"  correct_answer dolu: {qb_with_answer}")
print(f"  is_calibrated=TRUE: {calibrated}")
print(f"  is_active=TRUE: {active}")

# subject_area dagılımı
cur.execute("SELECT subject_area, COUNT(*) FROM question_bank GROUP BY subject_area ORDER BY COUNT(*) DESC LIMIT 10")
print(f"\n  Subject dagilimi:")
for r in cur.fetchall():
    print(f"    {r[0]}: {r[1]}")

# 2. IRT parametreleri
cur.execute("SELECT to_regclass('public.irt_parameters')")
print(f"\nirt_parameters tablosu: {cur.fetchone()[0]}")

# cat tabloları
for tbl in ['cat_sessions', 'cat_items', 'cat_session_items']:
    cur.execute(f"SELECT to_regclass('public.{tbl}')")
    r = cur.fetchone()[0]
    if r:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f"{tbl}: {cnt} kayit")
    else:
        print(f"{tbl}: YOK")

# 3. Eslesmis dosyalardaki soruların question_bank'te karşılığı var mı?
print("\n=== D-DATASET ESLESMIS SORU SAYISI ===")
import os, json as jsonlib
final_dir = r'C:\Users\husey\d-dataset\output\final'
total_matched = 0
for f in os.listdir(final_dir):
    if f.startswith('eslesmis_') and f.endswith('.jsonl'):
        fpath = os.path.join(final_dir, f)
        lines = [jsonlib.loads(l) for l in open(fpath, encoding='utf-8', errors='replace') if l.strip()]
        total_matched += len(lines)
print(f"  Toplam eslestirilmis soru (eslesmis_*.jsonl): {total_matched}")

# 4. question_bank'te hangi alanlar var?
cur.execute("""SELECT column_name, data_type FROM information_schema.columns
               WHERE table_name='question_bank' ORDER BY ordinal_position LIMIT 20""")
cols = cur.fetchall()
print(f"\n=== QUESTION_BANK KOLONLARI (ilk 20) ===")
for c in cols:
    print(f"  {c[0]}: {c[1]}")

conn.close()

# 5. CAT endpoint test
print("\n=== CAT ENDPOINT TEST ===")
def post(url, body, tok=None):
    d = jsonlib.dumps(body).encode()
    h = {'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request('http://localhost:8000' + url, data=d, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return jsonlib.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return jsonlib.loads(e.read()), e.code
        except: return {}, e.code
    except: return {}, 0

auth, _ = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
tok = auth.get('access_token', '')

cat_r, cat_s = post('/api/v1/cat/sessions', {'subject': 'MATEMATIK', 'exam_type': 'TYT'}, tok)
print(f"POST /api/v1/cat/sessions: {cat_s}")
print(f"  Response: {str(cat_r)[:200]}")
