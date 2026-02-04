import re

with open("tests/unit/test_exam_curriculum_models.py", "r") as f:
    content = f.read()

# Find all parametrize decorators with their test counts
parametrize_pattern = r"@pytest\.mark\.parametrize\([^)]+\[([^\]]+)\]"
matches = re.findall(parametrize_pattern, content, re.DOTALL)

total_param_cases = 0
for match in matches:
    # Count tuples (lines starting with '(' after whitespace)
    tuples = re.findall(r"^\s*\(", match, re.MULTILINE)
    count = len(tuples)
    total_param_cases += count

# Count test functions
test_funcs = len(re.findall(r"^\s+def test_", content, re.MULTILINE))

# Count parametrize decorators
param_decorators = len(re.findall(r"@pytest\.mark\.parametrize", content))

# Non-parametrized tests
non_param = test_funcs - param_decorators

total = total_param_cases + non_param

print(f"Parametrize decorators: {param_decorators}")
print(f"Parametrized test cases: {total_param_cases}")
print(f"Non-parametrized tests: {non_param}")
print(f"TOTAL TEST CASES: {total}")
