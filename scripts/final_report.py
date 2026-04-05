import sys, json, urllib.request, urllib.error, psycopg2, subprocess, re
sys.stdout.reconfigure(encoding='utf-8')

B = 'http://localhost:8000'

def post(url, body, tok=None):
    d = json.dumps(body).encode()
    h = {'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(B + url, data=d, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code
    except: return {}, 0

def get(url, tok=None):
    h = {}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(B + url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code
    except: return {}, 0

auth, _ = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
tok = auth.get('access_token', '')

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2', user='postgres', password='postgres')
cur = conn.cursor()

print("=" * 60)
print("KIRO2 FINAL SISTEM RAPORU")
print("=" * 60)

# Docker servisleri
r = subprocess.run(['docker', 'ps', '--filter', 'name=kiro2', '--format',
                    'table {{.Names}}\t{{.Status}}'], capture_output=True)
print("\n[DOCKER SERVISLER]")
print(r.stdout.decode('utf-8', errors='replace').strip())

# Image bilgisi
r2 = subprocess.run(['docker', 'images', 'kiro2-backend', '--format',
                     '{{.Repository}}:{{.Tag}} | {{.ID}} | {{.CreatedSince}} | {{.Size}}'],
                     capture_output=True)
print("\n[IMAGE]")
print(r2.stdout.decode('utf-8', errors='replace').strip())

# Auth
cur.execute("SELECT COUNT(*) FROM refresh_tokens"); rt = cur.fetchone()[0]
print(f"\n[AUTH]  refresh_tokens: {rt}")

# Endpoint'ler
tests = [
    '/api/v1/tts/voices', '/api/v1/bionic-reading/health', '/api/v1/adhd-support/focus-mode/health',
    '/api/v1/multisensory/health', '/api/v1/social/summary', '/api/v1/veli/cocuklar',
    '/api/v1/learning-path/today', '/api/v1/estimate/tyt', '/api/v1/gamification/profile',
    '/api/v1/soru-meydani/questions', '/api/v1/usta-cirak/pairs', '/api/v1/cozum-duellosu/active/list',
]
ok = sum(1 for ep in tests if get(ep, tok)[1] < 400)
print(f"\n[ENDPOINT] {ok}/{len(tests)} OK")

# DB
for label, sql in [
    ('refresh_tokens', 'SELECT COUNT(*) FROM refresh_tokens'),
    ('daily_plans', 'SELECT COUNT(*) FROM daily_plans'),
    ('student_abilities', 'SELECT COUNT(*) FROM student_abilities'),
    ('question_bank (times_asked>0)', 'SELECT COUNT(*) FROM question_bank WHERE times_asked > 0'),
    ('triggers', "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='public'"),
]:
    cur.execute(sql); print(f"  {label}: {cur.fetchone()[0]}")

# Frontend
r3 = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'cat', '/usr/share/nginx/html/index.html'],
                     capture_output=True, timeout=10)
html = r3.stdout.decode('utf-8', errors='replace')
js_ref = re.findall(r'/js/index-[^"\']+', html)
if js_ref:
    r4 = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'sh', '-c',
                          f'cat /usr/share/nginx/html{js_ref[0]}'], capture_output=True, timeout=15)
    js = r4.stdout.decode('utf-8', errors='replace')
    print(f"\n[FRONTEND] JS: {js_ref[0]}, teknofest: {'HATA' if 'teknofest-egitim.com' in js else 'TEMIZ'}")

print("\n" + "=" * 60)
conn.close()
