import subprocess, sys, os, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: FRONTEND DIST YAPISI")
print("=" * 60)

fe_dist = r'C:\Users\husey\kiro2\frontend\dist'
for root, dirs, files in os.walk(fe_dist):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    level = root.replace(fe_dist, '').count(os.sep)
    indent = '  ' * level
    folder_name = os.path.basename(root)
    file_count = len(files)
    total_size = sum(os.path.getsize(os.path.join(root, f)) for f in files)
    print(f"{indent}{folder_name}/ ({file_count} dosya, {total_size//1024}KB)")
    if level < 2:
        for f in sorted(files)[:5]:
            fsize = os.path.getsize(os.path.join(root, f))
            print(f"{indent}  {f} ({fsize//1024}KB)")

print("\n" + "=" * 60)
print("BÖLÜM 2: DOCKER FRONTEND NE SUNUYOR?")
print("=" * 60)

# Docker frontend icindeki nginx html klasoru
result = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'ls', '-la', '/usr/share/nginx/html/'],
    capture_output=True, timeout=10
)
print("Docker frontend /usr/share/nginx/html/:")
print(result.stdout.decode('utf-8', errors='replace'))

result2 = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'ls', '-la', '/usr/share/nginx/html/assets/'],
    capture_output=True, timeout=10
)
print("assets/ klasoru:")
print(result2.stdout.decode('utf-8', errors='replace')[:500] or result2.stderr.decode('utf-8', errors='replace')[:200])

result3 = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'ls', '/usr/share/nginx/html/js/'],
    capture_output=True, timeout=10
)
print("js/ klasoru:")
print(result3.stdout.decode('utf-8', errors='replace')[:300] or "yok")

# index.html icinde hangi port var?
result4 = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'grep', '-o', 'localhost:[0-9]*', '/usr/share/nginx/html/index.html'],
    capture_output=True, timeout=10
)
out4 = result4.stdout.decode('utf-8', errors='replace').strip()
print(f"\nindex.html'deki localhost referanslari: {out4 if out4 else '(yok)'}")

# JS dosyalarindaki localhost aramalari
result5 = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'sh', '-c',
     'grep -rl "localhost:800" /usr/share/nginx/html/ 2>/dev/null | head -5'],
    capture_output=True, timeout=10
)
print("localhost:800x bulunan dosyalar:")
print(result5.stdout.decode('utf-8', errors='replace') or "(bulunamadi)")

print("\n" + "=" * 60)
print("BÖLÜM 3: PLACEMENT/START 404 SEBEBI")
print("=" * 60)

# OpenAPI'den placement path bul
req = urllib.request.Request('http://localhost:8001/openapi.json')
try:
    resp = urllib.request.urlopen(req, timeout=10)
    oa = json.loads(resp.read())
    placement_paths = [p for p in oa.get('paths', {}) if 'placement' in p.lower() or 'assessment' in p.lower()]
    print("placement/assessment endpoint'leri:")
    for p in sorted(placement_paths):
        methods = list(oa['paths'][p].keys())
        print(f"  {methods} {p}")
except Exception as e:
    print(f"OpenAPI hatasi: {e}")

print("\n" + "=" * 60)
print("BÖLÜM 4: BCRYPT / REFRESH TOKEN SORUNU")
print("=" * 60)

# Docker backend'de bcrypt versiyonu
result6 = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'python', '-c',
     'import bcrypt; print("bcrypt ver:", bcrypt.__version__); print("has __about__:", hasattr(bcrypt, "__about__"))'],
    capture_output=True, timeout=10
)
print("Docker bcrypt:")
print(result6.stdout.decode('utf-8', errors='replace'))

# refresh_token tablosu var mi?
import psycopg2
conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT to_regclass('public.refresh_tokens')")
print(f"refresh_tokens tablosu: {cur.fetchone()[0]}")
cur.execute("SELECT to_regclass('public.user_sessions')")
print(f"user_sessions tablosu: {cur.fetchone()[0]}")
conn.close()
