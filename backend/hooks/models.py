"""
Pydantic models for Code Quality Hooks System.

Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ExitCode(int, Enum):
    """Exit codes for hook execution."""
    SUCCESS = 0
    BLOCKING_ERROR = 2  # Feeds back to Claude


class ErrorCategory(str, Enum):
    """Error categories for Ruff linting."""
    ERROR = "E"      # Error
    WARNING = "W"    # Warning
    FATAL = "F"      # Fatal
    INFO = "I"       # Info


class QualityCheckResult(BaseModel):
    """Result of a single quality check hook execution."""

    tool: str = Field(..., description="Tool name (ruff, mypy, pytest, etc.)")
    passed: bool = Field(..., description="Whether the check passed")
    exit_code: int = Field(
        default=0,
        description="Exit code: 0=success, 2=blocking error"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warning messages"
    )
    execution_time: float = Field(
        default=0.0,
        description="Execution time in seconds"
    )
    files_checked: int = Field(
        default=0,
        description="Number of files checked"
    )
    auto_fixed: int = Field(
        default=0,
        description="Number of issues auto-fixed"
    )

    def to_exit_code(self) -> ExitCode:
        """Convert result to exit code."""
        if self.passed:
            return ExitCode.SUCCESS
        return ExitCode.BLOCKING_ERROR


class HookConfig(BaseModel):
    """Configuration for a quality hook."""

    enabled: bool = Field(default=True, description="Whether hook is enabled")
    timeout: float = Field(
        default=30.0,
        description="Timeout in seconds (max 30s per hook)"
    )
    auto_fix: bool = Field(
        default=True,
        description="Whether to auto-fix issues"
    )
    strict_mode: bool = Field(
        default=False,
        description="Enable strict mode (mypy --strict)"
    )
    check_only: bool = Field(
        default=False,
        description="Check only, don't modify files"
    )
    line_length: int = Field(
        default=88,
        description="Line length for Black formatting"
    )


class LintError(BaseModel):
    """A single lint error from Ruff."""

    file: str
    line: int
    column: int
    code: str
    message: str
    category: ErrorCategory
    fixable: bool = False

    @property
    def is_critical(self) -> bool:
        """Check if error is critical (E or F)."""
        return self.category in (ErrorCategory.ERROR, ErrorCategory.FATAL)


class TypeErrorInfo(BaseModel):
    """A single type error from Mypy."""

    file: str
    line: int
    column: Optional[int] = None
    message: str
    error_code: Optional[str] = None
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None


class TestResult(BaseModel):
    """Result of a single test execution."""

    test_name: str
    passed: bool
    duration: float = 0.0
    error_message: Optional[str] = None
    traceback: Optional[str] = None


class DocstringInfo(BaseModel):
    """Information about a function's docstring."""

    function_name: str
    file: str
    line: int
    has_docstring: bool = False
    has_args_doc: bool = False
    has_returns_doc: bool = False
    missing_params: List[str] = Field(default_factory=list)
    style: str = "google"  # google, numpy, sphinx


class AggregatedResult(BaseModel):
    """Aggregated results from all hooks."""

    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_auto_fixed: int = 0
    total_execution_time: float = 0.0
    exit_code: int = 0
    results: List[QualityCheckResult] = Field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Check if all checks passed."""
        return self.failed_checks == 0

    def add_result(self, result: QualityCheckResult) -> None:
        """Add a result to the aggregation."""
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
        self.total_errors += len(result.errors)
        self.total_warnings += len(result.warnings)
        self.total_auto_fixed += result.auto_fixed
        self.total_execution_time += result.execution_time

        # Exit code 2 if any check fails
        if result.exit_code == ExitCode.BLOCKING_ERROR:
            self.exit_code = ExitCode.BLOCKING_ERROR
