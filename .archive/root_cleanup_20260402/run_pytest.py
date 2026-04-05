import subprocess
result = subprocess.run(
    [r"c:\Users\husey\kiro2\.venv\Scripts\python.exe", "-m", "pytest", "tests/", "-q", "--tb=no"],
    cwd=r"c:\Users\husey\kiro2\backend",
    capture_output=True, text=True, timeout=240
)
lines = (result.stdout + result.stderr).strip().splitlines()
for line in lines[-15:]:
    print(line)
print(f"\nExit code: {result.returncode}")
