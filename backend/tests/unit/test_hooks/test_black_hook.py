"""Tests for BlackHook."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.hooks.black_hook import BlackHook
from backend.hooks.models import HookConfig, ExitCode


class TestBlackHook:
    """Tests for BlackHook."""

    @pytest.fixture
    def hook(self):
        """Create BlackHook instance."""
        return BlackHook(HookConfig())

    @pytest.fixture
    def check_only_hook(self):
        """Create BlackHook in check-only mode."""
        return BlackHook(HookConfig(check_only=True))

    def test_name(self, hook):
        """Test hook name."""
        assert hook.name == "black"

    def test_count_formatted(self, hook):
        """Test formatted file counting."""
        output = "reformatted 3 files"
        count = hook._count_formatted(output, [])
        assert count == 3

    def test_find_unformatted(self, hook):
        """Test finding unformatted files."""
        output = """
would reformat test.py
would reformat service.py
"""
        unformatted = hook._find_unformatted(output)
        assert len(unformatted) == 2
        assert "test.py" in unformatted
        assert "service.py" in unformatted

    @pytest.mark.asyncio
    async def test_run_no_files(self, hook):
        """Test run with no Python files."""
        result = await hook.run([])
        assert result.passed is True
        assert result.files_checked == 0

    @pytest.mark.asyncio
    async def test_run_success(self, hook):
        """Test successful formatting."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "All done!", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_with_formatting(self, hook):
        """Test run when files are formatted."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "reformatted 2 files", "")
            result = await hook.run(["test.py", "service.py"])

            assert result.passed is True
            assert result.auto_fixed == 2

    @pytest.mark.asyncio
    async def test_check_only_mode_pass(self, check_only_hook):
        """Test check-only mode when files are formatted."""
        with patch.object(check_only_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "All done!", "")
            result = await check_only_hook.run(["test.py"])

            assert result.passed is True

    @pytest.mark.asyncio
    async def test_check_only_mode_fail(self, check_only_hook):
        """Test check-only mode when files need formatting."""
        with patch.object(check_only_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (1, "would reformat test.py", "")
            result = await check_only_hook.run(["test.py"])

            assert result.passed is False
            assert result.exit_code == ExitCode.BLOCKING_ERROR

    @pytest.mark.asyncio
    async def test_line_length_config(self, hook):
        """Test line length is passed to black."""
        hook.config.line_length = 120
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            await hook.run(["test.py"])

            call_args = mock_cmd.call_args[0][0]
            assert "--line-length" in call_args
            assert "120" in call_args
