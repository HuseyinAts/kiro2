#!/usr/bin/env python3
"""
Code Quality Runner
Comprehensive code quality checks and auto-fixes
"""
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: list, description: str) -> tuple[bool, str]:
    """Run a command and return success status and output"""
    print(f"Running {description}...")

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            encoding="utf-8",
            errors="replace",
        )
        end_time = time.time()

        duration = end_time - start_time
        status = "PASSED" if result.returncode == 0 else "FAILED"

        print(f"  {status} ({duration:.2f}s)")

        if result.returncode != 0 and result.stderr:
            print(f"  Error: {result.stderr.strip()}")

        return result.returncode == 0, result.stdout

    except FileNotFoundError:
        print(f"  FAILED - Tool not found")
        return False, ""


def main():
    """Main quality check runner"""
    print("=" * 60)
    print("Code Quality Analysis")
    print("=" * 60)

    # Define quality checks
    checks = [
        {
            "name": "Ruff Linting",
            "cmd": [sys.executable, "-m", "ruff", "check", "tests/fast/", "core/"],
            "fix_cmd": [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "tests/fast/",
                "core/",
                "--fix",
            ],
        },
        {
            "name": "Black Formatting",
            "cmd": [sys.executable, "-m", "black", "tests/fast/", "core/", "--check"],
            "fix_cmd": [sys.executable, "-m", "black", "tests/fast/", "core/"],
        },
        {
            "name": "Import Sorting",
            "cmd": [
                sys.executable,
                "-m",
                "isort",
                "tests/fast/",
                "core/",
                "--check-only",
            ],
            "fix_cmd": [sys.executable, "-m", "isort", "tests/fast/", "core/"],
        },
        {
            "name": "Type Checking",
            "cmd": [
                sys.executable,
                "-m",
                "mypy",
                "tests/fast/",
                "--ignore-missing-imports",
                "--explicit-package-bases",
            ],
            "fix_cmd": None,  # No auto-fix for mypy
        },
    ]

    # Stats
    passed = 0
    failed = 0

    # Run checks
    for check in checks:
        success, output = run_command(check["cmd"], check["name"])

        if success:
            passed += 1
        else:
            failed += 1

            # Auto-fix if available (non-interactive mode)
            if check.get("fix_cmd"):
                print(f"  Auto-fixing {check['name']}...")
                fix_success, _ = run_command(
                    check["fix_cmd"], f"Fixing {check['name']}"
                )
                if fix_success:
                    print(f"  SUCCESS: {check['name']} fixed!")
                    passed += 1
                    failed -= 1

    # Final report
    print("\n" + "=" * 60)
    print("Quality Report")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Score: {passed}/{len(checks)} ({passed/len(checks)*100:.1f}%)")

    # Additional stats
    if Path("htmlcov/index.html").exists():
        print("Coverage report: htmlcov/index.html")

    return failed == 0


def format_all():
    """Format all code with auto-fixes"""
    print("Auto-formatting all code...")

    commands = [
        (
            [sys.executable, "-m", "ruff", "check", "tests/fast/", "core/", "--fix"],
            "Ruff auto-fix",
        ),
        ([sys.executable, "-m", "black", "tests/fast/", "core/"], "Black formatting"),
        ([sys.executable, "-m", "isort", "tests/fast/", "core/"], "Import sorting"),
    ]

    for cmd, desc in commands:
        run_command(cmd, desc)

    print("Formatting complete!")


def generate_report():
    """Generate comprehensive quality report"""
    print("Generating quality report...")

    # Run tests with coverage
    test_success, _ = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/fast/",
            "--cov=core",
            "--cov-report=html",
        ],
        "Tests with coverage",
    )

    # Run quality checks
    ruff_success, ruff_output = run_command(
        [sys.executable, "-m", "ruff", "check", "tests/fast/", "core/", "--statistics"],
        "Ruff statistics",
    )

    # Count files
    py_files = list(Path("tests/fast").glob("*.py")) + list(Path("core").glob("*.py"))

    print(
        f"""
Code Quality Summary
=====================
Python files: {len(py_files)}
Tests passed: {'Yes' if test_success else 'No'}
Linting: {'Clean' if ruff_success else 'Issues found'}
Coverage report: htmlcov/index.html
    """
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Code Quality Tools")
    parser.add_argument("--fix", action="store_true", help="Auto-fix all issues")
    parser.add_argument("--report", action="store_true", help="Generate quality report")

    args = parser.parse_args()

    if args.fix:
        format_all()
    elif args.report:
        generate_report()
    else:
        success = main()
        sys.exit(0 if success else 1)
