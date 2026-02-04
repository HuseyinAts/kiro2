#!/usr/bin/env python3
"""
Coverage Gap Analysis Tool
Identifies priority areas for test coverage improvement
"""

import json
import os
import sys
from pathlib import Path


def analyze_coverage_gaps():
    """Analyze coverage gaps and identify priority areas"""

    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print(" Coverage data not found. Please run:")
        print("python -m pytest --cov=. --cov-report=json")
        return False

    try:
        with open(coverage_file, "r") as f:
            data = json.load(f)

        print("COVERAGE GAP ANALYSIS")
        print("=" * 60)

        # Extract file coverage data
        files_coverage = []
        for file_path, file_data in data["files"].items():
            # Skip test files and system files
            if not any(
                skip in file_path
                for skip in [
                    "test_",
                    "__pycache__",
                    ".pyc",
                    "migrations",
                    "venv",
                    "env",
                ]
            ):
                coverage = file_data["summary"]["percent_covered"]
                lines = file_data["summary"]["num_statements"]
                missing = file_data["summary"]["missing_lines"]
                covered = file_data["summary"]["covered_lines"]
                files_coverage.append((file_path, coverage, lines, missing, covered))

        # Sort by coverage (lowest first)
        files_coverage.sort(key=lambda x: x[1])

        print("TOP 20 LOWEST COVERAGE FILES:")
        print(
            "File".ljust(35)
            + "Coverage".ljust(12)
            + "Lines".ljust(8)
            + "Missing".ljust(8)
            + "Priority"
        )
        print("-" * 75)

        priority_files = []
        for i, (file_path, coverage, lines, missing, covered) in enumerate(
            files_coverage[:20]
        ):
            # Get just filename
            filename = os.path.basename(file_path)

            # Calculate priority score (low coverage + high line count = high priority)
            priority_score = (100 - coverage) * (lines / 100)

            if coverage < 30 and lines > 50:
                priority = "[HIGH]"
            elif coverage < 50 and lines > 30:
                priority = "[MED] "
            else:
                priority = "[LOW] "

            print(
                f"{filename[:32].ljust(35)} {coverage:6.1f}%".ljust(12)
                + f"{lines:5d}".ljust(8)
                + f"{missing:5d}".ljust(8)
                + priority
            )

            if priority.startswith("[HIGH]") or priority.startswith("[MED]"):
                priority_files.append(
                    (file_path, coverage, lines, missing, priority_score)
                )

        # Category analysis
        print(f"\n* CATEGORY BREAKDOWN:")
        categories = {
            "services": [],
            "api": [],
            "core": [],
            "agents": [],
            "models": [],
            "algorithms": [],
            "integrations": [],
            "other": [],
        }

        for file_path, coverage, lines, missing, covered in files_coverage:
            if "services" in file_path.lower():
                categories["services"].append((file_path, coverage, lines, missing))
            elif "api" in file_path.lower():
                categories["api"].append((file_path, coverage, lines, missing))
            elif "core" in file_path.lower():
                categories["core"].append((file_path, coverage, lines, missing))
            elif "agents" in file_path.lower():
                categories["agents"].append((file_path, coverage, lines, missing))
            elif "models" in file_path.lower():
                categories["models"].append((file_path, coverage, lines, missing))
            elif "algorithms" in file_path.lower():
                categories["algorithms"].append((file_path, coverage, lines, missing))
            elif "integrations" in file_path.lower():
                categories["integrations"].append((file_path, coverage, lines, missing))
            else:
                categories["other"].append((file_path, coverage, lines, missing))

        for category, files in categories.items():
            if files:
                avg_coverage = sum(f[1] for f in files) / len(files)
                total_missing = sum(f[3] for f in files)
                total_lines = sum(f[2] for f in files)

                # Category priority
                if avg_coverage < 30:
                    cat_priority = "HIGH"
                elif avg_coverage < 50:
                    cat_priority = "MED"
                else:
                    cat_priority = "LOW"

                print(
                    f"{category.upper():12} {len(files):2d} files, "
                    f"{avg_coverage:5.1f}% avg, {total_missing:4d}/{total_lines:4d} missing, {cat_priority}"
                )

        # Specific recommendations
        print(f"\n* RECOMMENDED TEST PRIORITIES:")
        print("=" * 40)

        # Sort priority files by score
        priority_files.sort(key=lambda x: x[4], reverse=True)

        for i, (file_path, coverage, lines, missing, score) in enumerate(
            priority_files[:10]
        ):
            filename = os.path.basename(file_path)
            potential_gain = (missing * 100) / lines if lines > 0 else 0

            print(f"{i+1:2d}. {filename}")
            print(f"    Current: {coverage:.1f}%, Missing: {missing} lines")
            print(f"    Potential gain: +{potential_gain:.1f}% coverage")
            print(f"    Impact score: {score:.1f}")
            print()

        # Overall statistics
        total_coverage = data["totals"]["percent_covered"]
        total_lines = data["totals"]["num_statements"]
        total_covered = data["totals"]["covered_lines"]
        total_missing = data["totals"]["missing_lines"]

        print(f"* OVERALL STATISTICS:")
        print(f"Current Coverage: {total_coverage:.2f}%")
        print(f"Total Lines: {total_lines:,}")
        print(f"Covered Lines: {total_covered:,}")
        print(f"Missing Lines: {total_missing:,}")

        # Calculate target improvements
        targets = [30, 50, 80]
        for target in targets:
            if total_coverage < target:
                lines_needed = int((target * total_lines / 100) - total_covered)
                print(f"To reach {target}%: Need {lines_needed:,} more lines covered")

        print(f"\n* QUICK WINS (Easy coverage gains):")
        quick_wins = [f for f in files_coverage if 20 <= f[1] <= 40 and f[2] <= 100][:5]

        for file_path, coverage, lines, missing, covered in quick_wins:
            filename = os.path.basename(file_path)
            potential = ((lines - missing) / lines) * 100 if lines > 0 else 0
            gain = potential - coverage
            print(f"  {filename}: {coverage:.1f}% -> {potential:.1f}% (+{gain:.1f}%)")

        return True

    except Exception as e:
        print(f" Error analyzing coverage: {e}")
        return False


if __name__ == "__main__":
    success = analyze_coverage_gaps()
    sys.exit(0 if success else 1)
