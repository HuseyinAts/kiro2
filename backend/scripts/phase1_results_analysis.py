#!/usr/bin/env python3
"""
Phase 1 Progressive Coverage Results Analysis
"""

import json
import sys


def analyze_phase1_results():
    """Phase 1 sonuçlarını analiz et"""

    try:
        # Baseline coverage
        with open("coverage.json", "r") as f:
            baseline = json.load(f)

        # Phase 1 final coverage
        with open("coverage_phase1_final.json", "r") as f:
            phase1 = json.load(f)

        print("PHASE 1 PROGRESSIVE COVERAGE RESULTS")
        print("=" * 60)

        # Overall comparison
        baseline_total = baseline["totals"]["percent_covered"]
        phase1_total = phase1["totals"]["percent_covered"]
        improvement = phase1_total - baseline_total

        print("OVERALL PROGRESS:")
        print(f"   Baseline:      {baseline_total:.2f}%")
        print(f"   Phase 1:       {phase1_total:.2f}%")
        print(f"   Improvement:   {improvement:+.2f}%")
        print(f"   Target (25%):  {25.0:.1f}%")
        print(f"   Remaining:     {max(0, 25.0 - phase1_total):.1f}%")

        # Phase 1 target assessment
        if phase1_total >= 25.0:
            print("   Status:        PHASE 1 COMPLETED!")
        elif phase1_total >= 20.0:
            print("   Status:        VERY CLOSE TO TARGET")
        elif improvement > 0:
            print("   Status:        GOOD PROGRESS")
        else:
            print("   Status:        NEEDS IMPROVEMENT")

        # Top file improvements
        print("\nTOP FILE IMPROVEMENTS:")
        print("-" * 50)

        improvements = []
        for file_path in phase1["files"]:
            if file_path in baseline["files"]:
                baseline_cov = baseline["files"][file_path]["summary"][
                    "percent_covered"
                ]
                phase1_cov = phase1["files"][file_path]["summary"]["percent_covered"]
                file_improvement = phase1_cov - baseline_cov

                if file_improvement > 10:  # Significant improvements
                    improvements.append(
                        (file_path, baseline_cov, phase1_cov, file_improvement)
                    )

        improvements.sort(key=lambda x: x[3], reverse=True)

        print("File".ljust(40) + "Before".ljust(10) + "After".ljust(10) + "Gain")
        print("-" * 70)

        total_files_improved = 0
        for file_path, before, after, gain in improvements:
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
            total_files_improved += 1

        # Phase 1 strategy effectiveness
        print("\nPHASE 1 STRATEGY EFFECTIVENESS:")
        phase1_priority_files = [
            "berturk_service.py",
            "learning_analytics.py",
            "security_manager.py",
            "content_management_service.py",
            "fast_learning_service.py",
            "revolutionary_features_service.py",
        ]

        priority_improvements = 0
        priority_coverage_sum = 0

        for file_path in phase1["files"]:
            filename = (
                file_path.split("/")[-1]
                if "/" in file_path
                else file_path.split("\\")[-1]
            )
            if filename in phase1_priority_files:
                current_cov = phase1["files"][file_path]["summary"]["percent_covered"]
                baseline_cov = (
                    baseline["files"]
                    .get(file_path, {})
                    .get("summary", {})
                    .get("percent_covered", 0)
                )

                if current_cov > baseline_cov:
                    priority_improvements += 1
                    priority_coverage_sum += current_cov
                    print(
                        f"   [+] {filename}: {baseline_cov:.1f}% -> {current_cov:.1f}%"
                    )

        # Test effectiveness metrics
        print("\nTEST EFFECTIVENESS METRICS:")
        print(
            f"   Priority files improved: {priority_improvements}/{len(phase1_priority_files)}"
        )
        print(f"   Total files improved: {total_files_improved}")
        print(
            f"   Average improvement: {improvement/max(1, total_files_improved):.1f}%"
        )

        # Lines of code impact
        baseline_lines = baseline["totals"]["covered_lines"]
        phase1_lines = phase1["totals"]["covered_lines"]
        lines_added = phase1_lines - baseline_lines

        print("\nLINES OF CODE IMPACT:")
        print(f"   Baseline lines covered: {baseline_lines:,}")
        print(f"   Phase 1 lines covered:  {phase1_lines:,}")
        print(f"   New lines covered:      {lines_added:+,}")

        # Next phase readiness
        print("\nNEXT PHASE READINESS:")
        if phase1_total >= 25.0:
            print("Ready for Phase 2 (Target: 35% coverage)")
            print("Focus areas: Core modules, API endpoints, Database layer")
        else:
            remaining = 25.0 - phase1_total
            print(f"Need {remaining:.1f}% more to complete Phase 1")
            print("Recommendation: Focus on completing current priority files")

        # Success metrics summary
        print("\nPHASE 1 SUCCESS METRICS:")
        print(f"Coverage Improvement: {improvement:+.2f}%")
        print(f"Files Significantly Improved: {total_files_improved}")
        print("Tests Created: ~36 functional tests")
        print(f"High-Impact Modules Targeted: {priority_improvements}")

        return True

    except Exception as e:
        print(f"Error analyzing Phase 1 results: {e}")
        return False


if __name__ == "__main__":
    success = analyze_phase1_results()
    sys.exit(0 if success else 1)
