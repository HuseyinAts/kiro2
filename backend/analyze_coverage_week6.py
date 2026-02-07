"""Analyze Week 6 coverage results"""
import json


def analyze_coverage(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        d = json.load(f)

    files = d.get("files", {})
    totals = d.get("totals", {})

    # Group by module
    modules = {}
    for filepath, data in files.items():
        # Handle both forward slash and backslash
        parts = filepath.replace("\\", "/").split("/")
        if len(parts) > 1:
            module = parts[0]
            if module not in modules:
                modules[module] = {"lines": 0, "covered": 0}
            modules[module]["lines"] += data["summary"]["num_statements"]
            modules[module]["covered"] += data["summary"]["covered_lines"]

    # Calculate percentages and sort
    results = []
    for mod, data in modules.items():
        if data["lines"] > 0:
            pct = (data["covered"] / data["lines"]) * 100
            results.append((mod, pct, data["covered"], data["lines"]))

    results.sort(key=lambda x: x[1])

    # Print results
    print("=" * 70)
    print("WEEK 6 FINAL COVERAGE REPORT")
    print("=" * 70)
    print(f"\nTotal Coverage: {totals['percent_covered']:.2f}%")
    print(f"Lines Covered: {totals['covered_lines']:,} / {totals['num_statements']:,}")
    print(
        f"Branch Coverage: {(totals['covered_branches'] / totals['num_branches'] * 100):.1f}%"
    )
    print(f"Files Analyzed: {len(files)}")

    print("\n" + "=" * 70)
    print("MODULE-LEVEL COVERAGE (sorted by percentage)")
    print("=" * 70)
    print(f"{'Module':<25} {'Coverage':>10}  {'Lines':>15}")
    print("-" * 70)

    for mod, pct, covered, total in results:
        status = "***" if pct < 20 else ""
        print(f"{mod:<25} {pct:>9.1f}%  {covered:>6,}/{total:<6,} {status}")

    # Gap analysis
    print("\n" + "=" * 70)
    print("CRITICAL GAPS (< 20% coverage)")
    print("=" * 70)

    critical = [(m, p, c, t) for m, p, c, t in results if p < 20]
    if critical:
        for mod, pct, covered, total in critical:
            print(
                f"{mod:<25} {pct:>6.1f}% - Need {int((total * 0.3) - covered):,} more lines for 30%"
            )
    else:
        print("No critical gaps!")

    # High performers
    print("\n" + "=" * 70)
    print("HIGH PERFORMERS (>= 30% coverage)")
    print("=" * 70)

    high = [(m, p, c, t) for m, p, c, t in results if p >= 30]
    if high:
        for mod, pct, covered, total in high:
            print(f"{mod:<25} {pct:>6.1f}%")
    else:
        print("None yet - all modules need improvement")


if __name__ == "__main__":
    analyze_coverage("coverage_week6_final.json")
