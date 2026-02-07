#!/usr/bin/env python3
"""
Simple test of the coverage automation system
"""

import json
import sys
from pathlib import Path


def test_coverage_system():
    """Test the basic coverage system functionality"""

    print("Testing Coverage Automation System")
    print("=" * 40)

    # Check if coverage.json exists
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        print("[OK] Coverage data file found")

        try:
            with open(coverage_file, "r") as f:
                data = json.load(f)

            totals = data.get("totals", {})
            coverage_pct = totals.get("percent_covered", 0)
            total_lines = totals.get("num_statements", 0)
            covered_lines = totals.get("covered_lines", 0)

            print(f"[OK] Coverage data parsed successfully")
            print(f"  - Overall Coverage: {coverage_pct:.2f}%")
            print(f"  - Total Lines: {total_lines:,}")
            print(f"  - Covered Lines: {covered_lines:,}")

            # Test status determination
            if coverage_pct >= 80:
                status = "[EXCELLENT]"
            elif coverage_pct >= 50:
                status = "[GOOD]"
            elif coverage_pct >= 30:
                status = "[FAIR]"
            else:
                status = "[CRITICAL]"

            print(f"  - Status: {status}")

        except Exception as e:
            print(f"[ERROR] Error parsing coverage data: {e}")
            return False
    else:
        print("[ERROR] Coverage data file not found")
        return False

    # Check if script files exist
    scripts = [
        "scripts/automated_coverage_reporter.py",
        "scripts/coverage_dashboard.py",
        "scripts/run_coverage_automation.py",
    ]

    for script in scripts:
        if Path(script).exists():
            print(f"[OK] {script} found")
        else:
            print(f"[ERROR] {script} missing")
            return False

    # Check coverage reports directory
    reports_dir = Path("coverage_reports")
    if reports_dir.exists():
        print("[OK] Coverage reports directory found")

        # List recent reports
        md_reports = list(reports_dir.glob("*.md"))
        json_reports = list(reports_dir.glob("*.json"))

        print(f"  - Markdown reports: {len(md_reports)}")
        print(f"  - JSON reports: {len(json_reports)}")
    else:
        print("[ERROR] Coverage reports directory missing")

    print("\n" + "=" * 40)
    print("Coverage System Test Complete")

    return True


if __name__ == "__main__":
    success = test_coverage_system()
    sys.exit(0 if success else 1)
