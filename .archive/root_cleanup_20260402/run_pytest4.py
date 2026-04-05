import subprocess, os
outfile = r"c:\Users\husey\kiro2\test_result.txt"
with open(outfile, "w") as f:
    result = subprocess.run(
        [r"c:\Users\husey\kiro2\.venv\Scripts\python.exe", "-m", "pytest", "tests/", "-q", "--tb=no", "-p", "no:cacheprovider"],
        cwd=r"c:\Users\husey\kiro2\backend",
        stdout=f, stderr=subprocess.STDOUT, timeout=240
    )
with open(outfile, "r") as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
for line in lines[-20:]:
    print(line, end="")
print(f"\nExit code: {result.returncode}")
