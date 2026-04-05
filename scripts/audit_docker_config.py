import subprocess, sys, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BÖLÜM 1: DOCKER BACKEND KONFIGÜRASYONU")
print("=" * 60)

# Docker backend ENV degerleri
result = subprocess.run(['docker', 'exec', 'kiro2-backend', 'env'], capture_output=True)
env = result.stdout.decode('utf-8', errors='replace')
important_keys = ['DATABASE_URL', 'REDIS_URL', 'REDIS_HOST', 'CELERY_BROKER', 'SECRET_KEY',
                  'ENVIRONMENT', 'DB_HOST', 'DB_PORT', 'POSTGRES_HOST']
print("Docker backend ENV (önemli):")
for line in env.splitlines():
    for key in important_keys:
        if line.startswith(key + '='):
            # parolalari gizle
            val = line.split('=', 1)[1]
            if 'password' in key.lower() or 'secret' in key.lower() or 'key' in key.lower():
                val = val[:8] + '***'
            print(f"  {key}={val}")

print("\n" + "=" * 60)
print("BÖLÜM 2: REDIS BAĞLANTISI")
print("=" * 60)

# Docker icindeki redis baglanip baglanmiyor mu?
result2 = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'python', '-c',
     'import redis; r=redis.Redis(host="kiro2_redis",port=6379,socket_timeout=3); print("redis kiro2_redis:", r.ping())'],
    capture_output=True, timeout=10
)
print("Redis kiro2_redis host:", result2.stdout.decode('utf-8', errors='replace').strip())
if result2.returncode != 0:
    print("STDERR:", result2.stderr.decode('utf-8', errors='replace')[:200])

result3 = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'python', '-c',
     'import redis; r=redis.Redis(host="localhost",port=6379,socket_timeout=3); print("redis localhost:", r.ping())'],
    capture_output=True, timeout=10
)
print("Redis localhost host:", result3.stdout.decode('utf-8', errors='replace').strip())
if result3.returncode != 0:
    print("STDERR:", result3.stderr.decode('utf-8', errors='replace')[:200])

print("\n" + "=" * 60)
print("BÖLÜM 3: DATABASE BAĞLANTISI")
print("=" * 60)

result4 = subprocess.run(
    ['docker', 'exec', 'kiro2-backend', 'python', '-c',
     'import psycopg2; conn=psycopg2.connect(host="kiro2_postgres",port=5432,dbname="kiro2",user="postgres",password="changeme_strong_password_here"); print("DB OK:", conn.get_dsn_parameters())'],
    capture_output=True, timeout=10
)
print("DB kiro2_postgres:", result4.stdout.decode('utf-8', errors='replace').strip()[:200])
if result4.returncode != 0:
    print("STDERR:", result4.stderr.decode('utf-8', errors='replace')[:200])
