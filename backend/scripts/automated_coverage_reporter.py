#!/usr/bin/env python3
"""
Automated Test Coverage Reporter
Generates comprehensive coverage reports with trend analysis and actionable insights
"""

import json
import sys
import time
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, asdict
import sqlite3
import xml.etree.ElementTree as ET
from jinja2 import Template

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
    """Coverage metrics data structure"""

    timestamp: str
    total_lines: int
    covered_lines: int
    coverage_percentage: float
    missing_lines: int
    branch_coverage: float
    function_coverage: float
    class_coverage: float
    test_count: int
    test_duration: float
    failed_tests: int
    skipped_tests: int

    @property
    def passed_tests(self) -> int:
        return self.test_count - self.failed_tests - self.skipped_tests


@dataclass
class ModuleCoverage:
    """Individual module coverage"""

    name: str
    statements: int
    missing: int
    coverage: float
    missing_lines: List[str]
    branches: int = 0
    partial_branches: int = 0
    branch_coverage: float = 0.0


@dataclass
class CoverageReport:
    """Complete coverage report"""

    metrics: CoverageMetrics
    modules: List[ModuleCoverage]
    uncovered_modules: List[str]
    critical_gaps: List[str]
    improvement_suggestions: List[str]
    trend_analysis: Dict[str, Any]


class CoverageDatabase:
    """SQLite database for storing coverage history"""

    def __init__(self, db_path: str = "coverage_history.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize coverage history database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_lines INTEGER,
                    covered_lines INTEGER,
                    coverage_percentage REAL,
                    missing_lines INTEGER,
                    branch_coverage REAL,
                    function_coverage REAL,
                    class_coverage REAL,
                    test_count INTEGER,
                    test_duration REAL,
                    failed_tests INTEGER,
                    skipped_tests INTEGER,
                    git_commit TEXT,
                    config_hash TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS module_coverage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    module_name TEXT,
                    statements INTEGER,
                    missing INTEGER,
                    coverage REAL,
                    branches INTEGER,
                    partial_branches INTEGER,
                    branch_coverage REAL,
                    FOREIGN KEY (run_id) REFERENCES coverage_runs (id)
                )
            """
            )

    def save_coverage_run(
        self, metrics: CoverageMetrics, modules: List[ModuleCoverage]
    ) -> int:
        """Save coverage run to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert main metrics
            cursor.execute(
                """
                INSERT INTO coverage_runs (
                    timestamp, total_lines, covered_lines, coverage_percentage,
                    missing_lines, branch_coverage, function_coverage, class_coverage,
                    test_count, test_duration, failed_tests, skipped_tests,
                    git_commit, config_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.timestamp,
                    metrics.total_lines,
                    metrics.covered_lines,
                    metrics.coverage_percentage,
                    metrics.missing_lines,
                    metrics.branch_coverage,
                    metrics.function_coverage,
                    metrics.class_coverage,
                    metrics.test_count,
                    metrics.test_duration,
                    metrics.failed_tests,
                    metrics.skipped_tests,
                    self.get_git_commit(),
                    "default",
                ),
            )

            run_id = cursor.lastrowid

            # Insert module coverage
            for module in modules:
                cursor.execute(
                    """
                    INSERT INTO module_coverage (
                        run_id, module_name, statements, missing, coverage,
                        branches, partial_branches, branch_coverage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        run_id,
                        module.name,
                        module.statements,
                        module.missing,
                        module.coverage,
                        module.branches,
                        module.partial_branches,
                        module.branch_coverage,
                    ),
                )

            return run_id

    def get_coverage_trend(self, days: int = 30) -> List[CoverageMetrics]:
        """Get coverage trend for specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, total_lines, covered_lines, coverage_percentage,
                       missing_lines, branch_coverage, function_coverage, class_coverage,
                       test_count, test_duration, failed_tests, skipped_tests
                FROM coverage_runs 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """,
                (cutoff_date,),
            )

            return [CoverageMetrics(*row) for row in cursor.fetchall()]

    def get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"


class CoverageRunner:
    """Run tests and collect coverage data"""

    def __init__(self, project_root: Path, config_file: str = "pytest.ini"):
        self.project_root = Path(project_root)
        self.config_file = config_file
        self.coverage_dir = self.project_root / "htmlcov"
        self.coverage_json = self.project_root / "coverage.json"

    def run_tests_with_coverage(
        self, test_type: str = "all"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Run tests with coverage collection"""
        logger.info(f"Running {test_type} tests with coverage collection...")

        # Determine test paths and options
        test_paths, test_options = self._get_test_config(test_type)

        # Build pytest command
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *test_paths,
            "--cov=core",
            "--cov=models",
            "--cov=services",
            "--cov=api",
            "--cov=algorithms",
            "--cov-report=json:coverage.json",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term",
            "--tb=short",
            "--durations=10",
            *test_options,
        ]

        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
            )

            duration = time.time() - start_time

            # Parse results
            test_stats = self._parse_pytest_output(result.stdout, result.stderr)
            test_stats["duration"] = duration
            test_stats["success"] = result.returncode == 0
            test_stats["exit_code"] = result.returncode

            return result.returncode == 0, test_stats

        except subprocess.TimeoutExpired:
            logger.error("Test execution timed out")
            return False, {"error": "timeout", "duration": time.time() - start_time}
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return False, {"error": str(e), "duration": time.time() - start_time}

    def _get_test_config(self, test_type: str) -> Tuple[List[str], List[str]]:
        """Get test paths and options based on test type"""
        configs = {
            "fast": (["tests/fast"], ["--maxfail=3"]),
            "integration": (["tests/integration"], ["--maxfail=5", "-x"]),
            "slow": (["tests/slow"], ["--maxfail=2", "-x"]),
            "critical": (["tests/fast", "tests/integration"], ["--maxfail=10"]),
            "all": (["tests"], ["--maxfail=15"]),
        }

        return configs.get(test_type, configs["all"])

    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse pytest output to extract test statistics"""
        stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": [],
        }

        # Parse test results from output
        lines = stdout.split("\n") + stderr.split("\n")

        for line in lines:
            if "failed" in line and "passed" in line:
                # Extract numbers from summary line
                words = line.split()
                for i, word in enumerate(words):
                    if word == "failed":
                        try:
                            stats["failed"] = int(words[i - 1])
                        except (ValueError, IndexError):
                            pass
                    elif word == "passed":
                        try:
                            stats["passed"] = int(words[i - 1])
                        except (ValueError, IndexError):
                            pass
                    elif word == "skipped":
                        try:
                            stats["skipped"] = int(words[i - 1])
                        except (ValueError, IndexError):
                            pass
            elif "warnings summary" in line.lower():
                stats["warnings"].append(line)

        stats["total_tests"] = stats["passed"] + stats["failed"] + stats["skipped"]
        return stats


class CoverageAnalyzer:
    """Analyze coverage data and generate insights"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.coverage_json = self.project_root / "coverage.json"
        self.coverage_xml = self.project_root / "coverage.xml"

    def parse_coverage_data(
        self,
    ) -> Optional[Tuple[CoverageMetrics, List[ModuleCoverage]]]:
        """Parse coverage data from JSON and XML files"""
        if not self.coverage_json.exists():
            logger.error("Coverage JSON file not found")
            return None

        try:
            # Parse JSON coverage data
            with open(self.coverage_json, "r") as f:
                coverage_data = json.load(f)

            # Extract overall metrics
            totals = coverage_data.get("totals", {})

            # Parse XML for additional metrics
            branch_coverage = self._parse_branch_coverage()

            metrics = CoverageMetrics(
                timestamp=datetime.now().isoformat(),
                total_lines=totals.get("num_statements", 0),
                covered_lines=totals.get("covered_lines", 0),
                coverage_percentage=totals.get("percent_covered", 0.0),
                missing_lines=totals.get("missing_lines", 0),
                branch_coverage=branch_coverage,
                function_coverage=0.0,  # Would need additional parsing
                class_coverage=0.0,  # Would need additional parsing
                test_count=0,  # Will be updated from test runner
                test_duration=0.0,  # Will be updated from test runner
                failed_tests=0,  # Will be updated from test runner
                skipped_tests=0,  # Will be updated from test runner
            )

            # Parse module coverage
            modules = []
            files = coverage_data.get("files", {})

            for file_path, file_data in files.items():
                # Convert file path to module name
                module_name = self._file_path_to_module(file_path)

                summary = file_data.get("summary", {})
                modules.append(
                    ModuleCoverage(
                        name=module_name,
                        statements=summary.get("num_statements", 0),
                        missing=summary.get("missing_lines", 0),
                        coverage=summary.get("percent_covered", 0.0),
                        missing_lines=file_data.get("missing_lines", []),
                    )
                )

            return metrics, modules

        except Exception as e:
            logger.error(f"Failed to parse coverage data: {e}")
            return None

    def _parse_branch_coverage(self) -> float:
        """Parse branch coverage from XML file"""
        if not self.coverage_xml.exists():
            return 0.0

        try:
            tree = ET.parse(self.coverage_xml)
            root = tree.getroot()

            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                return float(coverage_elem.get("branch-rate", 0.0)) * 100

        except Exception as e:
            logger.warning(f"Failed to parse branch coverage: {e}")

        return 0.0

    def _file_path_to_module(self, file_path: str) -> str:
        """Convert file path to module name"""
        # Remove file extension and convert path separators
        module_path = file_path.replace(".py", "").replace("/", ".").replace("\\", ".")

        # Remove common prefixes
        for prefix in ["backend.", "src.", "."]:
            if module_path.startswith(prefix):
                module_path = module_path[len(prefix) :]

        return module_path

    def analyze_coverage_gaps(self, modules: List[ModuleCoverage]) -> Dict[str, Any]:
        """Analyze coverage gaps and identify improvement opportunities"""
        analysis = {
            "critical_gaps": [],
            "low_coverage_modules": [],
            "uncovered_modules": [],
            "improvement_suggestions": [],
            "priority_modules": [],
        }

        # Identify critical gaps (important modules with low coverage)
        critical_modules = ["core", "models", "services", "api", "auth", "database"]

        for module in modules:
            if module.coverage < 50 and any(
                crit in module.name for crit in critical_modules
            ):
                analysis["critical_gaps"].append(
                    {
                        "module": module.name,
                        "coverage": module.coverage,
                        "missing_lines": len(module.missing_lines),
                    }
                )

            if module.coverage < 30:
                analysis["low_coverage_modules"].append(module.name)

            if module.coverage == 0:
                analysis["uncovered_modules"].append(module.name)

        # Generate improvement suggestions
        if analysis["critical_gaps"]:
            analysis["improvement_suggestions"].append(
                f"Focus on {len(analysis['critical_gaps'])} critical modules with low coverage"
            )

        if analysis["uncovered_modules"]:
            analysis["improvement_suggestions"].append(
                f"Add basic tests for {len(analysis['uncovered_modules'])} uncovered modules"
            )

        # Prioritize modules for improvement
        sorted_modules = sorted(
            modules,
            key=lambda m: (
                -1 if any(crit in m.name for crit in critical_modules) else 0,
                m.coverage,
            ),
        )

        analysis["priority_modules"] = [
            {"name": m.name, "coverage": m.coverage, "statements": m.statements}
            for m in sorted_modules[:10]
        ]

        return analysis


class ReportGenerator:
    """Generate comprehensive coverage reports"""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(self, report: CoverageReport) -> str:
        """Generate comprehensive coverage report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"coverage_report_{timestamp}.md"

        # Generate markdown report
        markdown_content = self._generate_markdown_report(report)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Generate JSON report for API consumption
        json_file = self.output_dir / f"coverage_report_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"Coverage reports generated: {report_file}")
        return str(report_file)

    def _generate_markdown_report(self, report: CoverageReport) -> str:
        """Generate markdown coverage report"""
        template = Template(
            """
# Test Coverage Report

**Generated:** {{ report.metrics.timestamp }}
**Overall Coverage:** {{ "%.2f"|format(report.metrics.coverage_percentage) }}%

## 📊 Coverage Metrics

| Metric | Value |
|--------|-------|
| Total Lines | {{ report.metrics.total_lines }} |
| Covered Lines | {{ report.metrics.covered_lines }} |
| Missing Lines | {{ report.metrics.missing_lines }} |
| Coverage Percentage | {{ "%.2f"|format(report.metrics.coverage_percentage) }}% |
| Branch Coverage | {{ "%.2f"|format(report.metrics.branch_coverage) }}% |

## 🧪 Test Results

| Metric | Value |
|--------|-------|
| Total Tests | {{ report.metrics.test_count }} |
| Passed Tests | {{ report.metrics.passed_tests }} |
| Failed Tests | {{ report.metrics.failed_tests }} |
| Skipped Tests | {{ report.metrics.skipped_tests }} |
| Test Duration | {{ "%.2f"|format(report.metrics.test_duration) }}s |

## 🎯 Coverage by Module

| Module | Coverage | Statements | Missing |
|--------|----------|------------|---------|
{% for module in report.modules[:20] -%}
| {{ module.name }} | {{ "%.1f"|format(module.coverage) }}% | {{ module.statements }} | {{ module.missing }} |
{% endfor %}

## ⚠️ Critical Coverage Gaps

{% for gap in report.critical_gaps %}
- **{{ gap }}** - Requires immediate attention
{% endfor %}

## 📈 Improvement Suggestions

{% for suggestion in report.improvement_suggestions %}
- {{ suggestion }}
{% endfor %}

## 📉 Low Coverage Modules

{% for module in report.modules if module.coverage < 50 %}
- **{{ module.name }}**: {{ "%.1f"|format(module.coverage) }}% ({{ module.missing }} missing lines)
{% endfor %}

## 🔍 Uncovered Modules

{% for module in report.uncovered_modules %}
- {{ module }}
{% endfor %}

## 📊 Trend Analysis

{% if report.trend_analysis.get('coverage_trend') %}
**Coverage Trend:** {{ report.trend_analysis.coverage_trend }}

**Recent Changes:**
{% for change in report.trend_analysis.get('recent_changes', []) %}
- {{ change }}
{% endfor %}
{% endif %}

---
*Report generated by Automated Coverage Reporter*
        """
        )

        return template.render(report=report)


class CoverageAutomation:
    """Main automation orchestrator"""

    def __init__(self, project_root: str, output_dir: str = "coverage_reports"):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.db = CoverageDatabase(str(self.output_dir / "coverage_history.db"))
        self.runner = CoverageRunner(self.project_root)
        self.analyzer = CoverageAnalyzer(self.project_root)
        self.reporter = ReportGenerator(self.output_dir)

    def run_automated_coverage_analysis(self, test_type: str = "all") -> Optional[str]:
        """Run complete automated coverage analysis"""
        logger.info("Starting automated coverage analysis...")

        try:
            # Step 1: Run tests with coverage
            success, test_stats = self.runner.run_tests_with_coverage(test_type)

            if not success:
                logger.error(f"Tests failed: {test_stats}")
                return None

            # Step 2: Parse coverage data
            coverage_data = self.analyzer.parse_coverage_data()
            if not coverage_data:
                logger.error("Failed to parse coverage data")
                return None

            metrics, modules = coverage_data

            # Update metrics with test statistics
            metrics.test_count = test_stats.get("total_tests", 0)
            metrics.test_duration = test_stats.get("duration", 0.0)
            metrics.failed_tests = test_stats.get("failed", 0)
            metrics.skipped_tests = test_stats.get("skipped", 0)

            # Step 3: Analyze coverage gaps
            gap_analysis = self.analyzer.analyze_coverage_gaps(modules)

            # Step 4: Generate trend analysis
            trend_data = self._generate_trend_analysis()

            # Step 5: Create comprehensive report
            report = CoverageReport(
                metrics=metrics,
                modules=modules,
                uncovered_modules=gap_analysis["uncovered_modules"],
                critical_gaps=gap_analysis["critical_gaps"],
                improvement_suggestions=gap_analysis["improvement_suggestions"],
                trend_analysis=trend_data,
            )

            # Step 6: Save to database and generate reports
            run_id = self.db.save_coverage_run(metrics, modules)
            report_file = self.reporter.generate_comprehensive_report(report)

            logger.info(f"Coverage analysis completed. Report saved: {report_file}")

            # Step 7: Generate summary
            self._print_summary(report)

            return report_file

        except Exception as e:
            logger.error(f"Automated coverage analysis failed: {e}")
            return None

    def _generate_trend_analysis(self) -> Dict[str, Any]:
        """Generate coverage trend analysis"""
        try:
            recent_runs = self.db.get_coverage_trend(days=30)

            if len(recent_runs) < 2:
                return {"message": "Insufficient data for trend analysis"}

            # Calculate trend
            latest = recent_runs[-1]
            previous = recent_runs[-2]

            coverage_change = latest.coverage_percentage - previous.coverage_percentage
            test_change = latest.test_count - previous.test_count

            trend = (
                "improving"
                if coverage_change > 0
                else "declining"
                if coverage_change < 0
                else "stable"
            )

            return {
                "coverage_trend": trend,
                "coverage_change": coverage_change,
                "test_count_change": test_change,
                "recent_changes": [
                    f"Coverage changed by {coverage_change:.2f}%",
                    f"Test count changed by {test_change}",
                    f"Trend: {trend}",
                ],
            }

        except Exception as e:
            logger.warning(f"Failed to generate trend analysis: {e}")
            return {"error": str(e)}

    def _print_summary(self, report: CoverageReport):
        """Print coverage summary to console"""
        print("\n" + "=" * 60)
        print("📊 COVERAGE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Overall Coverage: {report.metrics.coverage_percentage:.2f}%")
        print(f"Total Tests: {report.metrics.test_count}")
        print(f"Test Duration: {report.metrics.test_duration:.2f}s")
        print(f"Critical Gaps: {len(report.critical_gaps)}")
        print(f"Uncovered Modules: {len(report.uncovered_modules)}")

        if report.critical_gaps:
            print("\n⚠️  Critical gaps requiring attention:")
            for gap in report.critical_gaps[:5]:
                print(f"  - {gap}")

        if report.improvement_suggestions:
            print("\n💡 Improvement suggestions:")
            for suggestion in report.improvement_suggestions[:3]:
                print(f"  - {suggestion}")

        print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Automated Test Coverage Reporter")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--output-dir", default="coverage_reports", help="Output directory"
    )
    parser.add_argument(
        "--test-type",
        choices=["fast", "integration", "slow", "critical", "all"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize automation
    automation = CoverageAutomation(args.project_root, args.output_dir)

    # Run analysis
    report_file = automation.run_automated_coverage_analysis(args.test_type)

    if report_file:
        print("\n✅ Coverage analysis completed successfully!")
        print(f"📋 Report saved to: {report_file}")
        sys.exit(0)
    else:
        print("\n❌ Coverage analysis failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
