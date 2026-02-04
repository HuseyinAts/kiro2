#!/usr/bin/env python3
"""
Fast Test Runner - Core Module Testing
Optimized for development speed
"""
import subprocess
import time
import sys


def run_fast_tests():
    """Run only fast core tests"""
    print("Running Fast Core Tests...")

    start_time = time.time()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/fast/",
        "-v",
        "--tb=short",
        "--cov=core",
        "--cov-report=term-missing",
        "--maxfail=3",
        "--disable-warnings",
        "--timeout=5",
    ]

    result = subprocess.run(cmd, capture_output=False)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nTest Duration: {duration:.2f} seconds")

    if result.returncode == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")

    return result.returncode


def run_parallel_tests():
    """Run fast tests in parallel"""
    print("Running Fast Tests (Parallel)...")

    start_time = time.time()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/fast/",
        "-n",
        "2",  # 2 workers for small test suite
        "--dist",
        "worksteal",
        "--tb=short",
        "--cov=core",
        "--cov-report=term-missing",
        "--maxfail=3",
        "--disable-warnings",
    ]

    result = subprocess.run(cmd, capture_output=False)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nParallel Test Duration: {duration:.2f} seconds")

    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fast Test Runner")
    parser.add_argument(
        "--parallel", "-p", action="store_true", help="Run tests in parallel"
    )

    args = parser.parse_args()

    if args.parallel:
        exit_code = run_parallel_tests()
    else:
        exit_code = run_fast_tests()

    sys.exit(exit_code)
