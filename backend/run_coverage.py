#!/usr/bin/env python3
"""
Coverage analysis script for KIRO2 backend.
Generates comprehensive coverage report with module breakdown.
"""
import subprocess
import json
import sys
from pathlib import Path

def run_coverage():
    """Run coverage analysis"""
    backend_dir = Path(__file__).parent

    print("=" * 80)
    print("KIRO2 Backend Coverage Analysis")
    print("=" * 80)
    print()

    # Run pytest with coverage
    print("[1/3] Running pytest with coverage instrumentation...")
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "--source=api,services,core,algorithms,analytics,agents",
        "-m",
        "pytest",
        "tests/",
        "--tb=no",
        "-q",
        "-p",
        "no:capture"
    ]

    result = subprocess.run(cmd, cwd=str(backend_dir), capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    print()
    print("[2/3] Generating coverage report...")

    # Generate report
    cmd_report = [
        sys.executable,
        "-m",
        "coverage",
        "report",
        "--skip-empty"
    ]

    result = subprocess.run(cmd_report, cwd=str(backend_dir), capture_output=True, text=True)
    report = result.stdout
    print(report)

    # Parse and analyze report
    print()
    print("[3/3] Analyzing coverage gaps...")
    print()

    lines = report.split('\n')

    # Find summary line
    summary_line = None
    for line in lines:
        if 'TOTAL' in line:
            summary_line = line
            break

    if summary_line:
        print("SUMMARY:")
        print(f"  {summary_line}")

        # Extract overall percentage
        parts = summary_line.split()
        if len(parts) > 0:
            pct = parts[-1]
            print(f"  Overall Coverage: {pct}")

    # Get JSON coverage data
    print()
    print("Generating JSON coverage report for detailed analysis...")
    cmd_json = [
        sys.executable,
        "-m",
        "coverage",
        "json",
        "-o",
        ".coverage.json"
    ]
    subprocess.run(cmd_json, cwd=str(backend_dir), capture_output=True)

    # Parse JSON
    cov_file = backend_dir / ".coverage.json"
    if cov_file.exists():
        with open(cov_file, 'r') as f:
            cov_data = json.load(f)

        # Sort by coverage percentage
        files = {}
        for file_path, file_data in cov_data.get('files', {}).items():
            summary = file_data.get('summary', {})
            num_statements = summary.get('num_statements', 0)
            covered_lines = summary.get('covered_lines', 0)

            if num_statements > 0:
                pct = (covered_lines / num_statements) * 100
                files[file_path] = {
                    'coverage': pct,
                    'covered': covered_lines,
                    'total': num_statements
                }

        if files:
            # Sort by coverage (lowest first)
            sorted_files = sorted(files.items(), key=lambda x: x[1]['coverage'])

            print()
            print("TOP 10 MODULES WITH LOWEST COVERAGE:")
            print("-" * 80)
            for i, (file_path, data) in enumerate(sorted_files[:10], 1):
                # Clean up path
                clean_path = file_path.replace(str(backend_dir) + '\\', '')
                print(f"{i:2d}. {clean_path:60s} {data['coverage']:6.1f}% ({data['covered']}/{data['total']})")

            print()
            print("TOP 10 MODULES WITH HIGHEST COVERAGE:")
            print("-" * 80)
            for i, (file_path, data) in enumerate(reversed(sorted_files[-10:]), 1):
                clean_path = file_path.replace(str(backend_dir) + '\\', '')
                print(f"{i:2d}. {clean_path:60s} {data['coverage']:6.1f}% ({data['covered']}/{data['total']})")

if __name__ == "__main__":
    run_coverage()
