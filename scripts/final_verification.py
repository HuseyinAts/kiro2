import sys, json, urllib.request, urllib.error, subprocess, psycopg2, re, time
sys.stdout.reconfigure(encoding='utf-8')

def post(base, url, body, tok=None):
    d = json.dumps(body).encode()
    h = {'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(base + url, data=d, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code
    except Exception as e:
        return {}, 0

def get(base, url, tok=None):
    h = {}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(base + url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code
    except Exception as e:
        return {}, 0

B8 = 'http://localhost:8000'
B1 = 'http://localhost:8001'

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()

print("=" * 60)
print("1. SERVISLER")
print("=" * 60)
r = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}',
                    '--filter', 'name=kiro2'], capture_output=True)
print(r.stdout.decode('utf-8', errors='replace'))

print("=" * 60)
print("2. BACKEND SAGLIK")
print("=" * 60)
for base, label in [(B8, 'Docker :8000'), (B1, 'Local :8001')]:
    r, s = get(base, '/health')
    ok = s == 200
    print(f"  {'OK' if ok else 'FAIL':4} {label}  status={s}")

print("=" * 60)
print("3. AUTH + REFRESH TOKEN")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM refresh_tokens"); before = cur.fetchone()[0]
data, s = post(B1, '/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk = data.get('access_token', '')
print(f"  Login :8001: {s}, token: {'OK' if atk else 'FAIL'}")
time.sleep(1)
cur.execute("SELECT COUNT(*) FROM refresh_tokens"); after = cur.fetchone()[0]
print(f"  refresh_tokens: {before} -> {after} ({'KAYDEDILDI' if after > before else 'HATA'})")

data8, s8 = post(B8, '/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk8 = data8.get('access_token', '')
print(f"  Login :8000: {s8}, token: {'OK' if atk8 else 'FAIL'}")

print("=" * 60)
print("4. KRITIK ENDPOINT'LER (her iki backend)")
print("=" * 60)
endpoints = [
    ('/api/v1/learning-path/today', 'LearningPath Today'),
    ('/api/v1/estimate/tyt', 'TYT Estimator'),
    ('/api/v1/gamification/profile', 'Gamification'),
    ('/api/v1/social/summary', 'Social Summary'),
    ('/api/v1/tts/voices', 'TTS Voices'),
    ('/api/v1/veli/cocuklar', 'Veli Cocuklar'),
    ('/api/v2/knowledge-graph/stats', 'KGraph V2'),
    ('/api/v1/bionic-reading/health', 'Bionic'),
    ('/api/v1/soru-meydani/questions', 'SoruMeydani'),
]
ok_8 = ok_1 = 0
for path, label in endpoints:
    tok = atk if ':8001' not in path else atk
    r8, s8r = get(B8, path, atk8)
    r1, s1r = get(B1, path, atk)
    if s8r < 400: ok_8 += 1
    if s1r < 400: ok_1 += 1
    sym8 = 'OK  ' if s8r < 400 else f'E{s8r}'
    sym1 = 'OK  ' if s1r < 400 else f'E{s1r}'
    print(f"  {sym8}|{sym1}  {label}")
print(f"\n  Docker :8000: {ok_8}/{len(endpoints)} OK")
print(f"  Local  :8001: {ok_1}/{len(endpoints)} OK")

print("=" * 60)
print("5. FRONTEND API URL (KRITIK FIX)")
print("=" * 60)
r = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'cat',
                    '/usr/share/nginx/html/index.html'], capture_output=True, timeout=10)
html = r.stdout.decode('utf-8', errors='replace')
js_ref = re.findall(r'/js/index-[^"\']+', html)
print(f"  index.html JS: {js_ref}")
if js_ref:
    r2 = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'sh', '-c',
                          f'cat /usr/share/nginx/html{js_ref[0]}'],
                         capture_output=True, timeout=15)
    content = r2.stdout.decode('utf-8', errors='replace')
    has_tek = 'teknofest-egitim.com' in content
    print(f"  teknofest URL: {'HALA VAR (KOTU)' if has_tek else 'YOK (IYI)'}")
    print(f"  Bundle boyutu: {len(content)//1024}KB")

print("=" * 60)
print("6. DOCKER BACKEND LOG HATALARI (yeni)")
print("=" * 60)
r3 = subprocess.run(['docker', 'logs', 'kiro2-backend', '--tail', '100'], capture_output=True)
log = r3.stdout.decode('utf-8', errors='replace') + r3.stderr.decode('utf-8', errors='replace')
errs = [l for l in log.splitlines() if
        any(k in l for k in ['ERROR', 'CRITICAL', 'gtts', 'pyttsx3', 'Loaded:', 'Failed:'])]
for e in errs[:20]:
    print(f"  {e[:120]}")

print("=" * 60)
print("7. VERITABANI DURUMU")
print("=" * 60)
checks = [
    ("question_bank times_asked > 0", "SELECT COUNT(*) FROM question_bank WHERE times_asked > 0"),
    ("refresh_tokens", "SELECT COUNT(*) FROM refresh_tokens"),
    ("daily_plans", "SELECT COUNT(*) FROM daily_plans"),
    ("student_abilities", "SELECT COUNT(*) FROM student_abilities"),
    ("subjects", "SELECT COUNT(*) FROM subjects"),
    ("triggers", "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='public'"),
]
for label, sql in checks:
    try:
        cur.execute(sql)
        print(f"  {label}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"  {label}: HATA - {e}")

conn.close()
print("\n=== DOGRULAMA TAMAMLANDI ===")
