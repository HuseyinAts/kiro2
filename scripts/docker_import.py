import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

# Dogru CMD ile docker import
cmd = [
    'docker', 'import',
    r'C:\Users\husey\kiro2\kiro2_backend_v2.tar',
    'kiro2-backend:v2-fixed',
    '--change', 'WORKDIR /app',
    '--change', 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
]
r = subprocess.run(cmd, capture_output=True, timeout=120)
out = r.stdout.decode('utf-8', errors='replace').strip()
err = r.stderr.decode('utf-8', errors='replace').strip()
print("returncode:", r.returncode)
print("stdout:", out[:200])
if err: print("stderr:", err[:200])
