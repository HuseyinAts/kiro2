import subprocess, sys, psycopg2, json, urllib.request, urllib.error, re, os
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: REFRESH TOKEN HATASI - KÖK NEDEN")
print("=" * 60)

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()

# refresh_tokens tablosu schema
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='refresh_tokens' ORDER BY ordinal_position")
print("refresh_tokens schema:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} (nullable={r[2]})")

# Kayit var mi?
cur.execute("SELECT COUNT(*) FROM refresh_tokens")
print(f"\nrefresh_tokens kayit sayisi: {cur.fetchone()[0]}")

# auth.py icindeki refresh token persist kodu
result = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'grep', '-n', 'persist_refresh\|refresh_token\|refresh_tokens', '/app/api/auth.py'],
    capture_output=True, timeout=10
)
out = result.stdout.decode('utf-8', errors='replace')
print(f"\nauth.py refresh token satirlari ({len(out.splitlines())} satir):")
print(out[:1500])

print("\n" + "=" * 60)
print("BÖLÜM 2: FRONTEND BUILT JS - API URL NEREYE YAZIYOR?")
print("=" * 60)

# dist/js klasorundeki en buyuk JS dosyasinda API URL ara
js_dir = r'C:\Users\husey\kiro2\frontend\dist\js'
if os.path.exists(js_dir):
    js_files = sorted(
        [os.path.join(js_dir, f) for f in os.listdir(js_dir) if f.endswith('.js')],
        key=os.path.getsize, reverse=True
    )
    print(f"En buyuk 3 JS dosyasi:")
    for jf in js_files[:3]:
        size = os.path.getsize(jf)
        content = open(jf, encoding='utf-8', errors='replace').read()
        # API URL referanslari ara
        api_refs = re.findall(r'["\'](https?://[^"\']{5,50})["\']', content)
        unique_refs = list(dict.fromkeys(api_refs))[:10]
        localhost_refs = [r for r in api_refs if 'localhost' in r]
        print(f"\n  {os.path.basename(jf)} ({size//1024}KB)")
        print(f"  API URL referanslari: {unique_refs[:5]}")
        print(f"  localhost referanslari: {list(dict.fromkeys(localhost_refs))[:3]}")
else:
    print("dist/js yok")

print("\n" + "=" * 60)
print("BÖLÜM 3: GERÇEK LOGIN + KORUNAN ENDPOINT AKIŞI")
print("=" * 60)

# Tam akiş: login → token → /me → veri endpoint
def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                  headers={'Content-Type': 'application/json'}, method='POST')
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

def get_json(url, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

login_data, login_s = post_json('http://localhost:8001/api/v1/auth/giris',
                                  {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
print(f"Login status: {login_s}")
print(f"Login response keys: {list(login_data.keys())}")

if login_s == 200:
    tok = login_data.get('access_token', '')
    ref_tok = login_data.get('refresh_token', '')
    print(f"access_token: {'OK (' + str(len(tok)) + ' chars)' if tok else 'YOK'}")
    print(f"refresh_token: {'OK (' + str(len(ref_tok)) + ' chars)' if ref_tok else 'YOK'}")

    me, me_s = get_json('http://localhost:8001/api/v1/auth/me', tok)
    print(f"\n/me status: {me_s}")
    if me_s == 200:
        print(f"/me response: id={me.get('id','?')[:16]}... role={me.get('role','?')}")

    # Öğrenci login
    student_r, student_s = post_json('http://localhost:8001/api/v1/auth/giris',
                                       {'email': 'ogrenci_veli_test@kiro2.com', 'password': 'OgrenciTest2026!'})
    print(f"\nÖğrenci login: {student_s}")
    if student_s == 200:
        stok = student_r.get('access_token', '')
        # Öğrenciye özel endpointleri test et
        for ep in ['/api/v1/learning-path/today', '/api/v1/learning-path/status',
                   '/api/v1/estimate/tyt', '/api/v1/gamification/profile']:
            r, s = get_json(f'http://localhost:8001{ep}', stok)
            sym = 'OK  ' if s < 400 else f'ERR_{s}'
            detail = str(list(r.keys())[:3]) if isinstance(r, dict) and s < 400 else str(r)[:80]
            print(f"  {sym} {ep}  {detail}")
    else:
        print(f"  Öğrenci login başarısız: {student_r}")

conn.close()
