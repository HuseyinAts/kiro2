"""
Pydantic models for detection results.

Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import ExitCode, PatternType, SeverityLevel


class DetectionResult(BaseModel):
    """
    Result of a single pattern detection.

    Contains all information about a detected reward hacking pattern
    including location, severity, and remediation suggestion.
    """

    detector_name: str = Field(
        ..., description="Name of the detector that found the issue"
    )
    pattern_type: PatternType = Field(
        ..., description="Type of reward hacking pattern detected"
    )
    severity: SeverityLevel = Field(..., description="Severity level of the detection")
    file_path: str = Field(..., description="Path to file containing the issue")
    line_number: int = Field(..., ge=1, description="Line number where issue was found")
    column_number: int | None = Field(
        default=None, ge=0, description="Column number where issue was found"
    )
    code_snippet: str = Field(
        ..., description="Code snippet showing the problematic code"
    )
    message: str = Field(..., description="Human-readable description of the issue")
    remediation: str = Field(..., description="Suggested fix for the issue")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score (0.0 to 1.0)"
    )

    model_config = ConfigDict(use_enum_values=True)


class HookResult(BaseModel):
    """
    Aggregated result from all detectors.

    Contains exit code decision, counts, and all individual results.
    """

    exit_code: ExitCode = Field(
        ..., description="Exit code: 0=clean, 1=warning, 2=block"
    )
    total_detections: int = Field(
        default=0, ge=0, description="Total number of detections"
    )
    critical_count: int = Field(
        default=0, ge=0, description="Number of critical (blocking) issues"
    )
    warning_count: int = Field(default=0, ge=0, description="Number of warning issues")
    info_count: int = Field(
        default=0, ge=0, description="Number of informational issues"
    )
    results: list[DetectionResult] = Field(
        default_factory=list, description="All individual detection results"
    )
    summary: str = Field(default="", description="Human-readable summary of results")
    execution_time_ms: float = Field(
        default=0.0, ge=0.0, description="Total execution time in milliseconds"
    )
    files_analyzed: int = Field(default=0, ge=0, description="Number of files analyzed")

    model_config = ConfigDict(use_enum_values=True)

    @property
    def is_clean(self) -> bool:
        """Check if no reward hacking was detected."""
        return self.total_detections == 0

    @property
    def should_block(self) -> bool:
        """Check if commit should be blocked."""
        return self.critical_count > 0


class DetectorConfig(BaseModel):
    """
    Configuration for a single detector.

    Allows enabling/disabling detectors and customizing behavior.
    """

    enabled: bool = Field(default=True, description="Whether the detector is enabled")
    severity: SeverityLevel | None = Field(
        default=None,
        description=(
            "Severity override. None = not overridden; the detector's own "
            "`default_severity` class attribute applies. A concrete value here "
            "(from YAML/CI config) wins over the class declaration."
        ),
    )
    patterns: list[str] = Field(
        default_factory=list, description="Additional regex patterns to match"
    )
    exceptions: list[str] = Field(
        default_factory=list,
        description="Exception patterns (legitimate uses to ignore)",
    )
    min_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for reporting",
    )

    model_config = ConfigDict(use_enum_values=True)


class GlobalConfig(BaseModel):
    """
    Global configuration for the reward hacking prevention system.
    """

    enabled: bool = Field(default=True, description="Master switch for the system")
    fail_on_warning: bool = Field(
        default=False, description="Whether to return exit code 2 for warnings"
    )
    timeout_seconds: float = Field(
        default=30.0, gt=0.0, description="Maximum execution time per file"
    )
    max_files: int = Field(
        default=100, gt=0, description="Maximum number of files to analyze in one run"
    )
    detectors: dict[str, DetectorConfig] = Field(
        default_factory=dict, description="Per-detector configuration"
    )
