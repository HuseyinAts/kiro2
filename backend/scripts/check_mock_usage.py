#!/usr/bin/env python3
"""
Mock Usage Quality Gate
Prevents excessive mock usage in tests
"""
import sys
from pathlib import Path
import re


# Thresholds
MAX_MOCKS_PER_FILE = 5  # Max mocks allowed per test file
MAX_MOCK_PERCENTAGE = 30  # Max % of test files that can use mocks


def count_mocks_in_file(file_path: Path) -> int:
    """Count mock usage in a test file"""
    content = file_path.read_text(encoding="utf-8")

    patterns = [
        r"@patch\(",
        r"@mock\.",
        r"Mock\(",
        r"MagicMock\(",
        r"AsyncMock\(",
        r"from unittest.mock import",
    ]

    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content))

    return count


def check_mock_usage():
    """Check if mock usage is within acceptable limits"""
    tests_dir = Path("tests")

    if not tests_dir.exists():
        print("⚠️  WARNING: tests directory not found")
        return

    # Find all test files
    test_files = list(tests_dir.rglob("test_*.py"))

    if not test_files:
        print("⚠️  WARNING: No test files found")
        return

    # Analyze mock usage
    files_with_mocks = []
    high_mock_files = []
    total_mocks = 0

    for test_file in test_files:
        mock_count = count_mocks_in_file(test_file)

        if mock_count > 0:
            files_with_mocks.append({"file": str(test_file), "mocks": mock_count})
            total_mocks += mock_count

            if mock_count > MAX_MOCKS_PER_FILE:
                high_mock_files.append({"file": str(test_file), "mocks": mock_count})

    # Calculate percentages
    mock_percentage = (len(files_with_mocks) / len(test_files)) * 100

    print("\n🔍 Mock Usage Analysis:")
    print(f"  Total test files: {len(test_files)}")
    print(f"  Files using mocks: {len(files_with_mocks)} ({mock_percentage:.1f}%)")
    print(f"  Total mock instances: {total_mocks}")

    # Check thresholds
    failures = []

    if high_mock_files:
        print(f"\n⚠️  Files exceeding {MAX_MOCKS_PER_FILE} mocks per file:")
        for item in sorted(high_mock_files, key=lambda x: x["mocks"], reverse=True)[
            :10
        ]:
            print(f"    {item['file']}: {item['mocks']} mocks")
        failures.append(f"{len(high_mock_files)} files exceed mock limit")

    if mock_percentage > MAX_MOCK_PERCENTAGE:
        print(
            f"\n⚠️  Mock usage percentage ({mock_percentage:.1f}%) exceeds {MAX_MOCK_PERCENTAGE}%"
        )
        failures.append("Too many files use mocks")

    if failures:
        print("\n❌ MOCK USAGE GATE FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        print(
            "\n💡 Recommendation: Use real dependencies with Testcontainers instead of mocks"
        )
        sys.exit(1)

    print("\n✅ MOCK USAGE GATE PASSED")


if __name__ == "__main__":
    check_mock_usage()
