"""
Custom exceptions for Reward Hacking Prevention system.

Daisy Stanton Standards - Error Handling
"""

from __future__ import annotations


class RewardHackingError(Exception):
    """
    Base exception for reward hacking detection errors.

    All custom exceptions in this module inherit from this class.
    """

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class DetectorError(RewardHackingError):
    """
    Exception raised when a detector fails to execute.

    This error indicates a problem with the detector itself,
    not with the code being analyzed.
    """

    def __init__(
        self,
        detector_name: str,
        message: str,
        file_path: str | None = None
    ):
        details = {
            "detector": detector_name,
            "file_path": file_path,
        }
        super().__init__(f"Detector '{detector_name}' failed: {message}", details)
        self.detector_name = detector_name
        self.file_path = file_path


class ASTParseError(RewardHackingError):
    """
    Exception raised when AST parsing fails.

    This typically occurs with malformed Python code.
    """

    def __init__(
        self,
        file_path: str,
        message: str,
        line_number: int | None = None
    ):
        details = {
            "file_path": file_path,
            "line_number": line_number,
        }
        super().__init__(f"AST parse error in '{file_path}': {message}", details)
        self.file_path = file_path
        self.line_number = line_number


class ConfigurationError(RewardHackingError):
    """
    Exception raised when configuration is invalid.
    """

    def __init__(self, message: str, config_key: str | None = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(f"Configuration error: {message}", details)
        self.config_key = config_key


class TimeoutError(RewardHackingError):
    """
    Exception raised when detection exceeds timeout.
    """

    def __init__(
        self,
        file_path: str,
        timeout_seconds: float
    ):
        details = {
            "file_path": file_path,
            "timeout_seconds": timeout_seconds,
        }
        super().__init__(
            f"Detection timed out after {timeout_seconds}s for '{file_path}'",
            details
        )
        self.file_path = file_path
        self.timeout_seconds = timeout_seconds


class PatternMatchError(RewardHackingError):
    """
    Exception raised when pattern matching fails.
    """

    def __init__(self, pattern: str, message: str):
        details = {"pattern": pattern}
        super().__init__(f"Pattern match error for '{pattern}': {message}", details)
        self.pattern = pattern
