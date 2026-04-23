import os
import subprocess

env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}
cwd = r"c:\Users\husey\kiro2\backend"
python = r"c:\Users\husey\kiro2\.venv\Scripts\python.exe"

# 1. Pytest count
print("=== PYTEST ===")
r1 = subprocess.run(
    [python, "-m", "pytest", "tests/unit/", "tests/integration/",
     "-p", "no:cacheprovider", "--tb=no", "--maxfail=500", "--no-header"],
    cwd=cwd, env=env, timeout=600,
    capture_output=True, encoding='utf-8', errors='replace')

out = r1.stdout or ''
lines = out.strip().split('\n')
for line in lines:
    line_lower = line.lower()
    if 'passed' in line_lower or 'failed' in line_lower or 'error' in line_lower:
        if '=====' in line:
            print("RESULT:", line.strip())

# Count from output
passed = out.count(' PASSED')
failed = out.count(' FAILED')
errors_count = sum(1 for l in lines if l.strip().startswith('ERROR '))
print(f"Passed: {passed}, Failed: {failed}, Errors: {errors_count}")

# 2. Coverage
print("\n=== COVERAGE ===")
r2 = subprocess.run(
    [python, "-m", "coverage", "run",
     "--source=api,services,core,algorithms,analytics,agents",
     "-m", "pytest", "tests/unit/", "tests/integration/",
     "-p", "no:cacheprovider", "--tb=no", "--maxfail=500"],
    cwd=cwd, env=env, timeout=600,
    capture_output=True, encoding='utf-8', errors='replace')

r3 = subprocess.run(
    [python, "-m", "coverage", "report", "--skip-empty"],
    cwd=cwd, capture_output=True, encoding='utf-8', errors='replace', env=env)

if r3.stdout:
    for line in r3.stdout.strip().split('\n'):
        if 'TOTAL' in line:
            print("COVERAGE:", line.strip())
