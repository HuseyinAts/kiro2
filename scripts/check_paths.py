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

ar, _ = post('/api/v1/auth/giris', {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
atk = ar.get('access_token', '')

# OpenAPI'den manipulatifler ve v2 path'lerini bul
oa, _ = get('/openapi.json')
paths = list(oa.get('paths', {}).keys())

manip = [p for p in paths if 'manipulativ' in p]
v2 = [p for p in paths if '/v2/' in p]
print('MANIPULATIF PATHS:', manip[:5])
print('V2 PATHS:', v2[:8])

# Dogru path ile test et
for p in manip[:3]:
    ra, rb = get(p, atk)
    print(str(rb) + ' ' + p + ' keys:' + str(list(ra.keys())[:3] if isinstance(ra,dict) else type(ra).__name__))

# v2 knowledge-graph POST mu?
oa_paths = oa.get('paths', {})
kg_path = '/api/v2/knowledge-graph/recommendations'
if kg_path in oa_paths:
    methods = list(oa_paths[kg_path].keys())
    print('KGraph methods:', methods)
    if 'post' in methods:
        ra, rb = post(kg_path, {'student_id': 'test', 'limit': 5}, atk)
        print('KGraph POST:', rb, str(ra)[:60])
