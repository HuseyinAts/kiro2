#!/usr/bin/env python
"""
Quick runner for API contract tests.

Usage:
    python tests/run_contract_tests.py
    python tests/run_contract_tests.py --verbose
    python tests/run_contract_tests.py --test=test_openapi_json_available
"""

import sys

import pytest

if __name__ == "__main__":
    # Default args
    args = [
        "tests/test_api_contract.py",
        "-v",
        "-m", "contract",
        "--tb=short",
        "-x",  # Stop on first failure
    ]

    # Add user-provided args
    args.extend(sys.argv[1:])

    # Run tests
    exit_code = pytest.main(args)
    sys.exit(exit_code)
