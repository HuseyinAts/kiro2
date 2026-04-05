import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

# Nginx config oku
r = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'cat', '/etc/nginx/conf.d/default.conf'],
    capture_output=True, timeout=10
)
print("=== /etc/nginx/conf.d/default.conf ===")
print(r.stdout.decode('utf-8', errors='replace') or "(bos)")
print("STDERR:", r.stderr.decode()[:100])

r2 = subprocess.run(
    ['docker', 'exec', 'kiro2-frontend', 'cat', '/etc/nginx/nginx.conf'],
    capture_output=True, timeout=10
)
print("\n=== /etc/nginx/nginx.conf (son 30 satir) ===")
lines = r2.stdout.decode('utf-8', errors='replace').splitlines()
for l in lines[-30:]:
    print(l)
