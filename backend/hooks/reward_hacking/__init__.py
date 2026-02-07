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
from .hook_manager import HookManager
from .exceptions import (
    RewardHackingError,
    DetectorError,
    ASTParseError,
)
from .models.enums import SeverityLevel, PatternType
from .models.detection_result import (
    DetectionResult,
    HookResult,
    DetectorConfig,
)

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
