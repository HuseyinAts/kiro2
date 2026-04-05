import subprocess, sys, psycopg2, redis
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: GERÇEK DB BAĞLANTISI - HANGİ ŞIFRE ÇALIŞIYOR?")
print("=" * 60)

for pwd in ['postgres', 'changeme_strong_password_here', 'kiro2', 'admin']:
    try:
        conn = psycopg2.connect(host='localhost', port=5434, dbname='kiro2',
                                user='postgres', password=pwd, connect_timeout=3)
        conn.close()
        print(f"  ÇALIŞIYOR: password='{pwd}'")
    except Exception as e:
        print(f"  BAŞARISIZ: password='{pwd}' — {str(e)[:60]}")

print("\n" + "=" * 60)
print("BÖLÜM 2: REDIS BAĞLANTISI")
print("=" * 60)

for host in ['localhost', '127.0.0.1']:
    try:
        r = redis.Redis(host=host, port=6379, socket_timeout=3)
        pong = r.ping()
        print(f"  Redis {host}:6379 → {pong}")
    except Exception as e:
        print(f"  Redis {host}:6379 → BAŞARISIZ: {str(e)[:80]}")

print("\n" + "=" * 60)
print("BÖLÜM 3: DOCKER BACKEND core/redis_cache.py INCELEME")
print("=" * 60)

# Doker icindeki redis_cache.py dosyasini oku
result = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'grep', '-n', 'localhost\|REDIS\|redis_url', '/app/core/redis_cache.py'],
    capture_output=True, timeout=10
)
out = result.stdout.decode('utf-8', errors='replace')
print("redis_cache.py localhost/REDIS referanslari:")
print(out[:1000] if out else "(bulunamadı)")

print("\n" + "=" * 60)
print("BÖLÜM 4: DOCKER .env DOSYASI")
print("=" * 60)

for envfile in ['/app/.env', '/app/.env.production', '/app/config/.env']:
    result2 = subprocess.run(
        ['docker', 'exec', 'kiro2-backend', 'cat', envfile],
        capture_output=True, timeout=5
    )
    if result2.returncode == 0:
        content = result2.stdout.decode('utf-8', errors='replace')
        print(f"--- {envfile} ---")
        for line in content.splitlines():
            if any(k in line for k in ['DB', 'REDIS', 'DATABASE', 'SECRET', 'POSTGRES']):
                if 'password' in line.lower() or 'secret' in line.lower():
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        line = f"{parts[0]}={parts[1][:8]}***"
                print(f"  {line}")
    else:
        print(f"{envfile}: yok")
