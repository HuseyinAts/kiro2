import subprocess
result = subprocess.run(
    [r"c:\Users\husey\kiro2\.venv\Scripts\python.exe", "-m", "pytest", "tests/", "-q", "--tb=short", "--co"],
    cwd=r"c:\Users\husey\kiro2\backend",
    capture_output=True, text=True, timeout=120
)
stdout_lines = result.stdout.strip().splitlines()
print(f"Collected tests (last 10 of {len(stdout_lines)} lines):")
for line in stdout_lines[-10:]:
    print(line)
stderr_lines = result.stderr.strip().splitlines()
if stderr_lines:
    print(f"\nStderr last 10 of {len(stderr_lines)} lines:")
    for line in stderr_lines[-10:]:
        print(line)
print(f"\nExit code: {result.returncode}")
