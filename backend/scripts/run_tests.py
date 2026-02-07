#!/usr/bin/env python
"""
Test runner script for CI/CD pipeline
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n=> {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {description}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main test runner"""
    os.chdir(Path(__file__).parent.parent)

    print("Starting Test Pipeline")
    print("=" * 50)

    # Test stages
    stages = [
        # Unit tests with coverage
        (
            [
                "python",
                "-m",
                "pytest",
                "tests/test_core_config_fixed.py",
                "--cov=core.config",
                "--cov-report=json",
                "--cov-report=term",
                "-v",
            ],
            "Core Config Tests",
        ),
        (
            [
                "python",
                "-m",
                "pytest",
                "tests/test_core_base_service_fixed.py",
                "--cov=core.base_service",
                "--cov-report=json",
                "--cov-report=term",
                "-v",
            ],
            "Core Base Service Tests",
        ),
        (
            [
                "python",
                "-m",
                "pytest",
                "tests/test_core_database_fixed.py",
                "--cov=core.database",
                "--cov-report=json",
                "--cov-report=term",
                "-v",
            ],
            "Core Database Tests",
        ),
        # Integration tests
        (
            ["python", "-m", "pytest", "-m", "integration", "--tb=short", "-x"],
            "Integration Tests",
        ),
        # Coverage report
        (["python", "-m", "coverage", "report", "--show-missing"], "Coverage Report"),
        (["python", "-m", "coverage", "html"], "HTML Coverage Report"),
    ]

    success_count = 0
    total_stages = len(stages)

    for cmd, description in stages:
        if run_command(cmd, description):
            success_count += 1
        else:
            print("\n⚠️  Stage failed, but continuing...")

    print("\n" + "=" * 50)
    print(f"📊 Test Pipeline Results: {success_count}/{total_stages} stages passed")

    if success_count == total_stages:
        print("🎉 All tests passed!")
        return 0
    elif success_count >= total_stages * 0.7:  # 70% success rate
        print("⚠️  Most tests passed, but some issues remain")
        return 1
    else:
        print("❌ Many tests failed, needs attention")
        return 2


if __name__ == "__main__":
    sys.exit(main())
