#!/usr/bin/env python3
"""
Migration Test Runner - REQ-8

CI/CD pipeline icin migration test scripti.
PR'lar merge edilmeden once migration'larin test edilmesini saglar.

Features:
    - Clean database initialization
    - Sequential migration testing
    - Upgrade/downgrade testing
    - PR blocking on failure

Usage:
    python scripts/ci/test_migrations.py
    python scripts/ci/test_migrations.py --revision head
    python scripts/ci/test_migrations.py --skip-downgrade

Exit Codes:
    0: Success - all tests passed
    2: Failure - tests failed (blocks PR)

GitHub Actions Integration:
    - name: Test Migrations
      run: python scripts/ci/test_migrations.py
      if: ${{ failure() }}
      # This will block the PR
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str):
    """Print styled header."""
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}[OK]{RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}[ERROR]{RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}[WARNING]{RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}[INFO]{RESET} {text}")


async def test_migrations(
    revision: str = "head",
    skip_downgrade: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Run migration tests.

    REQ-8.1: PR olusturuldugunda migration testlerini otomatik calistirir.

    Args:
        revision: Target revision (default: head)
        skip_downgrade: Skip downgrade testing
        verbose: Verbose output

    Returns:
        bool: True if all tests passed
    """
    from backend.db.testing.dry_run import DryRunConfig, DryRunTester

    print_header("Migration Test Runner")
    print(f"Revision: {revision}")
    print(f"Skip Downgrade: {skip_downgrade}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load configuration
    config = DryRunConfig.from_env()
    config.cleanup_on_exit = True  # Always cleanup in CI

    print_info(f"Database: {config.db_host}:{config.db_port}/{config.db_name}")
    print()

    success = True
    test_results = []

    try:
        # REQ-8.2: Start from clean database
        print_header("Phase 1: Setup Test Database")
        print_info("Creating test database from production schema...")

        async with DryRunTester(config) as tester:
            print_success(f"Test database created: {tester.test_db_name}")

            # REQ-8.3: Apply all migrations sequentially
            print_header("Phase 2: Test Upgrade Migration")
            print_info(f"Running upgrade to {revision}...")

            upgrade_result = await tester.run_upgrade(revision)

            if upgrade_result.success:
                print_success(f"Upgrade completed in {upgrade_result.duration_seconds:.2f}s")
                if upgrade_result.affected_tables:
                    print_info(f"Affected tables: {', '.join(upgrade_result.affected_tables)}")
                test_results.append(("Upgrade", True, upgrade_result.duration_seconds))
            else:
                print_error(f"Upgrade FAILED: {upgrade_result.error_message}")
                if verbose and upgrade_result.stderr:
                    print(f"\n{RED}STDERR:{RESET}\n{upgrade_result.stderr}")
                test_results.append(("Upgrade", False, upgrade_result.duration_seconds))
                success = False

            # REQ-8.4: Test downgrade
            if not skip_downgrade and success:
                print_header("Phase 3: Test Downgrade Migration")
                print_info("Running downgrade to previous revision...")

                downgrade_result = await tester.run_downgrade("-1")

                if downgrade_result.success:
                    print_success(f"Downgrade completed in {downgrade_result.duration_seconds:.2f}s")
                    test_results.append(("Downgrade", True, downgrade_result.duration_seconds))
                else:
                    print_error(f"Downgrade FAILED: {downgrade_result.error_message}")
                    if verbose and downgrade_result.stderr:
                        print(f"\n{RED}STDERR:{RESET}\n{downgrade_result.stderr}")
                    test_results.append(("Downgrade", False, downgrade_result.duration_seconds))
                    success = False

            # Verify schema integrity
            print_header("Phase 4: Verify Schema Integrity")
            print_info("Checking schema integrity...")

            integrity_ok = await tester.verify_schema_integrity()
            if integrity_ok:
                print_success("Schema integrity verified")
                test_results.append(("Integrity", True, 0.0))
            else:
                print_error("Schema integrity check FAILED")
                test_results.append(("Integrity", False, 0.0))
                success = False

    except Exception as e:
        print_error(f"Test runner failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        success = False

    # Print summary
    print_header("Test Summary")

    total_time = sum(r[2] for r in test_results)
    passed = sum(1 for r in test_results if r[1])
    failed = sum(1 for r in test_results if not r[1])

    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {GREEN}{passed}{RESET}")
    print(f"Failed: {RED}{failed}{RESET}")
    print(f"Duration: {total_time:.2f}s")
    print()

    for name, passed, duration in test_results:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {status} {name} ({duration:.2f}s)")

    print()

    # REQ-8.5 & REQ-8.6: Exit code for CI
    if success:
        print_success("All migration tests passed!")
        return True
    else:
        print_error("Migration tests FAILED - PR should be blocked")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migration Test Runner for CI/CD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_migrations.py                  # Test all migrations
    python test_migrations.py --revision head  # Test to specific revision
    python test_migrations.py --skip-downgrade # Skip downgrade test
    python test_migrations.py --verbose        # Verbose output

Exit Codes:
    0: All tests passed
    2: Tests failed (blocks PR in CI)
        """,
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head)",
    )
    parser.add_argument(
        "--skip-downgrade",
        action="store_true",
        help="Skip downgrade testing",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Load environment
    try:
        from dotenv import load_dotenv

        env_files = [
            project_root / "backend" / ".env",
            project_root / "backend" / ".env.test",
            project_root / ".env",
        ]

        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                if args.verbose:
                    print_info(f"Loaded environment from {env_file}")
                break
    except ImportError:
        print_warning("python-dotenv not installed, using system environment")

    # Run tests
    success = asyncio.run(test_migrations(
        revision=args.revision,
        skip_downgrade=args.skip_downgrade,
        verbose=args.verbose,
    ))

    # Exit with appropriate code
    # REQ-8.5: Test basarisiz olursa PR'i block et
    sys.exit(0 if success else 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test cancelled{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(2)
