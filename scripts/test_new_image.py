import sys, json, urllib.request, urllib.error, subprocess, psycopg2, re
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
    except Exception as e:
        return {}, 0

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
    except Exception as e:
        return {}, 0

print("=" * 55)
print("YENI IMAGE TEST (docker-compose up --build sonrasi)")
print("=" * 55)

# 1. Login + refresh token
conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM refresh_tokens"); before = cur.fetchone()[0]
data, s = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk = data.get('access_token', '')
import time; time.sleep(1)
cur.execute("SELECT COUNT(*) FROM refresh_tokens"); after = cur.fetchone()[0]
print(f"Auth fix: Login {s}, refresh_tokens {before}->{after} ({'OK' if after>before else 'HATA'})")

# 2. TTS - espeak/gtts
r, s2 = get('/api/v1/tts/voices', atk)
gtts_ok = r.get('gtts_available', False) if isinstance(r, dict) else False
pyttsx_ok = r.get('pyttsx3_available', False) if isinstance(r, dict) else False
print(f"TTS fix: status={s2}, gTTS={gtts_ok}, pyttsx3={pyttsx_ok}")

# 3. Router sayisi - Failed olmali 0
r3, s3 = get('/health')
print(f"Health: {s3}")
r4 = subprocess.run(['docker', 'exec', 'kiro2-backend', 'grep', '-c', 'Registered', '/app/backend.log'],
                     capture_output=True, timeout=10)

# openapi endpoint sayisi
oa, _ = get('/openapi.json')
paths = len(oa.get('paths', {}))
print(f"OpenAPI endpoint sayisi: {paths}")

# 4. Frontend URL
r5 = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'cat', '/usr/share/nginx/html/index.html'],
                     capture_output=True, timeout=10)
html = r5.stdout.decode('utf-8', errors='replace')
js_ref = re.findall(r'/js/index-[^"\']+', html)
js_hash = js_ref[0] if js_ref else '?'
if js_ref:
    r6 = subprocess.run(['docker', 'exec', 'kiro2-frontend', 'sh', '-c',
                          f'cat /usr/share/nginx/html{js_ref[0]}'],
                         capture_output=True, timeout=15)
    js_content = r6.stdout.decode('utf-8', errors='replace')
    has_teknofest = 'teknofest-egitim.com' in js_content
    print(f"Frontend fix: JS={js_hash}, teknofest={'HATA' if has_teknofest else 'TEMIZ'}")

# 5. Redis cache - yeni build'de calistiyor mu?
r7, s7 = get('/api/v1/gamification/profile', atk)
print(f"Gamification (cache test): {s7}")

# 6. Kritik endpointler
print("\nEndpoint testi (Docker :8000):")
tests = [
    ('/api/v1/tts/voices', 'TTS'),
    ('/api/v1/bionic-reading/health', 'Bionic'),
    ('/api/v1/adhd-support/focus-mode/health', 'ADHD'),
    ('/api/v1/social/summary', 'Social'),
    ('/api/v1/veli/cocuklar', 'Veli'),
    ('/api/v1/learning-path/today', 'LearningPath'),
    ('/api/v1/estimate/tyt', 'Estimator'),
    ('/api/v1/soru-meydani/questions', 'SoruMeydani'),
]
ok = 0
for path, label in tests:
    ra, rb = get(path, atk)
    sym = 'OK' if rb < 400 else f'E{rb}'
    if rb < 400: ok += 1
    print(f"  {sym:5} {label}")
print(f"\nSonuc: {ok}/{len(tests)} OK")

# 7. Image ID kontrol
r8 = subprocess.run(['docker', 'images', 'kiro2-backend', '--format', 'table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}'],
                     capture_output=True, timeout=10)
print("\nImage'lar:")
print(r8.stdout.decode('utf-8', errors='replace'))

conn.close()
