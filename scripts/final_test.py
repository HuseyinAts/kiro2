import json, urllib.request, urllib.error, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8001'

def post(url, body, tok=None):
    d = json.dumps(body).encode()
    h = {'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(BASE + url, data=d, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

def get(url, tok=None):
    h = {}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(BASE + url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

# Login
ar, _ = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk = ar.get('access_token', '')
vr, _ = post('/api/v1/auth/giris', {'email': 'veli_test@kiro2.com', 'password': 'VeliTest2026!'})
vtk = vr.get('access_token', '')

print('=== LOGIN ===')
print('admin:', 'OK' if atk else 'FAIL')
print('veli:', 'OK' if vtk else 'FAIL')

print('\n=== ENDPOINT TESTS ===')
tests = [
    ('/api/v1/tts/voices', 'TTS', atk),
    ('/api/v1/bionic-reading/health', 'Bionic Reading', atk),
    ('/api/v1/adhd-support/focus-mode/health', 'ADHD Focus', atk),
    ('/api/v1/multisensory/health', 'Multisensory', atk),
    ('/api/v1/manipulatives/list', 'Manipulatifler', atk),
    ('/api/v1/eba/taxonomy/subjects', 'EBA', atk),
    ('/api/v1/youtube/stats', 'YouTube', atk),
    ('/api/v1/soru-meydani/questions', 'Soru Meydani', atk),
    ('/api/v1/usta-cirak/pairs', 'Usta-Cirak', atk),
    ('/api/v1/cozum-duellosu/active/list', 'Cozum Duellosu', atk),
    ('/api/v1/social/summary', 'Social Summary', atk),
    ('/api/v2/knowledge-graph/recommendations', 'KGraph v2', atk),
    ('/api/v1/veli/cocuklar', 'Veli Cocuklar', vtk),
]

ok = 0
for path, label, tok in tests:
    ra, rb = get(path, tok)
    status = 'OK  ' if rb < 400 else 'ERR_' + str(rb)
    if rb < 400: ok += 1
    detail = str(list(ra.keys())[:3]) if isinstance(ra, dict) and rb < 400 else str(ra)[:60]
    print(status + '  ' + label.ljust(20) + '  ' + detail)

print('\n' + str(ok) + '/' + str(len(tests)) + ' endpoint OK')

# Frontend check
print('\n=== FRONTEND ===')
try:
    fr = urllib.request.urlopen('http://localhost:3000/', timeout=8)
    fc = fr.read().decode('utf-8', errors='replace')
    title = [l.strip() for l in fc.split('\n') if '<title' in l]
    print('HTTP:', fr.status, title[0][:60] if title else 'no title')
    print('Build timestamp check:', '21:46' in fc or '2026' in fc)
except Exception as e:
    print('Frontend ERR:', str(e)[:80])

# Backend router count from log
print('\n=== BACKEND STATUS ===')
try:
    log = open('C:/Users/husey/kiro2/backend/uvicorn_new.log', encoding='utf-8', errors='replace').read()
    loaded = [l for l in log.split('\n') if 'Loaded:' in l]
    failed = [l for l in log.split('\n') if 'Failed:' in l]
    print(loaded[-1].strip() if loaded else 'no loaded line')
    print(failed[-1].strip() if failed else 'no failed line')
except:
    print('log okunamadi')
