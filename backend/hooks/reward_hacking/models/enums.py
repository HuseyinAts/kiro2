"""
Enums for Reward Hacking Prevention system.

Daisy Stanton Standards - Exit Code Classification
"""

from __future__ import annotations

from enum import Enum


class SeverityLevel(str, Enum):
    """
    Severity levels for detected patterns.

    CRITICAL: Blocks commit (Exit Code 2)
    WARNING: Non-blocking warning (Exit Code 1)
    INFO: Informational only (Exit Code 0)
    """

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class PatternType(str, Enum):
    """
    Types of reward hacking patterns detected.

    Each type corresponds to a specific detector.
    """

    ASSERT_TRUE = "assert_true"
    ECHO_SUCCESS = "echo_success"
    PLACEHOLDER = "placeholder"
    COVERAGE_MANIPULATION = "coverage_manipulation"
    MOCK_ABUSE = "mock_abuse"
    EMPTY_EXCEPTION = "empty_exception"
    HARDCODED_TEST_DATA = "hardcoded_test_data"
    CICD_BYPASS = "cicd_bypass"


class ExitCode(int, Enum):
    """
    Exit codes following Daisy Stanton standards.

    SUCCESS (0): Clean - No reward hacking detected
    WARNING (1): Non-critical issues found
    BLOCKING_ERROR (2): Critical reward hacking detected, blocks commit
    """

    SUCCESS = 0
    WARNING = 1
    BLOCKING_ERROR = 2


class FileType(str, Enum):
    """
    Supported file types for analysis.
    """

    PYTHON = "python"
    SHELL = "shell"
    YAML = "yaml"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
