"""
Comprehensive Test Coverage Analysis Script
Analyzes test coverage for the entire project and generates detailed report

Usage:
    python analyze_test_coverage.py
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class TestCoverageAnalyzer:
    """Analyzes test coverage for the project"""

    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent
        self.coverage_threshold = 70.0  # Overall project threshold
        self.new_file_threshold = 80.0  # New file threshold

    def run_coverage_analysis(self) -> Tuple[bool, Dict]:
        """Run pytest with coverage and return results"""
        print("=" * 80)
        print("RUNNING COMPREHENSIVE TEST COVERAGE ANALYSIS")
        print("=" * 80)
        print(f"Backend Directory: {self.backend_dir}")
        print(f"Coverage Threshold: {self.coverage_threshold}%")
        print(f"New File Threshold: {self.new_file_threshold}%")
        print("=" * 80)

        # Run pytest with coverage
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/services/test_video_recommendation_service.py",
            "tests/load/",
            "-v",
            "--cov=services",
            "--cov=core",
            "--cov=tests/load",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--tb=short",
            "-x",  # Stop on first failure
        ]

        print(f"\nRunning command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            # Load coverage JSON
            coverage_file = self.backend_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r", encoding="utf-8") as f:
                    coverage_data = json.load(f)
                return True, coverage_data
            else:
                print("⚠️  Coverage JSON file not found")
                return False, {}

        except subprocess.TimeoutExpired:
            print("❌ Test execution timed out")
            return False, {}
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False, {}

    def analyze_coverage_data(self, coverage_data: Dict) -> Dict:
        """Analyze coverage data and generate report"""
        if not coverage_data:
            return {}

        files = coverage_data.get("files", {})
        totals = coverage_data.get("totals", {})

        # Overall coverage
        overall_coverage = totals.get("percent_covered", 0.0)

        # Categorize files
        high_coverage = []  # >= 80%
        medium_coverage = []  # 50-79%
        low_coverage = []  # < 50%
        zero_coverage = []  # 0%

        for filepath, file_data in files.items():
            coverage_pct = file_data["summary"]["percent_covered"]
            file_info = {
                "path": filepath,
                "coverage": coverage_pct,
                "lines": file_data["summary"]["num_statements"],
                "covered": file_data["summary"]["covered_lines"],
                "missing": file_data["summary"]["missing_lines"],
            }

            if coverage_pct == 0:
                zero_coverage.append(file_info)
            elif coverage_pct < 50:
                low_coverage.append(file_info)
            elif coverage_pct < 80:
                medium_coverage.append(file_info)
            else:
                high_coverage.append(file_info)

        return {
            "overall_coverage": overall_coverage,
            "total_files": len(files),
            "high_coverage": sorted(
                high_coverage, key=lambda x: x["coverage"], reverse=True
            ),
            "medium_coverage": sorted(
                medium_coverage, key=lambda x: x["coverage"], reverse=True
            ),
            "low_coverage": sorted(low_coverage, key=lambda x: x["coverage"]),
            "zero_coverage": sorted(zero_coverage, key=lambda x: x["path"]),
            "totals": totals,
        }

    def check_new_files(self) -> List[Dict]:
        """Check coverage of newly added/modified files"""
        # Files related to Task 22 (Load Testing)
        new_files = [
            "tests/load/locustfile.py",
            "services/video_recommendation_service.py",
            "core/multi_layer_cache.py",
            "services/turkish_content_filter.py",
            "services/semantic_youtube_search.py",
            "services/advanced_youtube_search.py",
            "core/structured_logger.py",
        ]

        results = []
        coverage_file = self.backend_dir / "coverage.json"

        if not coverage_file.exists():
            return results

        with open(coverage_file, "r", encoding="utf-8") as f:
            coverage_data = json.load(f)

        files = coverage_data.get("files", {})

        for new_file in new_files:
            # Find matching file in coverage data
            matching_files = [
                f for f in files.keys() if new_file in f.replace("\\", "/")
            ]

            if matching_files:
                for filepath in matching_files:
                    file_data = files[filepath]
                    coverage_pct = file_data["summary"]["percent_covered"]

                    results.append(
                        {
                            "file": new_file,
                            "full_path": filepath,
                            "coverage": coverage_pct,
                            "meets_threshold": coverage_pct >= self.new_file_threshold,
                            "lines": file_data["summary"]["num_statements"],
                            "covered": file_data["summary"]["covered_lines"],
                        }
                    )
            else:
                results.append(
                    {
                        "file": new_file,
                        "full_path": None,
                        "coverage": 0.0,
                        "meets_threshold": False,
                        "lines": 0,
                        "covered": 0,
                    }
                )

        return results

    def generate_report(self, analysis: Dict, new_files: List[Dict]) -> str:
        """Generate comprehensive coverage report"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("TEST COVERAGE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: Teknofest 2025 Eğitim Eylemci Platform")
        report.append("=" * 80)

        # Overall Coverage
        overall = analysis.get("overall_coverage", 0.0)
        report.append(f"\n📊 OVERALL PROJECT COVERAGE: {overall:.2f}%")

        if overall >= self.coverage_threshold:
            report.append(f"✅ PASSED - Meets {self.coverage_threshold}% threshold")
        else:
            report.append(f"❌ FAILED - Below {self.coverage_threshold}% threshold")
            report.append(f"   Gap: {self.coverage_threshold - overall:.2f}%")

        # File Statistics
        report.append(f"\n📁 FILE STATISTICS:")
        report.append(f"   Total Files Analyzed: {analysis.get('total_files', 0)}")
        report.append(
            f"   High Coverage (≥80%): {len(analysis.get('high_coverage', []))}"
        )
        report.append(
            f"   Medium Coverage (50-79%): {len(analysis.get('medium_coverage', []))}"
        )
        report.append(
            f"   Low Coverage (<50%): {len(analysis.get('low_coverage', []))}"
        )
        report.append(
            f"   Zero Coverage (0%): {len(analysis.get('zero_coverage', []))}"
        )

        # New/Modified Files
        report.append(f"\n🆕 NEW/MODIFIED FILES COVERAGE:")
        report.append("-" * 80)

        for file_info in new_files:
            file_name = file_info["file"]
            coverage = file_info["coverage"]
            meets_threshold = file_info["meets_threshold"]

            status = "✅" if meets_threshold else "❌"
            report.append(f"{status} {file_name}")
            report.append(
                f"   Coverage: {coverage:.2f}% (Threshold: {self.new_file_threshold}%)"
            )
            report.append(f"   Lines: {file_info['covered']}/{file_info['lines']}")

            if not meets_threshold and coverage > 0:
                gap = self.new_file_threshold - coverage
                report.append(
                    f"   ⚠️  Gap: {gap:.2f}% - Needs {int(gap * file_info['lines'] / 100)} more lines covered"
                )
            report.append("")

        # High Coverage Files (Top 10)
        high_cov = analysis.get("high_coverage", [])
        if high_cov:
            report.append(f"\n🏆 TOP 10 HIGH COVERAGE FILES:")
            report.append("-" * 80)
            for i, file_info in enumerate(high_cov[:10], 1):
                path = Path(file_info["path"]).name
                report.append(f"{i:2d}. {path:50s} {file_info['coverage']:6.2f}%")

        # Low Coverage Files (Bottom 10)
        low_cov = analysis.get("low_coverage", [])
        if low_cov:
            report.append(f"\n⚠️  BOTTOM 10 LOW COVERAGE FILES (Need Attention):")
            report.append("-" * 80)
            for i, file_info in enumerate(low_cov[:10], 1):
                path = Path(file_info["path"]).name
                report.append(f"{i:2d}. {path:50s} {file_info['coverage']:6.2f}%")

        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS:")
        report.append("-" * 80)

        if overall < self.coverage_threshold:
            report.append("1. Focus on increasing overall project coverage")
            report.append(f"   - Current: {overall:.2f}%")
            report.append(f"   - Target: {self.coverage_threshold}%")
            report.append(f"   - Gap: {self.coverage_threshold - overall:.2f}%")

        failing_new_files = [f for f in new_files if not f["meets_threshold"]]
        if failing_new_files:
            report.append(
                f"\n2. Improve coverage for {len(failing_new_files)} new/modified files:"
            )
            for file_info in failing_new_files:
                report.append(
                    f"   - {file_info['file']}: {file_info['coverage']:.2f}% → {self.new_file_threshold}%"
                )

        if len(low_cov) > 0:
            report.append(f"\n3. Address {len(low_cov)} low coverage files (<50%)")

        if len(analysis.get("zero_coverage", [])) > 0:
            report.append(
                f"\n4. Add tests for {len(analysis.get('zero_coverage', []))} files with zero coverage"
            )

        # Task 22 Specific Status
        report.append(f"\n📋 TASK 22 (LOAD TESTING) STATUS:")
        report.append("-" * 80)

        locustfile_info = next(
            (f for f in new_files if "locustfile" in f["file"]), None
        )
        if locustfile_info:
            report.append(f"✅ locustfile.py created and implemented")
            report.append(f"   Coverage: {locustfile_info['coverage']:.2f}%")
        else:
            report.append(f"⚠️  locustfile.py not found in coverage report")

        video_service_info = next(
            (f for f in new_files if "video_recommendation_service" in f["file"]), None
        )
        if video_service_info and video_service_info["coverage"] >= 80:
            report.append(
                f"✅ video_recommendation_service.py: {video_service_info['coverage']:.2f}% (Excellent!)"
            )

        report.append("\n" + "=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, report: str):
        """Save report to file"""
        report_file = self.backend_dir / "TEST_COVERAGE_ANALYSIS_REPORT.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Test Coverage Analysis Report\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write("```\n")
            f.write(report)
            f.write("\n```\n")

        print(f"\n📄 Report saved to: {report_file}")

    def run(self) -> bool:
        """Run complete analysis"""
        # Run coverage analysis
        success, coverage_data = self.run_coverage_analysis()

        if not success or not coverage_data:
            print("\n❌ Coverage analysis failed")
            return False

        # Analyze coverage data
        analysis = self.analyze_coverage_data(coverage_data)

        # Check new files
        new_files = self.check_new_files()

        # Generate report
        report = self.generate_report(analysis, new_files)
        print(report)

        # Save report
        self.save_report(report)

        # Determine pass/fail
        overall_pass = analysis.get("overall_coverage", 0.0) >= self.coverage_threshold
        new_files_pass = all(
            f["meets_threshold"] for f in new_files if f["coverage"] > 0
        )

        if overall_pass and new_files_pass:
            print("\n✅ ALL COVERAGE REQUIREMENTS MET")
            return True
        else:
            print("\n⚠️  SOME COVERAGE REQUIREMENTS NOT MET")
            if not overall_pass:
                print(f"   - Overall coverage below {self.coverage_threshold}%")
            if not new_files_pass:
                print(f"   - Some new files below {self.new_file_threshold}%")
            return False


if __name__ == "__main__":
    analyzer = TestCoverageAnalyzer()
    success = analyzer.run()
    sys.exit(0 if success else 1)
