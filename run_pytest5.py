with open(r"c:\Users\husey\kiro2\test_result.txt", "r") as f:
    lines = f.readlines()
# Find the summary line (e.g., "X passed, Y failed...")
for i, line in enumerate(lines):
    if 'passed' in line or 'failed' in line or 'error' in line or 'no tests ran' in line:
        print(f"Line {i}: {line.strip()}")
# Also show lines 1-10
print("\n--- First 10 lines ---")
for line in lines[:10]:
    print(line, end="")
