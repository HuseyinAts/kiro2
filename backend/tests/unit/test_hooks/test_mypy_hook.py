"""Tests for MypyHook."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.hooks.models import ExitCode, HookConfig
from backend.hooks.mypy_hook import MypyHook


class TestMypyHook:
    """Tests for MypyHook."""

    @pytest.fixture
    def hook(self):
        """Create MypyHook instance."""
        return MypyHook(HookConfig())

    @pytest.fixture
    def strict_hook(self):
        """Create MypyHook with strict mode."""
        return MypyHook(HookConfig(strict_mode=True))

    def test_name(self, hook):
        """Test hook name."""
        assert hook.name == "mypy"

    def test_parse_output(self, hook):
        """Test output parsing."""
        output = """
test.py:10:5: error: Incompatible return value type [return-value]
test.py:15:1: error: Missing return statement [return]
"""
        errors = hook._parse_output(output)
        assert len(errors) == 2
        assert errors[0].line == 10
        assert errors[0].error_code == "return-value"

    def test_extract_types(self, hook):
        """Test type extraction from message."""
        message = 'Incompatible return value type (got "str", expected "int")'
        expected, actual = hook._extract_types(message)
        assert expected == "int"
        assert actual == "str"

    def test_extract_types_no_match(self, hook):
        """Test type extraction with no type info."""
        message = "Missing return statement"
        expected, actual = hook._extract_types(message)
        assert expected is None
        assert actual is None

    def test_find_missing_hints(self, hook):
        """Test finding missing type hints."""
        output = """
test.py:10: error: Function is missing a type annotation
test.py:20: note: Some note
"""
        warnings = hook._find_missing_hints(output)
        assert len(warnings) == 1
        assert "Missing type hint" in warnings[0]

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
            mock_cmd.return_value = (0, "Success: no issues found", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_with_type_errors(self, hook):
        """Test run with type errors."""
        error_output = "test.py:10:5: error: Incompatible return value type [return-value]"
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (1, error_output, "")
            result = await hook.run(["test.py"])

            assert result.passed is False
            assert result.exit_code == ExitCode.BLOCKING_ERROR
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_strict_mode(self, strict_hook):
        """Test strict mode adds --strict flag."""
        with patch.object(strict_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            await strict_hook.run(["test.py"])

            # Check that --strict was in the command
            call_args = mock_cmd.call_args[0][0]
            assert "--strict" in call_args
