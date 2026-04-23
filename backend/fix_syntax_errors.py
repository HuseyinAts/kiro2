#!/usr/bin/env python3
"""
Fix syntax errors in test files caused by pytestmark inserted inside try/except blocks.

The problem:
```python
try:
    from tests.conftest import ...
except ImportError:
    import jwt as _jwt

pytestmark = pytest.mark.skipif(...)  # ← BREAKS THE except BLOCK!

    TEST_JWT_SECRET = "..."  # ← Now indented but not in a block = IndentationError
```

The fix: Remove the pytestmark block and properly indent the except block content.
"""

import os
import re

FILES_TO_FIX = [
    "tests/test_adhd_task_management_api.py",
    "tests/slow/test_revolutionary_api_integration.py",
    "tests/slow/test_revolutionary_features.py",
    "tests/slow/test_websocket_realtime_comprehensive.py",
    "tests/slow/test_learning_style_service_comprehensive.py",
]


def fix_file(filepath):
    """Fix syntax error in a single file."""
    abs_path = os.path.join(os.getcwd(), filepath)

    if not os.path.exists(abs_path):
        print(f"  [SKIP] File not found: {filepath}")
        return False

    try:
        with open(abs_path, encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Pattern 1: pytestmark inside except block (most common)
        # Look for: except ImportError:\n    import jwt\n\npytestmark = ...\n\n    TEST_JWT_SECRET
        pattern1 = re.compile(
            r'(except ImportError:\n    import jwt as _jwt)\n\n'
            r'pytestmark = pytest\.mark\.skipif\(\n    True,\n    reason="[^"]+",\n\)\n\n\n'
            r'(    TEST_JWT_SECRET = )',
            re.MULTILINE
        )

        new_content = pattern1.sub(r'\1\n\2', content)

        if new_content != content:
            with open(abs_path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_content)
            print(f"  [OK] Fixed: {filepath}")
            return True
        print(f"  [SKIP] No pattern matched: {filepath}")
        return False

    except Exception as e:
        print(f"  [ERROR] Error processing {filepath}: {e}")
        return False


def main():
    print("=" * 80)
    print("Syntax Error Fix Script")
    print("=" * 80)
    print(f"\nWorking directory: {os.getcwd()}")
    print(f"Files to process: {len(FILES_TO_FIX)}\n")

    fixed_count = 0
    for filepath in FILES_TO_FIX:
        if fix_file(filepath):
            fixed_count += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"[OK] Fixed: {fixed_count}/{len(FILES_TO_FIX)}")
    print("=" * 80)

    return 0 if fixed_count == len(FILES_TO_FIX) else 1


if __name__ == "__main__":
    exit(main())
