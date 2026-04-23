import os
import subprocess

env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}
cwd = r"c:\Users\husey\kiro2\backend"
python = r"c:\Users\husey\kiro2\.venv\Scripts\python.exe"

print("=== Coverage Run ===")
r1 = subprocess.run(
    [python, "-m", "coverage", "run",
     "--source=api,services,core,algorithms,analytics,agents",
     "-m", "pytest", "tests/unit/", "tests/integration/",
     "-p", "no:cacheprovider",
     "--tb=no", "-q", "--maxfail=500"],
    cwd=cwd, env=env, timeout=600,
    capture_output=True, encoding='utf-8', errors='replace')
print("Exit:", r1.returncode)
if r1.stdout:
    print("STDOUT tail:", r1.stdout[-500:])

print("\n=== Coverage Report ===")
r2 = subprocess.run(
    [python, "-m", "coverage", "report", "--skip-empty"],
    cwd=cwd, capture_output=True, encoding='utf-8', errors='replace', env=env)
if r2.stdout:
    lines = r2.stdout.strip().split('\n')
    for line in lines:
        if 'TOTAL' in line or 'Name' in line or '---' in line:
            print(line)
