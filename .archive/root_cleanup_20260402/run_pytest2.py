import subprocess
result = subprocess.run(
    [r"c:\Users\husey\kiro2\.venv\Scripts\python.exe", "-m", "pytest", "tests/", "-q", "--tb=no"],
    cwd=r"c:\Users\husey\kiro2\backend",
    capture_output=True, text=True, timeout=240
)
stdout_lines = result.stdout.strip().splitlines()
print("=== STDOUT last 15 lines ===")
for line in stdout_lines[-15:]:
    print(line)
print(f"\nTotal stdout lines: {len(stdout_lines)}")
print(f"Exit code: {result.returncode}")
