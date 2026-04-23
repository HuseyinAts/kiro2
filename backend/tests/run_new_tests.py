#!/usr/bin/env python3
"""
Test runner for newly created KIRO2 test suite.

Runs all new tests with proper reporting and verification.
Following Boris Cherny verification standards.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0
        return success, result.stdout

    except Exception as e:
        print(f"ERROR: {e}")
        return False, str(e)


def main():
    """Run all verification steps."""
    print("\n" + "="*60)
    print("KIRO2 NEW TEST SUITE VERIFICATION")
    print("="*60)

    results = {}

    # Test categories
    test_suites = [
        ("API Route Tests", ["pytest", "tests/unit/api/", "-v", "--tb=short"]),
        ("Database Tests", ["pytest", "tests/db/", "-v", "--tb=short"]),
        ("DevOps Tests", ["pytest", "tests/devops/", "-v", "--tb=short"]),
        ("Functional Tests", ["pytest", "tests/functional/", "-v", "--tb=short"]),
        ("Integration Scenarios", ["pytest", "tests/integration/scenarios/", "-v", "--tb=short"]),
    ]

    # Run each test suite
    for name, cmd in test_suites:
        success, output = run_command(cmd, name)
        results[name] = success

    # Summary
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} test suites passed")

    # Return exit code
    if passed == total:
        print("\n🎉 All test suites passed!")
        return 0
    print(f"\n⚠️  {total - passed} test suite(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
