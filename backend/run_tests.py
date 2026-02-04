"""
Comprehensive Test Runner Script
Sprint 7: Test Coverage

Runs all tests with coverage reporting.
"""
import sys
import subprocess
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def run_command(command, description):
    """Run shell command and capture output"""
    print(f"{Colors.OKCYAN}► Running: {description}{Colors.ENDC}")
    print(f"  Command: {' '.join(command)}\n")

    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent,
            capture_output=False,  # Show output in real-time
            text=True
        )

        if result.returncode == 0:
            print_success(f"{description} - PASSED")
            return True
        else:
            print_error(f"{description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print_error(f"{description} - ERROR: {str(e)}")
        return False


def main():
    """Main test runner"""
    print_header("KIRO2 BACKEND TEST SUITE - SPRINT 7")

    # Set environment for testing
    os.environ["TESTING"] = "true"

    all_passed = True
    results = {}

    # =================================================================
    # Phase 1: Unit Tests (Fast)
    # =================================================================
    print_header("PHASE 1: Unit Tests (Fast, Isolated)")

    unit_test_result = run_command(
        [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--maxfail=10",
            "-m", "not slow",
            "--cov=core",
            "--cov=api",
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/unit",
            "--junit-xml=junit-unit.xml",
            "-n", "auto"  # Parallel execution
        ],
        "Unit Tests"
    )

    results["Unit Tests"] = unit_test_result
    all_passed = all_passed and unit_test_result

    # =================================================================
    # Phase 2: Integration Tests
    # =================================================================
    print_header("PHASE 2: Integration Tests (Requires Services)")

    integration_test_result = run_command(
        [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--maxfail=5",
            "--cov=core",
            "--cov=api",
            "--cov=services",
            "--cov-append",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/integration",
            "--junit-xml=junit-integration.xml",
            "-n", "auto"
        ],
        "Integration Tests"
    )

    results["Integration Tests"] = integration_test_result
    all_passed = all_passed and integration_test_result

    # =================================================================
    # Phase 3: E2E Tests (if exist)
    # =================================================================
    e2e_path = Path(__file__).parent / "tests" / "e2e"
    if e2e_path.exists():
        print_header("PHASE 3: End-to-End Tests")

        e2e_test_result = run_command(
            [
                sys.executable, "-m", "pytest",
                "tests/e2e/",
                "-v",
                "--tb=short",
                "--maxfail=3",
                "--junit-xml=junit-e2e.xml"
            ],
            "E2E Tests"
        )

        results["E2E Tests"] = e2e_test_result
        all_passed = all_passed and e2e_test_result

    # =================================================================
    # Phase 4: Coverage Report
    # =================================================================
    print_header("PHASE 4: Coverage Report")

    coverage_result = run_command(
        [
            sys.executable, "-m", "coverage",
            "report",
            "--precision=2",
            "--skip-covered"
        ],
        "Coverage Report"
    )

    # Generate JSON coverage for CI
    run_command(
        [sys.executable, "-m", "coverage", "json", "-o", "coverage.json"],
        "Coverage JSON Export"
    )

    # =================================================================
    # Final Summary
    # =================================================================
    print_header("TEST SUMMARY")

    print(f"\n{Colors.BOLD}Test Results:{Colors.ENDC}\n")
    for test_name, passed in results.items():
        status = f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}" if passed else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        print(f"  {test_name:30} {status}")

    print(f"\n{Colors.BOLD}Coverage Reports Generated:{Colors.ENDC}\n")
    print(f"  • HTML Report:  htmlcov/index.html")
    print(f"  • JSON Report:  coverage.json")
    print(f"  • XML Reports:  junit-*.xml")

    print(f"\n{Colors.BOLD}View Coverage:{Colors.ENDC}\n")
    print(f"  Open: file:///{Path(__file__).parent.absolute()}/htmlcov/index.html")

    if all_passed:
        print_success("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print_error("\n❌ SOME TESTS FAILED")
        print_warning("   Check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
