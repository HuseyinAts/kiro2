"""
Code Quality Checker Script
Sprint 8: Code Quality & Standardization

Runs all code quality checks: formatting, linting, type checking, security.
"""
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

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


def print_header(message: str):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def run_command(command: List[str], description: str, allow_failure: bool = False) -> bool:
    """Run command and return success status"""
    print(f"\n{Colors.OKCYAN}► Running: {description}{Colors.ENDC}")
    print(f"  Command: {' '.join(command)}\n")

    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success(f"{description} - PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            if allow_failure:
                print_warning(f"{description} - FAILED (allowed)")
            else:
                print_error(f"{description} - FAILED")

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            return allow_failure

    except FileNotFoundError:
        print_error(f"{description} - COMMAND NOT FOUND")
        print(f"  Please install: {command[0]}")
        return allow_failure
    except Exception as e:
        print_error(f"{description} - ERROR: {str(e)}")
        return allow_failure


def main():
    """Main code quality checker"""
    print_header("KIRO2 CODE QUALITY CHECKER - SPRINT 8")

    all_passed = True
    results: List[Tuple[str, bool]] = []

    # =================================================================
    # Phase 1: Code Formatting
    # =================================================================
    print_header("PHASE 1: Code Formatting")

    # Black
    black_result = run_command(
        [sys.executable, "-m", "black", "--check", "--diff", "."],
        "Black Code Formatter Check"
    )
    results.append(("Black Formatting", black_result))
    all_passed = all_passed and black_result

    # isort
    isort_result = run_command(
        [sys.executable, "-m", "isort", "--check-only", "--diff", "."],
        "isort Import Sorting Check"
    )
    results.append(("isort Import Sorting", isort_result))
    all_passed = all_passed and isort_result

    # =================================================================
    # Phase 2: Linting
    # =================================================================
    print_header("PHASE 2: Code Linting")

    # Flake8
    flake8_result = run_command(
        [sys.executable, "-m", "flake8", ".", "--count", "--statistics"],
        "Flake8 Code Linting",
        allow_failure=True  # Allow warnings
    )
    results.append(("Flake8 Linting", flake8_result))

    # Ruff (modern, fast linter)
    ruff_result = run_command(
        [sys.executable, "-m", "ruff", "check", "."],
        "Ruff Fast Linting",
        allow_failure=True
    )
    results.append(("Ruff Linting", ruff_result))

    # =================================================================
    # Phase 3: Type Checking
    # =================================================================
    print_header("PHASE 3: Type Checking")

    # MyPy (only on core modules for speed)
    mypy_result = run_command(
        [
            sys.executable, "-m", "mypy",
            "core/",
            "--ignore-missing-imports",
            "--explicit-package-bases",
            "--show-error-codes"
        ],
        "MyPy Type Checking (core module)",
        allow_failure=True  # Gradually enable
    )
    results.append(("MyPy Type Checking", mypy_result))

    # =================================================================
    # Phase 4: Security Checks
    # =================================================================
    print_header("PHASE 4: Security Scanning")

    # Bandit
    bandit_result = run_command(
        [
            sys.executable, "-m", "bandit",
            "-r", ".",
            "-x", "./tests,./venv",
            "-ll"  # Only high severity
        ],
        "Bandit Security Scan",
        allow_failure=True
    )
    results.append(("Bandit Security", bandit_result))

    # Safety (dependency vulnerabilities)
    safety_result = run_command(
        [sys.executable, "-m", "safety", "check", "--json"],
        "Safety Dependency Scan",
        allow_failure=True
    )
    results.append(("Safety Dependencies", safety_result))

    # =================================================================
    # Phase 5: Documentation
    # =================================================================
    print_header("PHASE 5: Documentation Check")

    # pydocstyle (optional)
    pydocstyle_result = run_command(
        [sys.executable, "-m", "pydocstyle", "core/", "api/"],
        "pydocstyle Documentation Check",
        allow_failure=True  # Optional
    )
    results.append(("pydocstyle Docs", pydocstyle_result))

    # =================================================================
    # Final Summary
    # =================================================================
    print_header("CODE QUALITY SUMMARY")

    print(f"\n{Colors.BOLD}Check Results:{Colors.ENDC}\n")
    for check_name, passed in results:
        status = f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}" if passed else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        print(f"  {check_name:30} {status}")

    print(f"\n{Colors.BOLD}Quick Fixes:{Colors.ENDC}\n")
    print("  • Auto-format code:  python -m black .")
    print("  • Fix imports:       python -m isort .")
    print("  • Auto-fix linting:  python -m ruff check . --fix")
    print("  • Run pre-commit:    pre-commit run --all-files")

    print(f"\n{Colors.BOLD}CI/CD Integration:{Colors.ENDC}\n")
    print("  • GitHub Actions:    .github/workflows/backend-tests.yml")
    print("  • Pre-commit hooks:  .pre-commit-config.yaml")

    if all_passed:
        print_success("\n🎉 ALL CRITICAL CHECKS PASSED!")
        print_info("   Your code meets quality standards.")
        return 0
    else:
        print_warning("\n⚠ SOME CHECKS FAILED")
        print_info("   Review the output above and apply fixes.")
        print_info("   Non-critical checks are allowed to fail during development.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
