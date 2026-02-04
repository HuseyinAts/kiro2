#!/usr/bin/env python3
"""
Coverage Quality Gate
Enforces minimum coverage requirements
"""
import json
import sys
from pathlib import Path


# Coverage thresholds by module type
THRESHOLDS = {
    "security": 90,  # Security modules need 90%+
    "core": 70,  # Core modules need 70%+
    "api": 60,  # API modules need 60%+
    "services": 60,  # Services need 60%+
    "models": 80,  # Data models need 80%+
    "default": 50,  # Everything else needs 50%+
}

# Critical security modules (must have 90% coverage)
SECURITY_MODULES = [
    "core/auth_middleware.py",
    "core/auth_security_utils.py",
    "core/security_middleware.py",
    "core/data_encryption.py",
    "core/ddos_protection.py",
    "core/kvkk_compliance.py",
    "core/security_manager.py",
    "core/csrf_protection.py",
]


def get_module_threshold(file_path: str) -> int:
    """Determine coverage threshold based on file path"""
    if any(sec_mod in file_path for sec_mod in SECURITY_MODULES):
        return THRESHOLDS["security"]
    elif file_path.startswith("core/"):
        return THRESHOLDS["core"]
    elif file_path.startswith("api/"):
        return THRESHOLDS["api"]
    elif file_path.startswith("services/"):
        return THRESHOLDS["services"]
    elif file_path.startswith("models/"):
        return THRESHOLDS["models"]
    else:
        return THRESHOLDS["default"]


def check_coverage():
    """Check if coverage meets thresholds"""
    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print("❌ ERROR: coverage.json not found")
        sys.exit(1)

    with open(coverage_file) as f:
        data = json.load(f)

    overall_coverage = data["totals"]["percent_covered"]
    print(f"\n📊 Overall Coverage: {overall_coverage:.2f}%")

    failures = []

    # Check each file
    for file_path, file_data in data["files"].items():
        # Skip test files
        if "test_" in file_path or "/tests/" in file_path:
            continue

        coverage = file_data["summary"]["percent_covered"]
        threshold = get_module_threshold(file_path)

        if coverage < threshold:
            failures.append(
                {
                    "file": file_path,
                    "coverage": coverage,
                    "threshold": threshold,
                    "gap": threshold - coverage,
                }
            )

    # Report failures
    if failures:
        print("\n❌ COVERAGE GATE FAILED - Files below threshold:\n")

        # Sort by gap (worst first)
        failures.sort(key=lambda x: x["gap"], reverse=True)

        for failure in failures[:20]:  # Show top 20
            print(f"  {failure['file']}")
            print(
                f"    Current: {failure['coverage']:.1f}% | Required: {failure['threshold']}% | Gap: {failure['gap']:.1f}%"
            )

        if len(failures) > 20:
            print(f"\n  ... and {len(failures) - 20} more files")

        print(f"\n📉 Total files below threshold: {len(failures)}")
        sys.exit(1)

    print("\n✅ COVERAGE GATE PASSED - All files meet thresholds")

    # Check overall minimum (40%)
    if overall_coverage < 40:
        print(f"\n⚠️  WARNING: Overall coverage ({overall_coverage:.2f}%) is below 40%")
        print("   This is acceptable now, but should improve over time")


if __name__ == "__main__":
    check_coverage()
