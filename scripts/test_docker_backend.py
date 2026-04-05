import json, urllib.request, urllib.error, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE8 = 'http://localhost:8000'

def post8(url, body, tok=None):
    d = json.dumps(body).encode()
    h = {'Content-Type': 'application/json'}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(BASE8 + url, data=d, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

def get8(url, tok=None):
    h = {}
    if tok: h['Authorization'] = 'Bearer ' + tok
    req = urllib.request.Request(BASE8 + url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

ar, _ = post8('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk = ar.get('access_token', '')
vr, _ = post8('/api/v1/auth/giris', {'email': 'veli_test@kiro2.com', 'password': 'VeliTest2026!'})
vtk = vr.get('access_token', '')

print('=== DOCKER :8000 BACKEND TESTS ===')
tests = [
    ('/api/v1/social/summary', 'SocialSummary (fix test)', atk),
    ('/api/v1/veli/cocuklar', 'VeliCocuklar (fix test)', vtk),
    ('/api/v2/knowledge-graph/stats', 'KGraphV2 (fix test)', atk),
    ('/api/v1/tts/health', 'TTS', atk),
    ('/api/v1/bionic-reading/health', 'Bionic', atk),
    ('/api/v1/soru-meydani/questions', 'SoruMeydani', atk),
    ('/api/v1/youtube/stats', 'YouTube', atk),
]
ok = 0
for path, label, tok in tests:
    ra, rb = get8(path, tok)
    status = 'OK  ' if rb < 400 else 'ERR_' + str(rb)
    if rb < 400: ok += 1
    detail = str(list(ra.keys())[:3]) if isinstance(ra, dict) and rb < 400 else str(ra)[:60]
    print(status + '  ' + label.ljust(25) + '  ' + detail)

print('\n' + str(ok) + '/' + str(len(tests)) + ' Docker backend OK')

# Openapi path sayisi kontrol
oa, _ = get8('/openapi.json')
all_paths = list(oa.get('paths', {}).keys())
v2 = [p for p in all_paths if '/v2/' in p]
print('Toplam endpoint:', len(all_paths), '| v2 endpoint:', len(v2))
