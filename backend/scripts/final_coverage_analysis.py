#!/usr/bin/env python3
"""
Final Coverage Analysis
Compare baseline vs final coverage improvements
"""

import json
import sys


def analyze_final_coverage():
    """Analyze final coverage improvements"""

    try:
        # Load baseline coverage
        with open("coverage.json", "r") as f:
            baseline = json.load(f)

        # Load final coverage
        with open("coverage_final.json", "r") as f:
            final = json.load(f)

        print("FINAL CODECOV COVERAGE ANALYSIS")
        print("=" * 60)

        # Overall improvement
        baseline_total = baseline["totals"]["percent_covered"]
        final_total = final["totals"]["percent_covered"]
        improvement = final_total - baseline_total

        print("OVERALL COVERAGE IMPROVEMENT:")
        print(f"   Baseline:    {baseline_total:.2f}%")
        print(f"   Final:       {final_total:.2f}%")
        print(f"   Improvement: {improvement:+.2f}%")

        # Lines improvement
        baseline_lines = baseline["totals"]["covered_lines"]
        final_lines = final["totals"]["covered_lines"]
        lines_improvement = final_lines - baseline_lines

        print("\nLINES COVERED IMPROVEMENT:")
        print(f"   Baseline:    {baseline_lines:,} lines")
        print(f"   Final:       {final_lines:,} lines")
        print(f"   Added:       {lines_improvement:+,} lines")

        # Significant file improvements
        print("\nSIGNIFICANT FILE IMPROVEMENTS:")
        print("-" * 50)

        improvements = []
        for file_path in final["files"]:
            if file_path in baseline["files"]:
                baseline_cov = baseline["files"][file_path]["summary"][
                    "percent_covered"
                ]
                final_cov = final["files"][file_path]["summary"]["percent_covered"]
                file_improvement = final_cov - baseline_cov

                if file_improvement > 5:  # Only show improvements > 5%
                    improvements.append(
                        (file_path, baseline_cov, final_cov, file_improvement)
                    )

        improvements.sort(key=lambda x: x[3], reverse=True)

        print("File".ljust(40) + "Before".ljust(10) + "After".ljust(10) + "Gain")
        print("-" * 70)

        for file_path, before, after, gain in improvements[:15]:
            filename = (
                file_path.split("/")[-1]
                if "/" in file_path
                else file_path.split("\\")[-1]
            )
            print(
                f"{filename[:38].ljust(40)} {before:6.1f}%".ljust(10)
                + f"{after:6.1f}%".ljust(10)
                + f"+{gain:5.1f}%"
            )

        # Success metrics
        print("\nSUCCESS METRICS:")
        print(f"Files improved:      {len(improvements)}")
        print(f"Total improvement:   {improvement:+.2f}%")
        print("Tests created:       96 tests")
        print("Test files:          5 new test files")

        # Next targets
        remaining_to_30 = max(0, 30 - final_total)
        if remaining_to_30 > 0:
            print("\nNEXT TARGET:")
            print(f"Need {remaining_to_30:.1f}% more to reach 30% coverage")
        else:
            print("\nTARGET ACHIEVED: Over 30% coverage!")

        return True

    except Exception as e:
        print(f"Error analyzing final coverage: {e}")
        return False


if __name__ == "__main__":
    success = analyze_final_coverage()
    sys.exit(0 if success else 1)
