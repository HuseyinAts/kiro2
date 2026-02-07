"""Tests for hooks models."""

from backend.hooks.models import (
    QualityCheckResult,
    HookConfig,
    ExitCode,
    ErrorCategory,
    LintError,
    AggregatedResult,
)


class TestQualityCheckResult:
    """Tests for QualityCheckResult model."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = QualityCheckResult(
            tool="ruff",
            passed=True,
            exit_code=0,
            errors=[],
            warnings=[],
            execution_time=1.5,
            files_checked=10
        )
        assert result.passed is True
        assert result.exit_code == 0
        assert result.to_exit_code() == ExitCode.SUCCESS

    def test_create_error_result(self):
        """Test creating an error result."""
        result = QualityCheckResult(
            tool="mypy",
            passed=False,
            exit_code=2,
            errors=["Type error found"],
            warnings=[],
            execution_time=2.0,
            files_checked=5
        )
        assert result.passed is False
        assert result.exit_code == ExitCode.BLOCKING_ERROR
        assert result.to_exit_code() == ExitCode.BLOCKING_ERROR

    def test_auto_fixed_default(self):
        """Test auto_fixed defaults to 0."""
        result = QualityCheckResult(
            tool="black",
            passed=True,
            execution_time=0.5,
            files_checked=1
        )
        assert result.auto_fixed == 0


class TestHookConfig:
    """Tests for HookConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = HookConfig()
        assert config.enabled is True
        assert config.timeout == 30.0
        assert config.auto_fix is True
        assert config.strict_mode is False
        assert config.check_only is False
        assert config.line_length == 88

    def test_custom_config(self):
        """Test custom configuration."""
        config = HookConfig(
            timeout=60.0,
            strict_mode=True,
            line_length=120
        )
        assert config.timeout == 60.0
        assert config.strict_mode is True
        assert config.line_length == 120


class TestLintError:
    """Tests for LintError model."""

    def test_critical_error(self):
        """Test critical error detection."""
        error = LintError(
            file="test.py",
            line=10,
            column=5,
            code="E501",
            message="Line too long",
            category=ErrorCategory.ERROR
        )
        assert error.is_critical is True

    def test_fatal_error(self):
        """Test fatal error detection."""
        error = LintError(
            file="test.py",
            line=1,
            column=1,
            code="F401",
            message="Unused import",
            category=ErrorCategory.FATAL
        )
        assert error.is_critical is True

    def test_warning_not_critical(self):
        """Test warning is not critical."""
        error = LintError(
            file="test.py",
            line=5,
            column=1,
            code="W291",
            message="Trailing whitespace",
            category=ErrorCategory.WARNING
        )
        assert error.is_critical is False


class TestAggregatedResult:
    """Tests for AggregatedResult model."""

    def test_empty_result(self):
        """Test empty aggregated result."""
        result = AggregatedResult()
        assert result.total_checks == 0
        assert result.all_passed is True
        assert result.exit_code == 0

    def test_add_success_result(self):
        """Test adding a success result."""
        aggregated = AggregatedResult()
        result = QualityCheckResult(
            tool="ruff",
            passed=True,
            exit_code=0,
            execution_time=1.0,
            files_checked=5
        )
        aggregated.add_result(result)

        assert aggregated.total_checks == 1
        assert aggregated.passed_checks == 1
        assert aggregated.failed_checks == 0
        assert aggregated.all_passed is True

    def test_add_failure_result(self):
        """Test adding a failure result."""
        aggregated = AggregatedResult()
        result = QualityCheckResult(
            tool="mypy",
            passed=False,
            exit_code=2,
            errors=["Type error"],
            execution_time=2.0,
            files_checked=3
        )
        aggregated.add_result(result)

        assert aggregated.total_checks == 1
        assert aggregated.passed_checks == 0
        assert aggregated.failed_checks == 1
        assert aggregated.all_passed is False
        assert aggregated.exit_code == ExitCode.BLOCKING_ERROR

    def test_multiple_results(self):
        """Test adding multiple results."""
        aggregated = AggregatedResult()

        # Add success
        aggregated.add_result(QualityCheckResult(
            tool="ruff",
            passed=True,
            exit_code=0,
            execution_time=1.0,
            files_checked=5
        ))

        # Add failure
        aggregated.add_result(QualityCheckResult(
            tool="mypy",
            passed=False,
            exit_code=2,
            errors=["Error 1", "Error 2"],
            execution_time=2.0,
            files_checked=5
        ))

        assert aggregated.total_checks == 2
        assert aggregated.passed_checks == 1
        assert aggregated.failed_checks == 1
        assert aggregated.total_errors == 2
        assert aggregated.total_execution_time == 3.0
        assert aggregated.exit_code == ExitCode.BLOCKING_ERROR
