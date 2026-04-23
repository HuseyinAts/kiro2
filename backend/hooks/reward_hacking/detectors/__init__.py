"""
Reward Hacking Detectors.

8 specialized detectors for detecting reward hacking patterns:
1. AssertTrueDetector - Detects fake assertions
2. EchoSuccessDetector - Detects fake success messages
3. PlaceholderDetector - Detects placeholder code
4. CoverageManipulationDetector - Detects coverage manipulation
5. MockAbuseDetector - Detects excessive mocking
6. EmptyExceptionDetector - Detects empty exception handlers
7. HardcodedTestDataDetector - Detects hardcoded test data
8. CICDBypassDetector - Detects CI/CD bypass attempts
"""

from __future__ import annotations

from .assert_true_detector import AssertTrueDetector
from .cicd_bypass_detector import CICDBypassDetector
from .coverage_manipulation_detector import CoverageManipulationDetector
from .echo_success_detector import EchoSuccessDetector
from .empty_exception_detector import EmptyExceptionDetector
from .hardcoded_test_data_detector import HardcodedTestDataDetector
from .mock_abuse_detector import MockAbuseDetector
from .placeholder_detector import PlaceholderDetector

__all__ = [
    "AssertTrueDetector",
    "CICDBypassDetector",
    "CoverageManipulationDetector",
    "EchoSuccessDetector",
    "EmptyExceptionDetector",
    "HardcodedTestDataDetector",
    "MockAbuseDetector",
    "PlaceholderDetector",
]
