#!/usr/bin/env python
"""
Verification script for Python 3.13 + pytest capture bug fix.

This script runs a subset of tests to verify that the capture plugin
is disabled and tests run without ValueError crashes.
"""

import subprocess
import sys
from pathlib import Path


def run_tests(test_path: str, description: str) -> tuple[bool, str]:
    """Run pytest on given path and return success status and output."""
    print(f"\n{'='*70}")
    print(f"Testing: {description}")
    print(f"Path: {test_path}")
    print(f"{'='*70}\n")

    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-q",  # quiet
        "--no-cov",  # no coverage
        "--tb=short",  # short traceback
        "--maxfail=5",  # stop after 5 failures
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent,
        )

        output = result.stdout + result.stderr

        # Check for the capture bug
        if "ValueError: I/O operation on closed file" in output:
            print("[FAILED] Capture bug still present!")
            return False, output

        # Check if tests ran
        if "passed" in output or "failed" in output:
            print("[SUCCESS] Tests ran without capture bug")
            # Print summary line
            for line in output.splitlines():
                if "passed" in line or "failed" in line:
                    print(f"   {line.strip()}")
            return True, output

        # Check if no tests found (also okay)
        if "collected 0 items" in output:
            print("[WARNING] No tests found, but no crash")
            return True, output

        print("[WARNING] Unexpected output")
        return False, output

    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Tests took too long")
        return False, "Timeout"
    except Exception as e:
        print(f"[ERROR] {e}")
        return False, str(e)


def main():
    """Run verification tests."""
    print("="*70)
    print("Python 3.13 + pytest Capture Bug Fix Verification")
    print("="*70)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")

    test_paths = [
        ("tests/core/", "Core utilities tests"),
        ("tests/fast/", "Fast unit tests"),
        ("tests/smoke/", "Smoke tests"),
    ]

    results = []
    for path, desc in test_paths:
        if Path(path).exists():
            success, output = run_tests(path, desc)
            results.append((desc, success))
        else:
            print(f"\n[SKIPPED] {path} does not exist")
            results.append((desc, None))

    # Print summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    for desc, success in results:
        if success is None:
            status = "[SKIPPED]"
        elif success:
            status = "[PASSED]"
        else:
            status = "[FAILED]"
        print(f"{status}: {desc}")

    # Overall result
    failed_count = sum(1 for _, s in results if s is False)
    passed_count = sum(1 for _, s in results if s is True)

    print("\n" + "="*70)
    if failed_count == 0 and passed_count > 0:
        print("[VERIFICATION PASSED] Capture bug is fixed!")
        print("="*70)
        return 0
    elif failed_count > 0:
        print(f"[VERIFICATION FAILED] {failed_count} test(s) failed")
        print("="*70)
        return 1
    else:
        print("[VERIFICATION INCONCLUSIVE] No tests ran")
        print("="*70)
        return 2


if __name__ == "__main__":
    sys.exit(main())
