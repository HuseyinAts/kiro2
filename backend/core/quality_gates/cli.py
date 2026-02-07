"""
Quality Gates CLI
=================

Command-line interface for running quality gates pipeline.

Usage:
    python -m core.quality_gates.cli run --all
    python -m core.quality_gates.cli run --gate code_quality
    python -m core.quality_gates.cli report --format html
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .orchestrator import QualityGatesOrchestrator, run_quality_gates
from .models import PipelineConfig, GateStatus
from .reporters import ConsoleReporter, JsonReporter, HtmlReporter


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="quality-gates",
        description="KIRO2 Quality Gates Pipeline",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run quality gates")
    run_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all gates",
    )
    run_parser.add_argument(
        "--gate", "-g",
        type=str,
        help="Run specific gate",
    )
    run_parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        default=True,
        help="Enable parallel execution",
    )
    run_parser.add_argument(
        "--fail-fast", "-f",
        action="store_true",
        help="Stop on first blocking failure",
    )
    run_parser.add_argument(
        "--format",
        choices=["console", "json", "html"],
        default="console",
        help="Output format",
    )
    run_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path",
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    run_parser.add_argument(
        "--dir", "-d",
        type=str,
        default=".",
        help="Working directory",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show gate status")
    status_parser.add_argument(
        "--dir", "-d",
        type=str,
        default=".",
        help="Working directory",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available gates")

    args = parser.parse_args()

    if args.command == "run":
        return run_command(args)
    elif args.command == "status":
        return status_command(args)
    elif args.command == "list":
        return list_command(args)
    else:
        parser.print_help()
        return 0


def run_command(args: argparse.Namespace) -> int:
    """Execute run command."""
    working_dir = Path(args.dir).resolve()

    if not working_dir.exists():
        print(f"Error: Directory '{working_dir}' does not exist")
        return 1

    # Configure pipeline
    config = PipelineConfig(
        parallel_execution=args.parallel,
        fail_fast=args.fail_fast,
    )

    # Run pipeline
    print(f"Running quality gates in {working_dir}...")
    result = asyncio.run(run_quality_gates(working_dir, config))

    # Generate report
    if args.format == "console":
        reporter = ConsoleReporter(verbose=args.verbose)
        reporter.report(result)
    elif args.format == "json":
        output_path = Path(args.output) if args.output else None
        reporter = JsonReporter(output_path=output_path)
        json_output = reporter.report(result)
        if not args.output:
            print(json_output)
    elif args.format == "html":
        output_path = Path(args.output) if args.output else Path("quality-gates-report.html")
        reporter = HtmlReporter(output_path=output_path)
        reporter.report(result)
        print(f"HTML report saved to {output_path}")

    # Return exit code based on result
    if result.status == GateStatus.PASS:
        return 0
    elif result.status == GateStatus.WARNING:
        return 0  # Warning is not a failure
    else:
        return 1


def status_command(args: argparse.Namespace) -> int:
    """Show current gate configuration status."""
    working_dir = Path(args.dir).resolve()

    orchestrator = QualityGatesOrchestrator(working_dir)

    print("\nQuality Gates Status")
    print("=" * 50)

    for name, gate in orchestrator._gates.items():
        status = "enabled" if gate.config.enabled else "disabled"
        blocking = "blocking" if gate.config.blocking else "advisory"
        deps = ", ".join(gate.get_dependencies()) or "none"

        print(f"\n{name}:")
        print(f"  Status: {status} | {blocking}")
        print(f"  Threshold: {gate.config.threshold}/10")
        print(f"  Timeout: {gate.config.timeout_seconds}s")
        print(f"  Dependencies: {deps}")

    return 0


def list_command(args: argparse.Namespace) -> int:
    """List available gates."""
    gates = [
        ("code_quality", "Lint, type check, complexity"),
        ("test_coverage", "Line, branch, function coverage"),
        ("security", "Bandit, safety, secrets"),
        ("performance", "Locust, memory, N+1"),
        ("architecture", "Imports, coupling, layers"),
        ("documentation", "README, API docs, docstrings"),
        ("compliance", "GDPR, KVKK, audit logs"),
    ]

    print("\nAvailable Quality Gates")
    print("=" * 50)

    for name, description in gates:
        print(f"  {name:20} - {description}")

    print("\nUse 'quality-gates run --all' to run all gates")
    print("Use 'quality-gates run --gate <name>' to run specific gate")

    return 0


if __name__ == "__main__":
    sys.exit(main())
