"""
Reward Hacking Prevention Hooks System.

Daisy Stanton Standards - Reward Hacking Prevention
Boris Cherny Standards - Verification Feedback Loops

This module provides comprehensive detection of reward hacking patterns:
- Assert True Detection
- Echo Success Detection
- Placeholder Code Detection
- Coverage Manipulation Detection
- Mock Abuse Detection
- Empty Exception Handler Detection
- Hardcoded Test Data Detection
- CI/CD Bypass Detection
"""

from __future__ import annotations

from .base_detector import BaseDetector
from .exceptions import (
    ASTParseError,
    DetectorError,
    RewardHackingError,
)
from .hook_manager import HookManager
from .models.detection_result import (
    DetectionResult,
    DetectorConfig,
    HookResult,
)
from .models.enums import PatternType, SeverityLevel

__all__ = [
    # Core
    "BaseDetector",
    "HookManager",
    # Exceptions
    "RewardHackingError",
    "DetectorError",
    "ASTParseError",
    # Enums
    "SeverityLevel",
    "PatternType",
    # Models
    "DetectionResult",
    "HookResult",
    "DetectorConfig",
]

__version__ = "1.0.0"
