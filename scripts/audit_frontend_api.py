import subprocess, sys, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: FRONTEND .ENV DOSYALARI")
print("=" * 60)

import os
fe_root = r'C:\Users\husey\kiro2\frontend'
for fname in ['.env', '.env.production', '.env.local', '.env.development']:
    fpath = os.path.join(fe_root, fname)
    if os.path.exists(fpath):
        print(f"--- {fname} ---")
        for line in open(fpath, encoding='utf-8', errors='replace').readlines():
            if line.strip() and not line.startswith('#'):
                print(f"  {line.rstrip()}")
    else:
        print(f"{fname}: yok")

print("\n" + "=" * 60)
print("BÖLÜM 2: FRONTEND API BASE URL - AKTÜEL BUILD")
print("=" * 60)

# dist/assets klasörünü kontrol et - hangi URL hardcode edilmiş?
assets_dir = os.path.join(fe_root, 'dist', 'assets')
if os.path.exists(assets_dir):
    js_files = [f for f in os.listdir(assets_dir) if f.endswith('.js')]
    print(f"JS dosya sayisi: {len(js_files)}")
    # en buyuk JS dosyasinda localhost:800x referanslarini bul
    js_files_sorted = sorted([os.path.join(assets_dir, f) for f in js_files],
                              key=lambda x: os.path.getsize(x), reverse=True)
    for jf in js_files_sorted[:3]:
        size = os.path.getsize(jf)
        print(f"\n  {os.path.basename(jf)} ({size//1024}KB)")
        content = open(jf, encoding='utf-8', errors='replace').read()
        import re
        urls = re.findall(r'localhost:\d{4}', content)
        url_counts = {}
        for u in urls:
            url_counts[u] = url_counts.get(u, 0) + 1
        print(f"  localhost referanslar: {url_counts}")

print("\n" + "=" * 60)
print("BÖLÜM 3: GERÇEK API ENDPOINT TEST - PORT 8000 vs 8001")
print("=" * 60)

def test_endpoint(base, path, token=None, method='GET', body=None):
    url = base + path
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return r.status, None
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read())
            return e.code, err.get('detail', str(err))[:80]
        except:
            return e.code, str(e)[:80]
    except Exception as e:
        return 0, str(e)[:80]

# Login
s8, _ = test_endpoint('http://localhost:8000', '/api/v1/auth/giris',
                        body={'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'}, method='POST')
print(f"Docker :8000 login: {s8}")

s1, _ = test_endpoint('http://localhost:8001', '/api/v1/auth/giris',
                        body={'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'}, method='POST')
print(f"Local  :8001 login: {s1}")

# Token al
for base, label in [('http://localhost:8000', ':8000'), ('http://localhost:8001', ':8001')]:
    r, _ = test_endpoint(base, '/api/v1/auth/giris',
                          body={'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'}, method='POST')
    # token cek
    req2 = urllib.request.Request(base + '/api/v1/auth/giris',
                                    data=json.dumps({'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'}).encode(),
                                    headers={'Content-Type': 'application/json'}, method='POST')
    try:
        resp = urllib.request.urlopen(req2, timeout=8)
        data = json.loads(resp.read())
        tok = data.get('access_token', '')
    except:
        tok = ''

    if not tok:
        print(f"{label}: token alinamadi")
        continue

    # kritik endpointleri test et
    endpoints = [
        '/api/v1/learning-path/today',
        '/api/v1/learning-path/status',
        '/api/v1/estimate/tyt',
        '/api/v1/cat/sessions',
        '/api/v1/placement/start',
        '/api/v1/fsrs/due',
        '/api/v1/gamification/profile',
        '/api/v1/osym-exam/active',
        '/api/v1/social/summary',
        '/api/v1/veli/cocuklar',
    ]
    print(f"\n--- {label} endpoint testleri ---")
    for ep in endpoints:
        s, err = test_endpoint(base, ep, token=tok)
        sym = 'OK  ' if s < 400 else f'ERR_{s}'
        print(f"  {sym} {ep}" + (f" → {err}" if err else ""))
