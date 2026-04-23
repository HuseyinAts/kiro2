"""
Console Reporter
================

Terminal-friendly output with color coding.
Uses rich library for formatting if available.
"""

from __future__ import annotations

import sys
from typing import TextIO

from ..models import GateStatus, PipelineResult

# Try to import rich for better formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleReporter:
    """
    Console reporter for quality gate results.

    Features:
    - Color-coded status indicators
    - Summary table
    - Issue details
    - Action items
    """

    # ANSI color codes (fallback when rich not available)
    COLORS = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "gray": "\033[90m",
        "reset": "\033[0m",
        "bold": "\033[1m",
    }

    STATUS_COLORS = {
        GateStatus.PASS: "green",
        GateStatus.WARNING: "yellow",
        GateStatus.FAIL: "red",
        GateStatus.SKIPPED: "gray",
        GateStatus.TIMEOUT: "red",
        GateStatus.ERROR: "red",
    }

    STATUS_ICONS = {
        GateStatus.PASS: "[PASS]",
        GateStatus.WARNING: "[WARN]",
        GateStatus.FAIL: "[FAIL]",
        GateStatus.SKIPPED: "[SKIP]",
        GateStatus.TIMEOUT: "[TIME]",
        GateStatus.ERROR: "[ERR]",
    }

    def __init__(
        self,
        output: TextIO | None = None,
        use_colors: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize console reporter.

        Args:
            output: Output stream (defaults to stdout)
            use_colors: Whether to use colors
            verbose: Show detailed output
        """
        self.output = output or sys.stdout
        self.use_colors = use_colors and self.output.isatty()
        self.verbose = verbose

        if RICH_AVAILABLE and self.use_colors:
            self._console = Console(file=self.output)
        else:
            self._console = None

    def report(self, result: PipelineResult) -> None:
        """Generate and output the report."""
        if self._console:
            self._report_rich(result)
        else:
            self._report_plain(result)

    def _report_rich(self, result: PipelineResult) -> None:
        """Generate report using rich library."""
        console = self._console

        # Header
        status_style = self._get_rich_style(result.status)
        title = f"Quality Gates Pipeline: {result.status.value.upper()}"
        console.print(Panel(title, style=status_style))

        # Summary table
        table = Table(title="Gate Results")
        table.add_column("Gate", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Message")

        for gate in result.gates:
            status_style = self._get_rich_style(gate.status)
            table.add_row(
                gate.gate_name,
                Text(gate.status.value.upper(), style=status_style),
                f"{gate.score:.1f}/10",
                f"{gate.execution_time_ms:.0f}ms",
                gate.message[:50] + "..." if len(gate.message) > 50 else gate.message,
            )

        console.print(table)

        # Summary stats
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total Score: {result.total_score:.1f}/10")
        console.print(f"  Passed: {result.passed_gates} | Failed: {result.failed_gates} | Skipped: {result.skipped_gates}")
        console.print(f"  Total Time: {result.total_execution_time_ms:.0f}ms")

        # Issues (if verbose or failed)
        if self.verbose or result.status == GateStatus.FAIL:
            self._report_issues_rich(result)

        # Action items
        self._report_actions_rich(result)

    def _report_issues_rich(self, result: PipelineResult) -> None:
        """Report issues using rich."""
        console = self._console
        all_issues = []

        for gate in result.gates:
            for issue in gate.issues[:5]:  # Limit per gate
                all_issues.append((gate.gate_name, issue))

        if all_issues:
            console.print("\n[bold red]Issues Found:[/bold red]")
            for gate_name, issue in all_issues[:20]:  # Limit total
                severity_style = {
                    "critical": "bold red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "blue",
                    "info": "gray",
                }.get(issue.severity.value, "white")

                console.print(
                    f"  [{severity_style}]{issue.severity.value.upper()}[/{severity_style}] "
                    f"[cyan]{gate_name}[/cyan]: {issue.message}"
                )
                if issue.file:
                    console.print(f"    File: {issue.file}:{issue.line or ''}")

    def _report_actions_rich(self, result: PipelineResult) -> None:
        """Report action items using rich."""
        console = self._console
        actions = []

        for gate in result.gates:
            if not gate.passed:
                actions.append(f"Fix {gate.gate_name} gate (score: {gate.score:.1f})")
                for issue in gate.issues[:2]:
                    if issue.suggestion:
                        actions.append(f"  - {issue.suggestion}")

        if actions:
            console.print("\n[bold]Action Items:[/bold]")
            for action in actions[:10]:
                console.print(f"  {action}")

    def _get_rich_style(self, status: GateStatus) -> str:
        """Get rich style for status."""
        return {
            GateStatus.PASS: "green",
            GateStatus.WARNING: "yellow",
            GateStatus.FAIL: "red",
            GateStatus.SKIPPED: "dim",
            GateStatus.TIMEOUT: "red",
            GateStatus.ERROR: "bold red",
        }.get(status, "white")

    def _report_plain(self, result: PipelineResult) -> None:
        """Generate plain text report (no rich)."""
        out = self.output

        # Header
        status_color = self._color(self.STATUS_COLORS.get(result.status, "reset"))
        reset = self._color("reset")
        bold = self._color("bold")

        out.write(f"\n{bold}{'='*60}{reset}\n")
        out.write(f"{bold}Quality Gates Pipeline: {status_color}{result.status.value.upper()}{reset}\n")
        out.write(f"{'='*60}\n\n")

        # Gate results
        out.write(f"{bold}Gate Results:{reset}\n")
        out.write("-" * 60 + "\n")

        for gate in result.gates:
            status_color = self._color(self.STATUS_COLORS.get(gate.status, "reset"))
            icon = self.STATUS_ICONS.get(gate.status, "[???]")

            out.write(
                f"{status_color}{icon}{reset} {gate.gate_name:20} "
                f"Score: {gate.score:.1f}/10  "
                f"Time: {gate.execution_time_ms:.0f}ms\n"
            )
            out.write(f"     {gate.message}\n")

        # Summary
        out.write(f"\n{bold}Summary:{reset}\n")
        out.write(f"  Total Score: {result.total_score:.1f}/10\n")
        out.write(f"  Passed: {result.passed_gates} | Failed: {result.failed_gates} | Skipped: {result.skipped_gates}\n")
        out.write(f"  Total Time: {result.total_execution_time_ms:.0f}ms\n")

        # Issues
        if self.verbose or result.status == GateStatus.FAIL:
            self._report_issues_plain(result)

        out.write("\n")

    def _report_issues_plain(self, result: PipelineResult) -> None:
        """Report issues in plain text."""
        out = self.output
        red = self._color("red")
        reset = self._color("reset")

        out.write(f"\n{red}Issues Found:{reset}\n")

        for gate in result.gates:
            for issue in gate.issues[:5]:
                out.write(f"  [{issue.severity.value.upper()}] {gate.gate_name}: {issue.message}\n")
                if issue.file:
                    out.write(f"    File: {issue.file}:{issue.line or ''}\n")

    def _color(self, color: str) -> str:
        """Get ANSI color code."""
        if not self.use_colors:
            return ""
        return self.COLORS.get(color, "")
