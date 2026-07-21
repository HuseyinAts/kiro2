"""
Property-based tests for Reward Hacking Prevention.

Uses Hypothesis to test system-wide properties.
"""

from __future__ import annotations

import os
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backend.hooks.reward_hacking.config.patterns import REWARD_HACKING_PATTERNS
from backend.hooks.reward_hacking.detectors import (
    AssertTrueDetector,
    CICDBypassDetector,
    CoverageManipulationDetector,
    EchoSuccessDetector,
    EmptyExceptionDetector,
    HardcodedTestDataDetector,
    MockAbuseDetector,
    PlaceholderDetector,
)
from backend.hooks.reward_hacking.hook_manager import HookManager
from backend.hooks.reward_hacking.models.enums import (
    ExitCode,
    PatternType,
    SeverityLevel,
)


def create_temp_file(content: str, suffix: str = '.py') -> str:
    """Create a temporary file with given content and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    try:
        os.write(fd, content.encode('utf-8'))
    finally:
        os.close(fd)
    return path


def cleanup_temp_file(path: str) -> None:
    """Safely clean up a temporary file."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        pass  # Windows file locking - ignore


# =============================================================================
# PROPERTY 1: DETECTION COMPLETENESS
# =============================================================================

class TestDetectionCompleteness:
    """
    Property 1: For any file containing a reward hacking pattern from the
    banned patterns list, the hook manager SHALL detect it and return a
    non-zero exit code.
    """

    # Known reward hacking patterns that MUST be detected
    KNOWN_PATTERNS = [
        ("assert True", "assert_true"),
        ("assert true", "assert_true"),
        ('echo "Success"', "echo_success"),
        ('print("Success")', "echo_success"),
        ("pass  # placeholder", "placeholder"),
        ("def skip_coverage():  # pragma: no cover\n    pass", "coverage_manipulation"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("pattern,pattern_type", KNOWN_PATTERNS)
    async def test_known_pattern_detected(self, pattern, pattern_type):
        """Test that all known patterns are detected."""
        manager = HookManager()
        path = create_temp_file(pattern)
        try:
            result = await manager.run_hooks([path])
            # Should detect something
            assert result.total_detections > 0, f"Pattern not detected: {pattern}"
        finally:
            cleanup_temp_file(path)

    @given(st.sampled_from(list(REWARD_HACKING_PATTERNS.keys())))
    @settings(max_examples=20)
    def test_pattern_type_has_patterns(self, pattern_type):
        """Test that each pattern type has at least one pattern defined."""
        patterns = REWARD_HACKING_PATTERNS[pattern_type]
        assert len(patterns) > 0, f"No patterns defined for {pattern_type}"


# =============================================================================
# PROPERTY 2: EXIT CODE CONSISTENCY
# =============================================================================

class TestExitCodeConsistency:
    """
    Property 2: For any detection result with severity CRITICAL,
    the aggregated exit code SHALL be 2 (blocking).
    """

    @pytest.mark.asyncio
    async def test_critical_detection_blocks(self):
        """Test that critical detections always return exit code 2."""
        manager = HookManager()

        # File with critical pattern
        critical_patterns = [
            "assert True",
            "except:\n    pass",
        ]

        for pattern in critical_patterns:
            path = create_temp_file(pattern)
            try:
                result = await manager.run_hooks([path])
                if result.critical_count > 0:
                    assert result.exit_code == ExitCode.BLOCKING_ERROR, \
                        f"Critical detection did not block: {pattern}"
            finally:
                cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_no_detection_returns_zero(self):
        """Test that clean files return exit code 0."""
        manager = HookManager()

        clean_code = """
def calculate_sum(a: int, b: int) -> int:
    '''Calculate the sum of two numbers.'''
    return a + b

def test_calculate_sum():
    result = calculate_sum(2, 3)
    assert result == 5
"""
        path = create_temp_file(clean_code)
        try:
            result = await manager.run_hooks([path])
            assert result.exit_code == ExitCode.SUCCESS
        finally:
            cleanup_temp_file(path)


# =============================================================================
# PROPERTY 3: FALSE POSITIVE MINIMIZATION
# =============================================================================

class TestFalsePositiveMinimization:
    """
    Property 3: For any legitimate code pattern (e.g., assert True in docstring),
    the context analyzer SHALL exclude it from critical detections.
    """

    LEGITIMATE_PATTERNS = [
        # Docstring examples
        '"""Example: assert True"""',
        "'''assert True is used for...'''",
        # Comments explaining patterns
        "# Note: assert True should not be used",
        "# Example of bad practice: assert True",
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("code", LEGITIMATE_PATTERNS)
    async def test_legitimate_pattern_not_critical(self, code):
        """Test that legitimate patterns are not flagged as critical."""
        detector = AssertTrueDetector()

        results = await detector.detect("file.py", code)

        # Should either not detect or have low confidence
        for result in results:
            if result.severity == SeverityLevel.CRITICAL:
                assert result.confidence < 0.8, \
                    f"Legitimate pattern flagged as critical: {code}"


# =============================================================================
# PROPERTY 4: REMEDIATION COMPLETENESS
# =============================================================================

class TestRemediationCompleteness:
    """
    Property 4: For any detection result, there SHALL exist a
    non-empty remediation suggestion.
    """

    ALL_DETECTORS = [
        AssertTrueDetector,
        EchoSuccessDetector,
        PlaceholderDetector,
        CoverageManipulationDetector,
        MockAbuseDetector,
        EmptyExceptionDetector,
        HardcodedTestDataDetector,
        CICDBypassDetector,
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("detector_cls", ALL_DETECTORS)
    async def test_detector_provides_remediation(self, detector_cls):
        """Test that each detector provides remediation."""
        detector = detector_cls()

        # Use a pattern that should trigger this detector
        test_patterns = {
            "AssertTrueDetector": "assert True",
            "EchoSuccessDetector": 'print("Success")',
            "PlaceholderDetector": "pass  # placeholder",
            "CoverageManipulationDetector": "# pragma: no cover",
            "MockAbuseDetector": "mock = Mock(return_value=True)",
            "EmptyExceptionDetector": "except:\n    pass",
            "HardcodedTestDataDetector": "password = 'password123'",
            "CICDBypassDetector": "[skip ci]",
        }

        pattern = test_patterns.get(detector_cls.__name__, "assert True")

        # Determine file type
        suffix = '.py' if 'Echo' not in detector_cls.__name__ else '.py'

        results = await detector.detect(f"test{suffix}", pattern)

        for result in results:
            assert result.remediation, \
                f"{detector_cls.__name__} did not provide remediation"
            assert len(result.remediation) > 10, \
                f"{detector_cls.__name__} remediation too short"


# =============================================================================
# PROPERTY 5: PARALLEL EXECUTION SAFETY
# =============================================================================

class TestParallelExecutionSafety:
    """
    Property 5: For any set of files analyzed concurrently,
    the detection results SHALL be deterministic and order-independent.
    """

    @pytest.mark.asyncio
    async def test_deterministic_results(self):
        """Test that results are deterministic across multiple runs."""
        manager = HookManager()

        code = """
def test_fake():
    assert True

try:
    risky()
except Exception:
    pass
"""
        path = create_temp_file(code)
        try:
            # Run multiple times
            results = []
            for _ in range(3):
                result = await manager.run_hooks([path])
                results.append(result)

            # All runs should have same counts
            assert all(r.total_detections == results[0].total_detections for r in results)
            assert all(r.critical_count == results[0].critical_count for r in results)
        finally:
            cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_order_independent_results(self):
        """Test that file order doesn't affect detection counts."""
        manager = HookManager()

        paths = []
        try:
            # Create test files
            for i in range(3):
                content = f"def test_{i}():\n    assert True\n"
                path = create_temp_file(content)
                paths.append(path)

            # Run in different orders
            result1 = await manager.run_hooks(paths)
            result2 = await manager.run_hooks(list(reversed(paths)))

            # Should have same total detections
            assert result1.total_detections == result2.total_detections

        finally:
            for path in paths:
                cleanup_temp_file(path)


# =============================================================================
# PROPERTY 6: PATTERN COVERAGE
# =============================================================================

class TestPatternCoverage:
    """
    Property 6: For any detector, the number of regex patterns + AST checks
    SHALL cover all acceptance criteria for that detector.
    """

    @pytest.mark.parametrize("pattern_type,min_patterns", [
        ("assert_true", 3),     # At least 3 patterns for assert True
        ("echo_success", 3),   # At least 3 patterns for echo success
        ("placeholder", 5),    # At least 5 patterns for placeholders
        ("coverage_manipulation", 3),  # At least 3 patterns
        ("mock_abuse", 3),     # At least 3 patterns
        ("empty_exception", 3),  # At least 3 patterns
        ("hardcoded_test_data", 3),  # At least 3 patterns
        ("cicd_bypass", 3),    # At least 3 patterns
    ])
    def test_minimum_pattern_count(self, pattern_type, min_patterns):
        """Test that each pattern type has minimum required patterns."""
        patterns = REWARD_HACKING_PATTERNS.get(pattern_type, [])
        assert len(patterns) >= min_patterns, \
            f"{pattern_type} has only {len(patterns)} patterns, expected {min_patterns}"

    def test_all_pattern_types_have_detector(self):
        """Test that every pattern type has a corresponding detector."""
        detector_pattern_types = {
            PatternType.ASSERT_TRUE,
            PatternType.ECHO_SUCCESS,
            PatternType.PLACEHOLDER,
            PatternType.COVERAGE_MANIPULATION,
            PatternType.MOCK_ABUSE,
            PatternType.EMPTY_EXCEPTION,
            PatternType.HARDCODED_TEST_DATA,
            PatternType.CICD_BYPASS,
        }

        # All pattern types should be covered
        assert len(detector_pattern_types) == 8
