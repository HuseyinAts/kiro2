"""Tests for RuffHook."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.hooks.ruff_hook import RuffHook
from backend.hooks.models import HookConfig, ExitCode, ErrorCategory


class TestRuffHook:
    """Tests for RuffHook."""

    @pytest.fixture
    def hook(self):
        """Create RuffHook instance."""
        return RuffHook(HookConfig())

    def test_name(self, hook):
        """Test hook name."""
        assert hook.name == "ruff"

    def test_filter_python_files(self, hook):
        """Test Python file filtering."""
        files = ["test.py", "readme.md", "src/main.py", "config.yaml"]
        result = hook._filter_python_files(files)
        assert result == ["test.py", "src/main.py"]

    def test_get_category_error(self, hook):
        """Test error category detection."""
        assert hook._get_category("E501") == ErrorCategory.ERROR

    def test_get_category_fatal(self, hook):
        """Test fatal category detection."""
        assert hook._get_category("F401") == ErrorCategory.FATAL

    def test_get_category_warning(self, hook):
        """Test warning category detection."""
        assert hook._get_category("W291") == ErrorCategory.WARNING

    def test_parse_output(self, hook):
        """Test output parsing."""
        output = """
test.py:10:5: E501 Line too long
test.py:15:1: F401 'os' imported but unused
"""
        errors = hook._parse_output(output)
        assert len(errors) == 2
        assert errors[0].code == "E501"
        assert errors[0].line == 10
        assert errors[1].code == "F401"
        assert errors[1].line == 15

    def test_count_auto_fixed(self, hook):
        """Test auto-fixed count parsing."""
        output = "Found 5 errors (3 fixed, 2 remaining)"
        count = hook._count_auto_fixed(output)
        assert count == 3

    @pytest.mark.asyncio
    async def test_run_no_files(self, hook):
        """Test run with no Python files."""
        result = await hook.run([])
        assert result.passed is True
        assert result.files_checked == 0

    @pytest.mark.asyncio
    async def test_run_success(self, hook):
        """Test successful run with no errors."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_with_critical_errors(self, hook):
        """Test run with critical errors."""
        error_output = "test.py:10:5: E501 Line too long"
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (1, error_output, "")
            result = await hook.run(["test.py"])

            assert result.passed is False
            assert result.exit_code == ExitCode.BLOCKING_ERROR
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_run_with_warnings_only(self, hook):
        """Test run with warnings only (should pass)."""
        warning_output = "test.py:10:5: W291 Trailing whitespace"
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, warning_output, "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS
            assert len(result.warnings) > 0
