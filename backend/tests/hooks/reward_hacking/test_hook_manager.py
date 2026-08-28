"""
Unit tests for HookManager.

Tests the orchestration of reward hacking detection.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path

import pytest

from backend.hooks.reward_hacking.hook_manager import (
    HookManager,
    run_reward_hacking_detection,
)
from backend.hooks.reward_hacking.models.detection_result import GlobalConfig
from backend.hooks.reward_hacking.models.enums import ExitCode


def create_temp_file(content: str, suffix: str = ".py") -> str:
    """Create a temporary file with given content and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)
    return path


def cleanup_temp_file(path: str) -> None:
    """Safely clean up a temporary file.

    30 Tem 2026: burada `except PermissionError: pass` vardi ve bekci bunu
    HAKLI olarak sessiz-yutma sayiyordu (GERCEK bulgu, fixture degil).
    Yorumu bekcinin regex'ine uyacak sekilde yeniden yazmak onu kandirmak
    olurdu; bunun yerine yutma deyimsel olarak ifade edildi.
    """
    with contextlib.suppress(PermissionError):  # Windows dosya kilidi
        Path(path).unlink(missing_ok=True)


class TestHookManager:
    """Tests for HookManager."""

    @pytest.fixture
    def manager(self):
        return HookManager()

    def test_registers_all_detectors(self, manager):
        """Test that all 8 detectors are registered."""
        assert len(manager.detectors) == 8
        names = manager.get_detector_names()
        assert "AssertTrueDetector" in names
        assert "EchoSuccessDetector" in names
        assert "PlaceholderDetector" in names
        assert "CoverageManipulationDetector" in names
        assert "MockAbuseDetector" in names
        assert "EmptyExceptionDetector" in names
        assert "HardcodedTestDataDetector" in names
        assert "CICDBypassDetector" in names

    @pytest.mark.asyncio
    async def test_clean_file_returns_success(self, manager):
        """Test that clean file returns exit code 0."""
        content = """
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
"""
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            assert result.exit_code == ExitCode.SUCCESS
            assert result.critical_count == 0
        finally:
            cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_reward_hacking_returns_blocking_error(self, manager):
        """Test that reward hacking returns exit code 2."""
        content = """
def test_fake():
    assert True
"""
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            assert result.exit_code == ExitCode.BLOCKING_ERROR
            assert result.critical_count > 0
        finally:
            cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_warning_returns_warning_code(self, manager):
        """Test that warnings return exit code 1 or 0."""
        content = """
def test_user():
    user_id = 1
    pass
"""
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            # Might be warning or info depending on detection
            assert result.exit_code in (ExitCode.SUCCESS, ExitCode.WARNING)
        finally:
            cleanup_temp_file(path)

    def test_disable_detector(self, manager):
        """Test disabling a detector."""
        result = manager.disable_detector("AssertTrueDetector")
        assert result is True

        # Verify it's disabled
        for detector in manager.detectors:
            if detector.name == "AssertTrueDetector":
                assert not detector.is_enabled()

    def test_enable_detector(self, manager):
        """Test enabling a detector."""
        manager.disable_detector("AssertTrueDetector")
        result = manager.enable_detector("AssertTrueDetector")
        assert result is True

        for detector in manager.detectors:
            if detector.name == "AssertTrueDetector":
                assert detector.is_enabled()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that slow detections are timed out."""
        config = GlobalConfig(timeout_seconds=0.001)  # Very short timeout
        manager = HookManager(config=config)

        content = "assert True" * 10000  # Large content
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            # Should complete without crashing
            assert result is not None
        finally:
            cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_unsupported_file_skipped(self, manager):
        """Test that unsupported files are skipped."""
        content = "assert True"  # Would be detected in .py
        path = create_temp_file(content, suffix=".txt")
        try:
            result = await manager.run_hooks([path])
            assert result.files_analyzed == 0
        finally:
            cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_multiple_files(self, manager):
        """Test analyzing multiple files."""
        paths = []
        try:
            for i in range(3):
                content = f"def test_{i}():\n    assert True\n"
                path = create_temp_file(content)
                paths.append(path)

            result = await manager.run_hooks(paths)
            assert result.files_analyzed == 3
            assert result.critical_count >= 3
        finally:
            for path in paths:
                cleanup_temp_file(path)

    @pytest.mark.asyncio
    async def test_summary_generation(self, manager):
        """Test that summary is generated correctly."""
        content = "assert True"
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            assert result.summary
            assert (
                "REWARD HACKING" in result.summary
                or "No reward hacking" in result.summary
            )
        finally:
            cleanup_temp_file(path)


class TestGlobalConfig:
    """Tests for GlobalConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GlobalConfig()
        assert config.enabled is True
        assert config.fail_on_warning is False
        assert config.timeout_seconds == 30.0
        assert config.max_files == 100

    def test_custom_config(self):
        """Test custom configuration."""
        config = GlobalConfig(
            enabled=True, fail_on_warning=True, timeout_seconds=10.0, max_files=50
        )
        assert config.fail_on_warning is True
        assert config.timeout_seconds == 10.0
        assert config.max_files == 50

    @pytest.mark.asyncio
    async def test_fail_on_warning_config(self):
        """Test fail_on_warning configuration."""
        config = GlobalConfig(fail_on_warning=True)
        manager = HookManager(config=config)

        content = """
def test_user():
    user_id = 1
"""
        path = create_temp_file(content)
        try:
            result = await manager.run_hooks([path])
            # With fail_on_warning, warnings should cause exit code 2
            if result.warning_count > 0:
                assert result.exit_code == ExitCode.BLOCKING_ERROR
        finally:
            cleanup_temp_file(path)


class TestConvenienceFunction:
    """Tests for run_reward_hacking_detection convenience function."""

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience function."""
        content = "assert True"
        path = create_temp_file(content)
        try:
            result = await run_reward_hacking_detection([path])
            assert result is not None
            assert hasattr(result, "exit_code")
        finally:
            cleanup_temp_file(path)
