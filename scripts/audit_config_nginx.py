import os, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')

fe_src = r'C:\Users\husey\kiro2\frontend\src'

print("=" * 60)
print("BÖLÜM 1: appConfig / config DOSYASI")
print("=" * 60)

# config dosyalarini bul
config_files = []
for root, dirs, files in os.walk(fe_src):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules']]
    for f in files:
        if ('config' in f.lower() or 'appconfig' in f.lower()) and f.endswith(('.ts', '.tsx', '.js')):
            config_files.append(os.path.join(root, f))

print(f"Config dosyalari ({len(config_files)}):")
for cf in config_files[:8]:
    print(f"  {cf.replace(fe_src,'').lstrip(os.sep)}")

# Kritik config dosyasini oku
for cf in config_files[:5]:
    try:
        content = open(cf, encoding='utf-8', errors='replace').read()
        if any(k in content for k in ['baseURL', 'VITE_API', 'api', 'API_URL']):
            print(f"\n--- {os.path.basename(cf)} ---")
            print(content[:1500])
            break
    except:
        pass

print("\n" + "=" * 60)
print("BÖLÜM 2: VITE.CONFIG.TS DEVAM - BUILD + PROXY BÖLÜMÜ")
print("=" * 60)

vc = open(r'C:\Users\husey\kiro2\frontend\vite.config.ts', encoding='utf-8', errors='replace').read()
# build ve server bölümlerini bul
for section in ['build', 'server', 'proxy', 'resolve']:
    idx = vc.find(section)
    if idx > 0:
        print(f"\n[{section} bölümü - satir ~{vc[:idx].count(chr(10))}]")
        print(vc[idx:idx+300])

print("\n" + "=" * 60)
print("BÖLÜM 3: NGINX CONFIG - PROXY AYARLARI")
print("=" * 60)

# Docker nginx config
result = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'cat', '/etc/nginx/conf.d/default.conf'],
    capture_output=True, timeout=10
)
nginx_conf = result.stdout.decode('utf-8', errors='replace')
if nginx_conf:
    print("nginx default.conf:")
    print(nginx_conf[:2000])
else:
    # /etc/nginx/nginx.conf dene
    result2 = subprocess.run(
        ['docker', 'exec', 'kiro2-frontend', 'cat', '/etc/nginx/nginx.conf'],
        capture_output=True, timeout=10
    )
    print("nginx.conf:")
    print(result2.stdout.decode('utf-8', errors='replace')[:1500])

print("\n" + "=" * 60)
print("BÖLÜM 4: CELERY BEAT LOG - GÖREVLER ÇALIŞIYOR MU?")
print("=" * 60)

result3 = subprocess.run(
    ['docker', 'logs', 'kiro2-celery-beat', '--tail', '30'],
    capture_output=True
)
beat_log = result3.stdout.decode('utf-8', errors='replace') + result3.stderr.decode('utf-8', errors='replace')
print("celery-beat son 30 satır:")
print(beat_log[:2000])
