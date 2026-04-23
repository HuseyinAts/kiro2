#!/usr/bin/env python3
"""
Coverage Automation Runner
Comprehensive script to run automated coverage analysis and reporting
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CoverageAutomationRunner:
    """Main runner for coverage automation"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backend_dir = self.project_root / "backend"
        self.scripts_dir = self.backend_dir / "scripts"
        self.reports_dir = self.backend_dir / "coverage_reports"

        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)

        # Check if we're in the right directory
        if not self.backend_dir.exists():
            raise ValueError(f"Backend directory not found: {self.backend_dir}")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        logger.info("Checking dependencies...")

        required_packages = ["pytest", "pytest-cov", "coverage", "jinja2"]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False

        logger.info("✅ All dependencies are installed")
        return True

    def run_coverage_analysis(
        self, test_type: str = "all", verbose: bool = False
    ) -> str | None:
        """Run automated coverage analysis"""
        logger.info(f"🧪 Starting coverage analysis (test type: {test_type})...")

        # Change to backend directory
        original_cwd = os.getcwd()
        os.chdir(self.backend_dir)

        try:
            # Run the automated coverage reporter
            cmd = [
                sys.executable,
                str(self.scripts_dir / "automated_coverage_reporter.py"),
                "--project-root",
                ".",
                "--output-dir",
                "coverage_reports",
                "--test-type",
                test_type,
            ]

            if verbose:
                cmd.append("--verbose")

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=1800  # 30 minutes
            )

            if result.returncode == 0:
                logger.info("✅ Coverage analysis completed successfully")

                # Find the generated report
                report_files = list(self.reports_dir.glob("coverage_report_*.md"))
                if report_files:
                    latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"📋 Report generated: {latest_report}")
                    return str(latest_report)
                logger.warning("No report file found")
                return None
            logger.error(
                f"❌ Coverage analysis failed (exit code: {result.returncode})"
            )
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return None

        except subprocess.TimeoutExpired:
            logger.error("⏱️ Coverage analysis timed out")
            return None
        except Exception as e:
            logger.error(f"❌ Coverage analysis error: {e}")
            return None
        finally:
            os.chdir(original_cwd)

    def start_dashboard(self, port: int = 5000, auto_open: bool = True) -> bool:
        """Start the coverage dashboard"""
        logger.info(f"🎯 Starting coverage dashboard on port {port}...")

        try:
            # Check if Flask is available
            try:
                import flask
            except ImportError:
                logger.error("Flask not installed. Install with: pip install flask")
                return False

            # Change to backend directory
            original_cwd = os.getcwd()
            os.chdir(self.backend_dir)

            try:
                cmd = [
                    sys.executable,
                    str(self.scripts_dir / "coverage_dashboard.py"),
                    "--db-path",
                    str(self.reports_dir / "coverage_history.db"),
                    "--port",
                    str(port),
                ]

                logger.info(f"Dashboard URL: http://localhost:{port}")

                if auto_open:
                    # Auto-open browser after a short delay
                    import threading

                    threading.Timer(
                        2.0, lambda: webbrowser.open(f"http://localhost:{port}")
                    ).start()

                # Run dashboard (this will block)
                subprocess.run(cmd)
                return True

            finally:
                os.chdir(original_cwd)

        except KeyboardInterrupt:
            logger.info("👋 Dashboard stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            return False

    def generate_quick_report(self) -> dict[str, Any]:
        """Generate a quick coverage summary"""
        logger.info("📊 Generating quick coverage summary...")

        coverage_json = self.backend_dir / "coverage.json"

        if not coverage_json.exists():
            logger.warning("No coverage.json found. Run coverage analysis first.")
            return {}

        try:
            with open(coverage_json) as f:
                coverage_data = json.load(f)

            totals = coverage_data.get("totals", {})

            summary = {
                "timestamp": datetime.now().isoformat(),
                "overall_coverage": totals.get("percent_covered", 0.0),
                "total_lines": totals.get("num_statements", 0),
                "covered_lines": totals.get("covered_lines", 0),
                "missing_lines": totals.get("missing_lines", 0),
                "file_count": len(coverage_data.get("files", {})),
            }

            # Determine coverage status
            coverage_pct = summary["overall_coverage"]
            if coverage_pct >= 80:
                summary["status"] = "🟢 Excellent"
                summary["grade"] = "A"
            elif coverage_pct >= 65:
                summary["status"] = "🟡 Good"
                summary["grade"] = "B"
            elif coverage_pct >= 50:
                summary["status"] = "🟠 Fair"
                summary["grade"] = "C"
            else:
                summary["status"] = "🔴 Critical"
                summary["grade"] = "F"

            return summary

        except Exception as e:
            logger.error(f"Error generating quick report: {e}")
            return {}

    def print_quick_summary(self):
        """Print a quick coverage summary to console"""
        summary = self.generate_quick_report()

        if not summary:
            print("\n❌ No coverage data available")
            print("💡 Run: python scripts/run_coverage_automation.py --analyze")
            return

        print("\n" + "=" * 60)
        print("📊 QUICK COVERAGE SUMMARY")
        print("=" * 60)
        print(f"Status: {summary['status']} (Grade: {summary['grade']})")
        print(f"Overall Coverage: {summary['overall_coverage']:.2f}%")
        print(
            f"Covered Lines: {summary['covered_lines']:,} / {summary['total_lines']:,}"
        )
        print(f"Missing Lines: {summary['missing_lines']:,}")
        print(f"Files Analyzed: {summary['file_count']}")
        print(f"Generated: {summary['timestamp']}")

        # Provide recommendations
        coverage_pct = summary["overall_coverage"]
        print("\n💡 RECOMMENDATIONS:")

        if coverage_pct < 50:
            print("  - 🚨 CRITICAL: Add basic tests for core functionality")
            print("  - 📝 Focus on testing critical business logic")
            print("  - 🎯 Target 50% coverage as immediate goal")
        elif coverage_pct < 65:
            print("  - 📈 Add integration tests for user workflows")
            print("  - 🔍 Test error handling and edge cases")
            print("  - 🎯 Target 65% coverage as next milestone")
        elif coverage_pct < 80:
            print("  - ✨ Add comprehensive unit tests")
            print("  - 🔗 Improve branch coverage")
            print("  - 🎯 Target 80% coverage for production readiness")
        else:
            print("  - 🎉 Excellent coverage! Maintain quality")
            print("  - 🔄 Focus on test maintenance and updates")
            print("  - 📊 Monitor coverage trends")

        print("=" * 60)

    def install_git_hooks(self):
        """Install git hooks for automated coverage checking"""
        logger.info("🔗 Installing git hooks...")

        git_hooks_dir = self.project_root / ".git" / "hooks"

        if not git_hooks_dir.exists():
            logger.error("Git hooks directory not found. Is this a git repository?")
            return False

        # Pre-commit hook
        pre_commit_hook = git_hooks_dir / "pre-commit"

        hook_content = f"""#!/bin/bash
# Automated coverage check pre-commit hook
# Generated by coverage automation system

echo "🧪 Running automated coverage check..."

cd "{self.backend_dir}"
python scripts/run_coverage_automation.py --quick-check

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ Coverage check failed. Commit blocked."
    echo "💡 Fix coverage issues or use --no-verify to skip"
    exit 1
fi

echo "✅ Coverage check passed"
exit 0
"""

        try:
            with open(pre_commit_hook, "w") as f:
                f.write(hook_content)

            # Make executable
            os.chmod(pre_commit_hook, 0o755)

            logger.info("✅ Git pre-commit hook installed")
            logger.info("💡 Use 'git commit --no-verify' to skip coverage check")
            return True

        except Exception as e:
            logger.error(f"Failed to install git hooks: {e}")
            return False

    def run_quick_check(self) -> bool:
        """Run a quick coverage check (for git hooks)"""
        summary = self.generate_quick_report()

        if not summary:
            logger.warning("No coverage data found")
            return False

        coverage_pct = summary["overall_coverage"]
        min_coverage = 30  # Minimum coverage threshold

        if coverage_pct < min_coverage:
            logger.error(f"Coverage {coverage_pct:.1f}% below minimum {min_coverage}%")
            return False

        logger.info(f"Coverage check passed: {coverage_pct:.1f}%")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Coverage Automation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_coverage_automation.py --analyze --test-type fast
  python run_coverage_automation.py --dashboard --port 8080
  python run_coverage_automation.py --summary
  python run_coverage_automation.py --install-hooks
        """,
    )

    parser.add_argument(
        "--analyze", "-a", action="store_true", help="Run coverage analysis"
    )
    parser.add_argument(
        "--dashboard", "-d", action="store_true", help="Start coverage dashboard"
    )
    parser.add_argument(
        "--summary", "-s", action="store_true", help="Show quick coverage summary"
    )
    parser.add_argument(
        "--install-hooks",
        action="store_true",
        help="Install git hooks for coverage checking",
    )
    parser.add_argument(
        "--quick-check",
        action="store_true",
        help="Run quick coverage check (for git hooks)",
    )

    parser.add_argument(
        "--test-type",
        choices=["fast", "integration", "slow", "critical", "all"],
        default="critical",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Dashboard port (default: 5000)"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        runner = CoverageAutomationRunner(args.project_root)

        # Check dependencies first
        if not runner.check_dependencies():
            sys.exit(1)

        success = True

        if args.install_hooks:
            success = runner.install_git_hooks()

        elif args.quick_check:
            success = runner.run_quick_check()

        elif args.analyze:
            report_file = runner.run_coverage_analysis(args.test_type, args.verbose)
            success = report_file is not None

            if success:
                print("\n✅ Coverage analysis completed!")
                print(f"📋 Report: {report_file}")

                # Show quick summary
                runner.print_quick_summary()

        elif args.dashboard:
            success = runner.start_dashboard(args.port)

        elif args.summary:
            runner.print_quick_summary()

        else:
            # Default: show summary and offer options
            print("🎯 Coverage Automation System")
            print("=" * 40)

            runner.print_quick_summary()

            print("\n🛠️  Available Commands:")
            print("  --analyze        Run full coverage analysis")
            print("  --dashboard      Start interactive dashboard")
            print("  --summary        Show this summary")
            print("  --install-hooks  Install git hooks")
            print(
                "\n💡 Example: python run_coverage_automation.py --analyze --test-type fast"
            )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
