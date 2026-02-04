"""
SQL Injection Audit Runner Script (Task 51.5)
CLI tool to run SQL injection security audit

Usage:
    python scripts/run_sql_audit.py [--path BACKEND_PATH] [--json]

Author: Claude
Date: 2025-10-27
"""
import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sql_injection_auditor import run_sql_audit


def main():
    parser = argparse.ArgumentParser(
        description="SQL Injection Security Audit Tool (Task 51.5)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="backend",
        help="Path to backend directory to audit (default: backend)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    # Run audit
    report = run_sql_audit(project_root=args.path)

    # Output JSON if requested
    if args.json:
        print(json.dumps(report, indent=2))

    # Exit with error code if critical vulnerabilities found
    if report["critical_count"] > 0:
        sys.exit(1)
    elif report["high_count"] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
