#!/usr/bin/env python3
"""Count total test cases including parametrized tests"""

import ast
import sys


def count_test_cases(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    total_tests = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Check for parametrize decorator
            param_count = 1
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if (
                        hasattr(decorator.func, "attr")
                        and decorator.func.attr == "parametrize"
                    ):
                        # Get the second argument (the list of parameters)
                        if len(decorator.args) >= 2:
                            params_arg = decorator.args[1]
                            if isinstance(params_arg, ast.List):
                                param_count = len(params_arg.elts)
                            elif isinstance(params_arg, ast.Tuple):
                                param_count = len(params_arg.elts)

            total_tests += param_count
            if param_count > 1:
                print(f"{node.name}: {param_count} test cases")

    return total_tests


if __name__ == "__main__":
    filename = "tests/unit/test_exam_curriculum_models.py"
    total = count_test_cases(filename)
    print(f"\n{'='*60}")
    print(f"TOTAL TEST CASES: {total}")
    print(f"{'='*60}")
