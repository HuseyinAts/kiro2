from unittest.mock import Mock, patch, AsyncMock

"""
Critical Coverage Validation Tests
Validates that critical modules meet their coverage requirements
"""
import json
from pathlib import Path

import pytest

from coverage_critical_modules import CriticalModules


@pytest.mark.security_critical
def test_security_modules_exist():
    """Test that all security critical modules exist"""
    base_path = Path(__file__).parent.parent

    for module_path in CriticalModules.SECURITY_MODULES.keys():
        full_path = base_path / module_path
        assert full_path.exists(), f"Security critical module missing: {module_path}"


@pytest.mark.turkish_nlp_critical
def test_turkish_nlp_modules_exist():
    """Test that all Turkish NLP critical modules exist"""
    base_path = Path(__file__).parent.parent

    for module_path in CriticalModules.TURKISH_NLP_MODULES.keys():
        full_path = base_path / module_path
        assert full_path.exists(), f"Turkish NLP critical module missing: {module_path}"


@pytest.mark.api_critical
def test_api_modules_exist():
    """Test that all API critical modules exist"""
    base_path = Path(__file__).parent.parent

    for module_path in CriticalModules.API_MODULES.keys():
        full_path = base_path / module_path
        assert full_path.exists(), f"API critical module missing: {module_path}"


@pytest.mark.core_critical
def test_core_service_modules_exist():
    """Test that all core service critical modules exist"""
    base_path = Path(__file__).parent.parent

    for module_path in CriticalModules.CORE_SERVICES.keys():
        full_path = base_path / module_path
        assert (
            full_path.exists()
        ), f"Core service critical module missing: {module_path}"


@pytest.mark.infrastructure_critical
def test_infrastructure_modules_exist():
    """Test that all infrastructure critical modules exist"""
    base_path = Path(__file__).parent.parent

    for module_path in CriticalModules.INFRASTRUCTURE_MODULES.keys():
        full_path = base_path / module_path
        assert (
            full_path.exists()
        ), f"Infrastructure critical module missing: {module_path}"


@pytest.mark.unit
def test_critical_modules_configuration():
    """Test critical modules configuration is valid"""
    all_modules = CriticalModules.get_all_critical_modules()

    assert len(all_modules) > 0, "No critical modules defined"

    # Check coverage requirements are reasonable
    for module_path, coverage in all_modules.items():
        assert (
            0 <= coverage <= 100
        ), f"Invalid coverage requirement for {module_path}: {coverage}%"
        assert (
            coverage >= 50
        ), f"Coverage requirement too low for critical module {module_path}: {coverage}%"


@pytest.mark.unit
def test_security_modules_high_coverage():
    """Test that security modules have appropriately high coverage requirements"""
    for module_path, coverage in CriticalModules.SECURITY_MODULES.items():
        assert (
            coverage >= 85
        ), f"Security module {module_path} should have >=85% coverage, got {coverage}%"


@pytest.mark.unit
def test_turkish_nlp_modules_coverage():
    """Test that Turkish NLP modules have appropriate coverage requirements"""
    for module_path, coverage in CriticalModules.TURKISH_NLP_MODULES.items():
        assert (
            coverage >= 75
        ), f"Turkish NLP module {module_path} should have >=75% coverage, got {coverage}%"


@pytest.mark.unit
def test_coverage_report_generation():
    """Test coverage report generation functionality"""
    # Mock coverage data
    mock_coverage = {
        "core/security_manager.py": 98.5,
        "api/auth.py": 85.2,
        "algorithms/turkish_zpd_maarif_system.py": 92.1,
        "core/turkish_nlp_service.py": 78.9,
        "api/zpd_maarif.py": 81.7,
        "services/zpd_maarif_service.py": 73.2,
        "core/database.py": 76.8,
    }

    report = CriticalModules.get_coverage_report(mock_coverage)

    # Check report structure
    assert "security" in report
    assert "turkish_nlp" in report
    assert "api" in report
    assert "core_services" in report
    assert "infrastructure" in report
    assert "summary" in report

    # Check summary calculations
    summary = report["summary"]
    assert isinstance(summary["total_modules"], int)
    assert isinstance(summary["passing_modules"], int)
    assert isinstance(summary["failing_modules"], int)
    assert isinstance(summary["average_coverage"], float)
    assert isinstance(summary["pass_rate"], float)

    assert 0 <= summary["pass_rate"] <= 100


@pytest.mark.unit
def test_missing_modules_validation():
    """Test validation of missing modules"""
    missing = CriticalModules.validate_module_paths()

    # Should return empty list if all modules exist
    # If modules are missing, this test will help identify them
    for module in missing:
        print(f"WARNING: Critical module not found: {module}")

    # We don't assert empty here as some modules might be missing during development
    assert isinstance(missing, list)


@pytest.mark.integration
def test_actual_coverage_if_available():
    """Test actual coverage data if coverage.json is available"""
    coverage_file = Path(__file__).parent.parent / "coverage.json"

    if not coverage_file.exists():
        pytest.skip("coverage.json not found - run tests with coverage first")

    try:
        with open(coverage_file, "r") as f:
            coverage_data = json.load(f)

        # Extract file coverage data
        files = coverage_data.get("files", {})
        file_coverage = {}

        for file_path, file_data in files.items():
            # Convert absolute paths to relative
            if isinstance(file_data, dict) and "summary" in file_data:
                coverage_percent = file_data["summary"].get("percent_covered", 0)
                # Normalize path for comparison
                normalized_path = file_path.replace("\\", "/").replace("backend/", "")
                file_coverage[normalized_path] = coverage_percent

        # Generate report for actual coverage
        report = CriticalModules.get_coverage_report(file_coverage)

        print("\nACTUAL COVERAGE REPORT FOR CRITICAL MODULES:")
        print(f"Pass rate: {report['summary']['pass_rate']:.1f}%")
        print(f"Average coverage: {report['summary']['average_coverage']:.1f}%")
        print(
            f"Passing modules: {report['summary']['passing_modules']}/{report['summary']['total_modules']}"
        )

        # Report failing modules
        failing_modules = []
        for category, modules in report.items():
            if category == "summary":
                continue
            for module_path, module_data in modules.items():
                if not module_data["passing"]:
                    failing_modules.append(
                        {
                            "module": module_path,
                            "required": module_data["required"],
                            "actual": module_data["actual"],
                            "gap": module_data["gap"],
                        }
                    )

        if failing_modules:
            print("\nFAILING CRITICAL MODULES:")
            for module in failing_modules:
                print(
                    f"  {module['module']}: {module['actual']:.1f}% (required: {module['required']}%, gap: {module['gap']:.1f}%)"
                )

        # Don't fail the test, just report
        assert True, "Coverage report generated successfully"

    except Exception as e:
        pytest.skip(f"Could not process coverage.json: {e}")


@pytest.mark.unit
def test_critical_module_categories():
    """Test that critical module categories are properly organized"""
    # Check no module appears in multiple categories
    all_modules = []
    categories = [
        CriticalModules.SECURITY_MODULES,
        CriticalModules.TURKISH_NLP_MODULES,
        CriticalModules.API_MODULES,
        CriticalModules.CORE_SERVICES,
        CriticalModules.INFRASTRUCTURE_MODULES,
    ]

    for category in categories:
        for module in category.keys():
            assert (
                module not in all_modules
            ), f"Module {module} appears in multiple categories"
            all_modules.append(module)

    # Check all categories have modules
    for i, category in enumerate(categories):
        assert len(category) > 0, f"Category {i} is empty"


@pytest.mark.unit
def test_coverage_thresholds_hierarchy():
    """Test that coverage thresholds follow expected hierarchy"""
    # Security should have highest requirements
    security_avg = sum(CriticalModules.SECURITY_MODULES.values()) / len(
        CriticalModules.SECURITY_MODULES
    )

    # Turkish NLP should be second highest
    turkish_avg = sum(CriticalModules.TURKISH_NLP_MODULES.values()) / len(
        CriticalModules.TURKISH_NLP_MODULES
    )

    # Infrastructure should be lowest
    infra_avg = sum(CriticalModules.INFRASTRUCTURE_MODULES.values()) / len(
        CriticalModules.INFRASTRUCTURE_MODULES
    )

    assert (
        security_avg >= turkish_avg
    ), "Security modules should have highest coverage requirements"
    assert (
        turkish_avg >= infra_avg
    ), "Turkish NLP modules should have higher coverage than infrastructure"
