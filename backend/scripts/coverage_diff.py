#!/usr/bin/env python3
"""
Coverage Diff Quality Gate
Fails if coverage decreases in PR
"""
import json
import sys
import subprocess
from pathlib import Path


def get_base_coverage():
    """Get coverage from base branch"""
    try:
        # Get base branch (main/master)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD@{upstream}"],
            capture_output=True,
            text=True,
        )
        base_branch = result.stdout.strip() or "main"

        # Checkout base branch coverage
        subprocess.run(
            ["git", "show", f"{base_branch}:coverage.json"],
            capture_output=True,
            text=True,
            check=True,
        )

        coverage_json = subprocess.run(
            ["git", "show", f"{base_branch}:coverage.json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        data = json.loads(coverage_json)
        return data["totals"]["percent_covered"]

    except Exception as e:
        print(f"⚠️  Could not get base coverage: {e}")
        return None


def check_coverage_diff():
    """Check if coverage decreased"""
    current_file = Path("coverage.json")

    if not current_file.exists():
        print("❌ ERROR: coverage.json not found")
        sys.exit(1)

    with open(current_file) as f:
        current_data = json.load(f)

    current_coverage = current_data["totals"]["percent_covered"]
    base_coverage = get_base_coverage()

    print(f"\n📊 Coverage Comparison:")
    print(f"  Current: {current_coverage:.2f}%")

    if base_coverage is not None:
        print(f"  Base: {base_coverage:.2f}%")
        diff = current_coverage - base_coverage

        if diff < 0:
            print(f"\n❌ COVERAGE DECREASED by {abs(diff):.2f}%")
            print("   Coverage must not decrease in PRs")
            sys.exit(1)
        elif diff > 0:
            print(f"\n✅ Coverage INCREASED by {diff:.2f}% 🎉")
        else:
            print("\n✅ Coverage unchanged")
    else:
        print("  Base: Not available (first run)")
        print("\n✅ Coverage check passed (no baseline)")


if __name__ == "__main__":
    check_coverage_diff()
