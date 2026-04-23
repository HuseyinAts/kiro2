"""
Quality Gates Test Fixtures
============================

Shared fixtures for quality gates unit tests.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from backend.core.quality_gates.gates.base import CommandResult, GateContext
from backend.core.quality_gates.models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
    GateStatus,
    PipelineConfig,
    PipelineResult,
)

# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with sample files."""
    # Create basic structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    # Create sample Python file
    (tmp_path / "src" / "main.py").write_text(
        '"""Main module."""\n\ndef main() -> None:\n    print("Hello")\n'
    )

    # Create sample test file
    (tmp_path / "tests" / "test_main.py").write_text(
        'def test_main():\n    assert True\n'
    )

    # Create README
    (tmp_path / "README.md").write_text("# Test Project\n\nDescription here.\n")

    # Create pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test-project"\nversion = "1.0.0"\n'
    )

    return tmp_path


# =============================================================================
# Config Fixtures
# =============================================================================

@pytest.fixture
def sample_gate_config() -> GateConfig:
    """Create a sample gate configuration."""
    return GateConfig(
        name="test_gate",
        enabled=True,
        blocking=True,
        threshold=7.0,
        warning_threshold=8.5,
        timeout_seconds=120,
        max_retries=2,
        depends_on=[],
        tool_config={},
    )


@pytest.fixture
def sample_pipeline_config() -> PipelineConfig:
    """Create a sample pipeline configuration."""
    return PipelineConfig(
        name="test-pipeline",
        enabled=True,
        parallel_execution=True,
        fail_fast=False,
        timeout_seconds=600,
        gates={},
        report_formats=["console", "json"],
        allow_override=True,
    )


# =============================================================================
# Context Fixtures
# =============================================================================

@pytest.fixture
def gate_context(tmp_path: Path, sample_gate_config: GateConfig) -> GateContext:
    """Create a standard GateContext for testing."""
    return GateContext(
        working_dir=tmp_path,
        config=sample_gate_config,
        commit_hash="abc123",
        branch="main",
        changed_files=["src/main.py"],
        previous_result=None,
        extra={},
    )


# =============================================================================
# Result Fixtures
# =============================================================================

@pytest.fixture
def sample_gate_result() -> GateResult:
    """Create a sample gate result."""
    return GateResult(
        gate_name="test_gate",
        status=GateStatus.PASS,
        score=8.5,
        threshold=7.0,
        message="All checks passed",
        issues=[],
        metrics=GateMetrics(
            lines_checked=100,
            files_checked=5,
            issues_found=0,
            coverage_percent=85.0,
        ),
        details={},
        execution_time_ms=1500.0,
        blocking=True,
        retries=0,
        auto_fixed=False,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


@pytest.fixture
def sample_failed_result() -> GateResult:
    """Create a sample failed gate result."""
    return GateResult(
        gate_name="test_gate",
        status=GateStatus.FAIL,
        score=5.0,
        threshold=7.0,
        message="Found 3 critical issues",
        issues=[
            GateIssue(
                file="src/main.py",
                line=10,
                rule="E001",
                message="Syntax error",
                severity=GateSeverity.CRITICAL,
                suggestion="Fix the syntax",
            ),
        ],
        metrics=None,
        details={},
        execution_time_ms=2000.0,
        blocking=True,
        retries=0,
        auto_fixed=False,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


@pytest.fixture
def sample_pipeline_result(sample_gate_result: GateResult) -> PipelineResult:
    """Create a sample pipeline result."""
    return PipelineResult(
        pipeline_name="test-pipeline",
        status=GateStatus.PASS,
        gates=[sample_gate_result],
        total_score=8.5,
        passed_gates=1,
        failed_gates=0,
        skipped_gates=0,
        total_execution_time_ms=1500.0,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_command_result() -> CommandResult:
    """Create a mock command result."""
    return CommandResult(
        returncode=0,
        stdout="Success",
        stderr="",
        execution_time_ms=100.0,
    )


@pytest.fixture
def mock_failed_command_result() -> CommandResult:
    """Create a mock failed command result."""
    return CommandResult(
        returncode=1,
        stdout="",
        stderr="Error: Command failed",
        execution_time_ms=50.0,
    )


@pytest.fixture
def mock_async_subprocess() -> AsyncMock:
    """Create a mock async subprocess."""
    mock = AsyncMock()
    mock.communicate = AsyncMock(return_value=(b"output", b""))
    mock.returncode = 0
    return mock


# =============================================================================
# Issue Fixtures
# =============================================================================

@pytest.fixture
def sample_issues() -> list[GateIssue]:
    """Create a list of sample issues."""
    return [
        GateIssue(
            file="src/main.py",
            line=10,
            rule="E001",
            message="Line too long",
            severity=GateSeverity.LOW,
            suggestion="Break into multiple lines",
        ),
        GateIssue(
            file="src/main.py",
            line=20,
            rule="W001",
            message="Missing docstring",
            severity=GateSeverity.MEDIUM,
            suggestion="Add docstring",
        ),
        GateIssue(
            file="src/utils.py",
            line=5,
            rule="F001",
            message="Unused import",
            severity=GateSeverity.LOW,
            suggestion="Remove unused import",
        ),
    ]


# =============================================================================
# Helper Functions
# =============================================================================

def create_gate_config(
    name: str = "test_gate",
    enabled: bool = True,
    blocking: bool = True,
    threshold: float = 7.0,
    warning_threshold: float = 8.5,
    timeout_seconds: int = 120,
    **kwargs: Any,
) -> GateConfig:
    """Factory function for creating gate configs."""
    return GateConfig(
        name=name,
        enabled=enabled,
        blocking=blocking,
        threshold=threshold,
        warning_threshold=warning_threshold,
        timeout_seconds=timeout_seconds,
        max_retries=kwargs.get("max_retries", 2),
        depends_on=kwargs.get("depends_on", []),
        tool_config=kwargs.get("tool_config", {}),
    )


def create_gate_result(
    gate_name: str = "test_gate",
    status: GateStatus = GateStatus.PASS,
    score: float = 8.5,
    threshold: float = 7.0,
    **kwargs: Any,
) -> GateResult:
    """Factory function for creating gate results."""
    return GateResult(
        gate_name=gate_name,
        status=status,
        score=score,
        threshold=threshold,
        message=kwargs.get("message", "Test result"),
        issues=kwargs.get("issues", []),
        metrics=kwargs.get("metrics"),
        details=kwargs.get("details", {}),
        execution_time_ms=kwargs.get("execution_time_ms", 100.0),
        blocking=kwargs.get("blocking", True),
        retries=kwargs.get("retries", 0),
        auto_fixed=kwargs.get("auto_fixed", False),
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )
