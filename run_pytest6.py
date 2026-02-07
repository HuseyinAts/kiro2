with open(r"c:\Users\husey\kiro2\test_result.txt", "r") as f:
    lines = f.readlines()
# Show lines 10-30 to find root cause
for line in lines[10:35]:
    print(line, end="")
