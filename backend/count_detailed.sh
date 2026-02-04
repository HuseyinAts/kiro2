#!/bin/bash

# Count parametrize decorators
param_decorators=$(grep -c "@pytest.mark.parametrize" tests/unit/test_exam_curriculum_models.py)

# Count parameter tuples (each represents a test case)
param_cases=$(grep -E '@pytest\.mark\.parametrize.*\[' tests/unit/test_exam_curriculum_models.py -A20 | grep -E '^\s*\(' | wc -l)

# Count all test functions
total_funcs=$(grep -cE '^\s+def test_' tests/unit/test_exam_curriculum_models.py)

# Estimate: parametrized tests contribute (param_cases) test cases
# Non-parametrized tests are approximately (total_funcs - param_decorators)
non_param=$((total_funcs - param_decorators))

total=$((param_cases + non_param))

echo "Analysis of test_exam_curriculum_models.py:"
echo "============================================="
echo "Parametrize decorators: $param_decorators"
echo "Parametrized test cases: $param_cases"
echo "Total test functions: $total_funcs"
echo "Non-parametrized tests: $non_param"
echo "============================================="
echo "ESTIMATED TOTAL TEST CASES: $total"
echo "============================================="
