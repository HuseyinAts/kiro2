"""
Unit tests for Reward Hacking Detectors.

Tests each detector with known patterns.
"""

from __future__ import annotations

import pytest

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
from backend.hooks.reward_hacking.models.enums import PatternType, SeverityLevel

# =============================================================================
# ASSERT TRUE DETECTOR TESTS
# =============================================================================

class TestAssertTrueDetector:
    """Tests for AssertTrueDetector."""

    @pytest.fixture
    def detector(self):
        return AssertTrueDetector()

    @pytest.mark.asyncio
    async def test_detects_assert_true(self, detector):
        """REQ-1.1: Detect assert True pattern."""
        content = """
def test_something():
    assert True
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1
        assert any(r.pattern_type == PatternType.ASSERT_TRUE for r in results)

    @pytest.mark.asyncio
    async def test_detects_assert_true_with_comment(self, detector):
        """REQ-1.1: Detect assert True with comment."""
        content = """
def test_something():
    assert True  # this is fake
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_assert_true_cpp_style(self, detector):
        """REQ-1.3: Detect ASSERT_TRUE(true)."""
        content = """
TEST(MyTest, TestCase) {
    ASSERT_TRUE(true);
}
"""
        results = await detector.detect("test_file.cpp", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_self_assertTrue_True(self, detector):
        """REQ-1.4: Detect self.assertTrue(True)."""
        content = """
class TestCase(unittest.TestCase):
    def test_something(self):
        self.assertTrue(True)
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_ignores_legitimate_assert(self, detector):
        """REQ-1.5: Ignore legitimate assertions."""
        content = """
def test_user_creation():
    user = create_user()
    assert user.email == "test@example.com"
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_provides_remediation(self, detector):
        """REQ-1.6: Provides remediation suggestion."""
        content = "assert True"
        results = await detector.detect("test_file.py", content)
        if results:
            assert results[0].remediation
            assert "meaningful" in results[0].remediation.lower()


# =============================================================================
# ECHO SUCCESS DETECTOR TESTS
# =============================================================================

class TestEchoSuccessDetector:
    """Tests for EchoSuccessDetector."""

    @pytest.fixture
    def detector(self):
        return EchoSuccessDetector()

    @pytest.mark.asyncio
    async def test_detects_echo_success(self, detector):
        """REQ-2.1: Detect echo Success pattern."""
        content = 'echo "Success"'
        results = await detector.detect("script.sh", content)
        assert len(results) >= 1
        assert any(r.pattern_type == PatternType.ECHO_SUCCESS for r in results)

    @pytest.mark.asyncio
    async def test_detects_print_success(self, detector):
        """REQ-2.2: Detect print("Success")."""
        content = 'print("Success")'
        results = await detector.detect("script.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_ignores_validated_success(self, detector):
        """REQ-2.5: Ignore success with validation."""
        content = """
if test -f result.txt; then
    echo "Success"
fi
"""
        results = await detector.detect("script.sh", content)
        # Should have lower confidence or be filtered
        assert all(r.confidence < 0.9 for r in results) or len(results) == 0


# =============================================================================
# PLACEHOLDER DETECTOR TESTS
# =============================================================================

class TestPlaceholderDetector:
    """Tests for PlaceholderDetector."""

    @pytest.fixture
    def detector(self):
        return PlaceholderDetector()

    @pytest.mark.asyncio
    async def test_detects_pass_placeholder(self, detector):
        """REQ-3.1: Detect pass # placeholder."""
        content = """
def my_function():
    pass  # placeholder
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_todo_comment(self, detector):
        """REQ-3.2: Detect # TODO: comments."""
        content = """
def my_function():
    # TODO: implement this
    pass
"""
        results = await detector.detect("file.py", content)
        # Should detect either TODO or pass placeholder
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_empty_function(self, detector):
        """REQ-3.3: Detect function with only pass."""
        content = """
def empty_function():
    pass
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_not_implemented(self, detector):
        """REQ-3.4: Detect raise NotImplementedError."""
        content = """
def not_ready():
    raise NotImplementedError()
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_ellipsis(self, detector):
        """REQ-3.5: Detect ... (Ellipsis) placeholder."""
        content = """
def stub():
    ...
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1


# =============================================================================
# COVERAGE MANIPULATION DETECTOR TESTS
# =============================================================================

class TestCoverageManipulationDetector:
    """Tests for CoverageManipulationDetector."""

    @pytest.fixture
    def detector(self):
        return CoverageManipulationDetector()

    @pytest.mark.asyncio
    async def test_detects_pragma_no_cover(self, detector):
        """REQ-4.1: Detect # pragma: no cover."""
        content = "if DEBUG:  # pragma: no cover"
        results = await detector.detect("file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_accepts_documented_pragma(self, detector):
        """REQ-4.6: Accept documented pragma."""
        content = "if DEBUG:  # pragma: no cover  # defensive code for race condition"
        results = await detector.detect("file.py", content)
        # Should be INFO, not CRITICAL
        assert all(r.severity != SeverityLevel.CRITICAL for r in results) or len(results) == 0

    @pytest.mark.asyncio
    async def test_detects_type_ignore(self, detector):
        """REQ-4.4: Detect excessive type: ignore."""
        content = """
x: int = "string"  # type: ignore
y: str = 123  # type: ignore
z: bool = None  # type: ignore
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1


# =============================================================================
# MOCK ABUSE DETECTOR TESTS
# =============================================================================

class TestMockAbuseDetector:
    """Tests for MockAbuseDetector."""

    @pytest.fixture
    def detector(self):
        return MockAbuseDetector()

    @pytest.mark.asyncio
    async def test_detects_high_mock_ratio(self, detector):
        """REQ-5.2: Warn when mock ratio > 80%."""
        content = """
from unittest.mock import Mock, patch, MagicMock

@patch('module.func1')
@patch('module.func2')
@patch('module.func3')
@patch('module.func4')
@patch('module.func5')
def test_something(mock1, mock2, mock3, mock4, mock5):
    pass
"""
        results = await detector.detect("test_file.py", content)
        # Should detect mock abuse
        assert any(r.pattern_type == PatternType.MOCK_ABUSE for r in results)

    @pytest.mark.asyncio
    async def test_detects_static_return_values(self, detector):
        """REQ-5.4: Detect static mock return values."""
        content = """
mock = Mock(return_value=True)
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1


# =============================================================================
# EMPTY EXCEPTION DETECTOR TESTS
# =============================================================================

class TestEmptyExceptionDetector:
    """Tests for EmptyExceptionDetector."""

    @pytest.fixture
    def detector(self):
        return EmptyExceptionDetector()

    @pytest.mark.asyncio
    async def test_detects_except_pass(self, detector):
        """REQ-6.1: Detect except: pass."""
        content = """
try:
    risky()
except:
    pass
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1
        assert any(r.pattern_type == PatternType.EMPTY_EXCEPTION for r in results)

    @pytest.mark.asyncio
    async def test_detects_except_exception_pass(self, detector):
        """REQ-6.2: Detect except Exception: pass."""
        content = """
try:
    risky()
except Exception:
    pass
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_bare_except(self, detector):
        """REQ-6.4: Detect bare except:."""
        content = """
try:
    something()
except:
    handle_error()
"""
        results = await detector.detect("file.py", content)
        assert len(results) >= 1


# =============================================================================
# HARDCODED TEST DATA DETECTOR TESTS
# =============================================================================

class TestHardcodedTestDataDetector:
    """Tests for HardcodedTestDataDetector."""

    @pytest.fixture
    def detector(self):
        return HardcodedTestDataDetector()

    @pytest.mark.asyncio
    async def test_detects_magic_number(self, detector):
        """REQ-7.2: Detect magic numbers."""
        content = """
def test_user():
    user_id = 1
    assert get_user(user_id)
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_hardcoded_password(self, detector):
        """REQ-7.3: Detect hardcoded password."""
        content = """
def test_login():
    password = "password123"
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1


# =============================================================================
# CI/CD BYPASS DETECTOR TESTS
# =============================================================================

class TestCICDBypassDetector:
    """Tests for CICDBypassDetector."""

    @pytest.fixture
    def detector(self):
        return CICDBypassDetector()

    @pytest.mark.asyncio
    async def test_detects_skip_ci(self, detector):
        """REQ-8.1: Detect [skip ci]."""
        content = "[skip ci] Update README"
        results = await detector.detect("COMMIT_MSG", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_detects_pytest_skip_without_reason(self, detector):
        """REQ-8.3: Detect @pytest.mark.skip without reason."""
        content = """
@pytest.mark.skip
def test_broken():
    pass
"""
        results = await detector.detect("test_file.py", content)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_accepts_skip_with_reason(self, detector):
        """REQ-8.3: Accept skip with reason."""
        content = """
@pytest.mark.skip(reason="External service unavailable")
def test_external():
    pass
"""
        results = await detector.detect("test_file.py", content)
        # Should be INFO or no results
        assert all(r.severity != SeverityLevel.CRITICAL for r in results) or len(results) == 0
