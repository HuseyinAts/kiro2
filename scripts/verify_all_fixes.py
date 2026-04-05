import subprocess, re, sys, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 55)
print("1. YENİ BUILD - API URL DOĞRULAMA")
print("=" * 55)

# Yeni index.html hangi JS dosyasini yukluyor?
r = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'cat', '/usr/share/nginx/html/index.html'],
    capture_output=True, timeout=10
)
html = r.stdout.decode('utf-8', errors='replace')
js_ref = re.findall(r'/js/index-[^"\']+', html)
print(f"index.html JS referansi: {js_ref}")

# Yeni JS dosyasinda API URL
if js_ref:
    jf = js_ref[0]
    r2 = subprocess.run(
        ['docker', 'exec', 'kiro2-frontend', 'sh', '-c', f'cat /usr/share/nginx/html{jf}'],
        capture_output=True, timeout=15
    )
    content = r2.stdout.decode('utf-8', errors='replace')
    api_refs = re.findall(r'https?://[a-zA-Z0-9._:-]{5,60}', content)
    bad = [u for u in api_refs if 'teknofest' in u or 'localhost:800' in u]
    print(f"teknofest/localhost URL: {bad if bad else 'YOK (iyi!)'}")
    print(f"Toplam URL ref sayisi: {len(set(api_refs))}")

print("\n" + "=" * 55)
print("2. BACKEND STATUS")
print("=" * 55)

# Local backend hazir mi?
import time; time.sleep(3)
try:
    r3 = urllib.request.urlopen('http://localhost:8001/health', timeout=5)
    print(f"Local :8001 health: {r3.status}")
except Exception as e:
    print(f"Local :8001: {e}")

try:
    r4 = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
    print(f"Docker :8000 health: {r4.status}")
except Exception as e:
    print(f"Docker :8000: {e}")

print("\n" + "=" * 55)
print("3. REFRESH TOKEN FIX DOĞRULAMA")
print("=" * 55)

def post_json(url, body):
    req = urllib.request.Request(url,
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read()), e.code
        except: return {}, e.code

import psycopg2
conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM refresh_tokens")
before = cur.fetchone()[0]
print(f"refresh_tokens ÖNCE: {before} kayit")

data, s = post_json('http://localhost:8001/api/v1/auth/giris',
                     {'email': 'admin@kiro2.com', 'password': 'Kiro2Beta2026@x'})
print(f"Login: {s}")
print(f"response keys: {list(data.keys())}")

cur.execute("SELECT COUNT(*) FROM refresh_tokens")
after = cur.fetchone()[0]
print(f"refresh_tokens SONRA: {after} kayit")
print(f"Refresh token kaydedildi mi: {after > before}")

conn.close()
