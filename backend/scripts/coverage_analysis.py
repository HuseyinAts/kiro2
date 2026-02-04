#!/usr/bin/env python3
"""
Coverage Gap Analysis Tool for Codecov Integration
"""

import json
import os
import sys
from pathlib import Path


def analyze_coverage():
    """Analyze coverage and identify priority areas for testing"""

    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print("Coverage data not found. Running coverage analysis...")
        os.system("python -m pytest --cov=. --cov-report=json --tb=short")

        if not coverage_file.exists():
            print("Failed to generate coverage data")
            return False

    try:
        with open(coverage_file, "r") as f:
            data = json.load(f)

        print("COVERAGE GAP ANALYSIS")
        print("=" * 60)

        files_coverage = []
        for file_path, file_data in data["files"].items():
            # Skip test and system files
            if not any(
                skip in file_path
                for skip in ["test_", "__pycache__", ".pyc", "migrations", "venv"]
            ):
                coverage = file_data["summary"]["percent_covered"]
                lines = file_data["summary"]["num_statements"]
                missing = file_data["summary"]["missing_lines"]
                files_coverage.append((file_path, coverage, lines, missing))

        # Sort by coverage (lowest first)
        files_coverage.sort(key=lambda x: x[1])

        print("TOP 15 LOWEST COVERAGE FILES:")
        print(
            "File".ljust(40)
            + "Coverage".ljust(12)
            + "Lines".ljust(8)
            + "Missing".ljust(8)
            + "Priority"
        )
        print("-" * 80)

        priority_files = []
        for file_path, coverage, lines, missing in files_coverage[:15]:
            filename = os.path.basename(file_path)

            # Priority based on coverage and file size
            if coverage < 20 and lines > 50:
                priority = "[HIGH]"
            elif coverage < 40 and lines > 30:
                priority = "[MED ]"
            else:
                priority = "[LOW ]"

            print(
                f"{filename[:38].ljust(40)} {coverage:6.1f}%".ljust(12)
                + f"{lines:5d}".ljust(8)
                + f"{missing:5d}".ljust(8)
                + priority
            )

            if priority in ["[HIGH]", "[MED ]"]:
                priority_files.append((file_path, coverage, lines, missing))

        # Category breakdown
        print(f"\nCATEGORY ANALYSIS:")
        categories = {
            "services": [],
            "api": [],
            "core": [],
            "agents": [],
            "models": [],
            "other": [],
        }

        for file_path, coverage, lines, missing in files_coverage:
            path_lower = file_path.lower()
            if "services" in path_lower:
                categories["services"].append((coverage, lines, missing))
            elif "api" in path_lower:
                categories["api"].append((coverage, lines, missing))
            elif "core" in path_lower:
                categories["core"].append((coverage, lines, missing))
            elif "agents" in path_lower:
                categories["agents"].append((coverage, lines, missing))
            elif "models" in path_lower:
                categories["models"].append((coverage, lines, missing))
            else:
                categories["other"].append((coverage, lines, missing))

        for category, files in categories.items():
            if files:
                avg_coverage = sum(f[0] for f in files) / len(files)
                total_missing = sum(f[2] for f in files)
                total_lines = sum(f[1] for f in files)

                priority = (
                    "[HIGH]"
                    if avg_coverage < 30
                    else "[MED ]"
                    if avg_coverage < 50
                    else "[LOW ]"
                )

                print(
                    f"{category.upper():12} {len(files):2d} files, "
                    f"{avg_coverage:5.1f}% avg, {total_missing:4d}/{total_lines:4d} missing {priority}"
                )

        # Overall stats
        total_coverage = data["totals"]["percent_covered"]
        total_lines = data["totals"]["num_statements"]
        total_covered = data["totals"]["covered_lines"]
        total_missing = data["totals"]["missing_lines"]

        print(f"\nOVERALL STATISTICS:")
        print(f"Current Coverage: {total_coverage:.2f}%")
        print(f"Total Lines: {total_lines:,}")
        print(f"Covered Lines: {total_covered:,}")
        print(f"Missing Lines: {total_missing:,}")

        # Coverage targets
        targets = [30, 50, 80]
        for target in targets:
            if total_coverage < target:
                lines_needed = int((target * total_lines / 100) - total_covered)
                print(f"To reach {target}%: Need {lines_needed:,} more lines covered")

        # Quick wins identification
        print(f"\nQUICK WINS (High impact, low effort):")
        quick_wins = []
        for file_path, coverage, lines, missing in files_coverage:
            if 10 <= coverage <= 50 and lines <= 200 and missing > 10:
                filename = os.path.basename(file_path)
                potential_gain = (missing / total_lines) * 100
                quick_wins.append((filename, coverage, missing, potential_gain))

        quick_wins.sort(key=lambda x: x[3], reverse=True)  # Sort by potential gain

        for filename, coverage, missing, gain in quick_wins[:8]:
            print(
                f"  {filename}: {coverage:.1f}% -> +{missing} lines = +{gain:.2f}% total gain"
            )

        return True, priority_files

    except Exception as e:
        print(f"Error analyzing coverage: {e}")
        return False, []


if __name__ == "__main__":
    success, priority_files = analyze_coverage()
    if success:
        print(f"\nIdentified {len(priority_files)} priority files for testing")
    sys.exit(0 if success else 1)
