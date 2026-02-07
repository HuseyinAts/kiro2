#!/usr/bin/env python3
"""
Coverage Comparison Tool
Compares before and after coverage to measure improvement
"""

import json
import sys
from typing import Dict


def load_coverage_data(file_path: str) -> Dict:
    """Load coverage data from JSON file"""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Coverage file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in coverage file: {file_path}")
        return {}


def compare_coverage():
    """Compare before and after coverage data"""

    # Load coverage data
    baseline = load_coverage_data("coverage.json")
    new_coverage = load_coverage_data("coverage_new.json")

    if not baseline or not new_coverage:
        print("Cannot compare coverage - missing data files")
        return False

    print("COVERAGE COMPARISON ANALYSIS")
    print("=" * 60)

    # Overall comparison
    baseline_total = baseline["totals"]["percent_covered"]
    new_total = new_coverage["totals"]["percent_covered"]
    improvement = new_total - baseline_total

    print("OVERALL COVERAGE:")
    print(f"   Baseline:    {baseline_total:.2f}%")
    print(f"   New:         {new_total:.2f}%")
    print(f"   Change:      {improvement:+.2f}%")

    if improvement > 0:
        print("   Status:      IMPROVED")
    elif improvement < 0:
        print("   Status:      DECREASED")
    else:
        print("   Status:      NO CHANGE")

    # Lines comparison
    baseline_lines = baseline["totals"]["covered_lines"]
    new_lines = new_coverage["totals"]["covered_lines"]
    lines_added = new_lines - baseline_lines

    print("\nLINES COVERED:")
    print(f"   Baseline:    {baseline_lines:,} lines")
    print(f"   New:         {new_lines:,} lines")
    print(f"   Added:       {lines_added:+,} lines")

    # File-level improvements
    print("\nFILE-LEVEL IMPROVEMENTS:")
    print("-" * 50)

    file_improvements = []
    for file_path in new_coverage["files"]:
        if file_path in baseline["files"]:
            baseline_file_cov = baseline["files"][file_path]["summary"][
                "percent_covered"
            ]
            new_file_cov = new_coverage["files"][file_path]["summary"][
                "percent_covered"
            ]
            file_improvement = new_file_cov - baseline_file_cov

            if abs(file_improvement) > 0.1:  # Only show meaningful changes
                file_improvements.append(
                    (file_path, baseline_file_cov, new_file_cov, file_improvement)
                )

    # Sort by improvement (largest first)
    file_improvements.sort(key=lambda x: x[3], reverse=True)

    if file_improvements:
        print("File".ljust(40) + "Before".ljust(10) + "After".ljust(10) + "Change")
        print("-" * 70)

        for file_path, before, after, change in file_improvements[:15]:
            filename = (
                file_path.split("/")[-1]
                if "/" in file_path
                else file_path.split("\\")[-1]
            )
            status = "[+]" if change > 0 else "[-]" if change < 0 else "[=]"
            print(
                f"{filename[:38].ljust(40)} {before:6.1f}%".ljust(10)
                + f"{after:6.1f}%".ljust(10)
                + f"{change:+6.1f}% {status}"
            )
    else:
        print("No significant file-level changes detected")

    # New files covered
    new_files = set(new_coverage["files"].keys()) - set(baseline["files"].keys())
    if new_files:
        print(f"\nNEW FILES COVERED ({len(new_files)}):")
        for file_path in sorted(new_files)[:10]:
            filename = (
                file_path.split("/")[-1]
                if "/" in file_path
                else file_path.split("\\")[-1]
            )
            coverage = new_coverage["files"][file_path]["summary"]["percent_covered"]
            print(f"   {filename}: {coverage:.1f}%")

    # Category analysis
    print("\nCATEGORY IMPACT:")
    categories = {
        "services": [],
        "api": [],
        "core": [],
        "agents": [],
        "models": [],
        "tests": [],
    }

    for file_path in new_coverage["files"]:
        if file_path in baseline["files"]:
            baseline_cov = baseline["files"][file_path]["summary"]["percent_covered"]
            new_cov = new_coverage["files"][file_path]["summary"]["percent_covered"]
            improvement = new_cov - baseline_cov

            path_lower = file_path.lower()
            if "services" in path_lower:
                categories["services"].append(improvement)
            elif "api" in path_lower:
                categories["api"].append(improvement)
            elif "core" in path_lower:
                categories["core"].append(improvement)
            elif "agents" in path_lower:
                categories["agents"].append(improvement)
            elif "models" in path_lower:
                categories["models"].append(improvement)
            elif "test" in path_lower:
                categories["tests"].append(improvement)

    for category, improvements in categories.items():
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            total_improvement = sum(improvements)
            status = (
                "[+]"
                if avg_improvement > 0
                else "[-]"
                if avg_improvement < 0
                else "[=]"
            )
            print(
                f"   {category.upper():10} {len(improvements):2d} files, "
                f"avg: {avg_improvement:+5.1f}%, total: {total_improvement:+5.1f}% {status}"
            )

    # Test effectiveness analysis
    print("\nTEST EFFECTIVENESS:")

    # Calculate tests vs coverage ratio
    test_files = [f for f in new_coverage["files"] if "test_" in f.lower()]
    production_files = [f for f in new_coverage["files"] if "test_" not in f.lower()]

    if test_files and production_files:
        test_lines = sum(
            new_coverage["files"][f]["summary"]["num_statements"] for f in test_files
        )
        prod_coverage = sum(
            new_coverage["files"][f]["summary"]["covered_lines"]
            for f in production_files
        )

        print(f"   Test code lines: {test_lines:,}")
        print(f"   Production lines covered: {prod_coverage:,}")
        if test_lines > 0:
            efficiency = prod_coverage / test_lines
            print(
                f"   Test efficiency: {efficiency:.2f} (coverage lines per test line)"
            )

    # Summary and recommendations
    print("\nSUMMARY & RECOMMENDATIONS:")
    print("-" * 40)

    if improvement > 1.0:
        print("Excellent progress! Coverage improved significantly.")
    elif improvement > 0.1:
        print("Good progress! Coverage improved.")
    elif improvement > -0.1:
        print("Minimal change in coverage.")
    else:
        print("Coverage decreased - investigate test issues.")

    # Next steps
    remaining_to_30 = max(0, 30 - new_total)
    remaining_to_50 = max(0, 50 - new_total)

    if remaining_to_30 > 0:
        print(f"Next target: {remaining_to_30:.1f}% more to reach 30% coverage")
    elif remaining_to_50 > 0:
        print(f"Next target: {remaining_to_50:.1f}% more to reach 50% coverage")
    else:
        print("Next target: Maintain high coverage and focus on quality")

    return True


if __name__ == "__main__":
    success = compare_coverage()
    sys.exit(0 if success else 1)
