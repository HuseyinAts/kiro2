import os, sys, re, psycopg2, subprocess
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: FRONTEND API CLIENT KONFIGÜRASYONU")
print("=" * 60)

# API client dosyalarini bul
fe_src = r'C:\Users\husey\kiro2\frontend\src'
api_files = []
for root, dirs, files in os.walk(fe_src):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git']]
    for f in files:
        if any(k in f.lower() for k in ['api', 'client', 'axios', 'fetch', 'http', 'request']):
            if f.endswith(('.ts', '.tsx', '.js')):
                api_files.append(os.path.join(root, f))

print(f"API ile ilgili dosyalar ({len(api_files)}):")
for f in api_files[:10]:
    print(f"  {f.replace(fe_src, '').lstrip(os.sep)}")

# En kritik dosyayi oku
for af in api_files[:5]:
    try:
        content = open(af, encoding='utf-8', errors='replace').read()
        if any(k in content for k in ['baseURL', 'BASE_URL', 'API_URL', 'VITE_API']):
            print(f"\n--- {os.path.basename(af)} ---")
            for i, line in enumerate(content.splitlines(), 1):
                if any(k in line for k in ['baseURL', 'BASE_URL', 'API_URL', 'VITE_API',
                                            'localhost', 'axios.create', 'baseUrl']):
                    print(f"  {i}: {line.strip()[:100]}")
    except:
        pass

print("\n" + "=" * 60)
print("BÖLÜM 2: VITE.CONFIG.TS - PROXY AYARLARI")
print("=" * 60)

vc = r'C:\Users\husey\kiro2\frontend\vite.config.ts'
if os.path.exists(vc):
    content = open(vc, encoding='utf-8', errors='replace').read()
    print(content[:2000])
else:
    print("vite.config.ts yok")

print("\n" + "=" * 60)
print("BÖLÜM 3: KULLANICI LISTESI - GERÇEK EMAIL'LER")
print("=" * 60)

conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                         user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("""
    SELECT email, role::text, first_name, last_name, is_active
    FROM users
    ORDER BY created_at
    LIMIT 15
""")
print(f"{'email':40} {'role':15} {'ad':15} {'aktif'}")
for r in cur.fetchall():
    print(f"{str(r[0]):40} {str(r[1]):15} {str(r[2] or ''):15} {r[4]}")

print("\n" + "=" * 60)
print("BÖLÜM 4: JWT MANAGER - _save_refresh_token_to_db KODU")
print("=" * 60)

result = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'grep', '-n',
     'save_refresh\|persist_refresh\|refresh_token', '/app/core/jwt_auth.py'],
    capture_output=True, timeout=10
)
out = result.stdout.decode('utf-8', errors='replace')
print(f"jwt_auth.py refresh token ({len(out.splitlines())} satir):")
print(out[:1500])

conn.close()
