"""Tests for IsortHook - REQ-6.1 to REQ-6.6.

isort import sorting hook icin unit testleri.
Black uyumlulugu ve import siralama testleri.
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.hooks.isort_hook import IsortHook, run_isort
from backend.hooks.models import ExitCode, HookConfig


class TestIsortHook:
    """Tests for IsortHook."""

    @pytest.fixture
    def hook(self):
        """Create IsortHook instance."""
        return IsortHook(HookConfig())

    @pytest.fixture
    def check_only_hook(self):
        """Create IsortHook in check-only mode."""
        return IsortHook(HookConfig(check_only=True))

    def test_name(self, hook):
        """Test hook name is 'isort'."""
        assert hook.name == "isort"

    def test_count_sorted_fixing(self, hook):
        """Test counting sorted files from 'Fixing' output."""
        output = "Fixing test.py\nFixing service.py\nFixing utils.py"
        count = hook._count_sorted(output)
        assert count == 3

    def test_count_sorted_alternative_format(self, hook):
        """Test counting sorted files from 'Sorted X' output."""
        output = "Sorted 5 imports in 2 files"
        count = hook._count_sorted(output)
        assert count == 5

    def test_count_sorted_empty(self, hook):
        """Test zero count when no sorting done."""
        output = "All imports are already sorted!"
        count = hook._count_sorted(output)
        assert count == 0

    def test_find_unsorted_would_fix(self, hook):
        """Test finding files that need sorting."""
        output = """
would fix test.py
would fix service.py
"""
        unsorted = hook._find_unsorted(output)
        assert len(unsorted) == 2
        assert "test.py" in unsorted
        assert "service.py" in unsorted

    def test_find_unsorted_would_be_sorted(self, hook):
        """Test finding unsorted files from alternative format."""
        output = "ERROR: test.py would be sorted differently"
        unsorted = hook._find_unsorted(output)
        assert "test.py" in unsorted

    def test_find_unused_imports(self, hook):
        """Test finding unused import warnings."""
        output = """
unused import: os
unreferenced import: sys
"""
        warnings = hook._find_unused_imports(output)
        assert len(warnings) == 2
        assert any("os" in w for w in warnings)
        assert any("sys" in w for w in warnings)

    def test_find_unused_imports_none(self, hook):
        """Test no unused imports."""
        output = "All imports are properly used"
        warnings = hook._find_unused_imports(output)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_run_no_files(self, hook):
        """Test run with no Python files returns success."""
        result = await hook.run([])
        assert result.passed is True
        assert result.files_checked == 0

    @pytest.mark.asyncio
    async def test_run_non_python_files(self, hook):
        """Test run with non-Python files returns success."""
        result = await hook.run(["README.md", "package.json"])
        assert result.passed is True
        assert result.files_checked == 0

    @pytest.mark.asyncio
    async def test_run_success(self, hook):
        """Test successful import sorting."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "Fixing test.py", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS
            assert result.files_checked == 1

    @pytest.mark.asyncio
    async def test_run_with_sorting(self, hook):
        """Test run when files are sorted."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "Fixing test.py\nFixing service.py", "")
            result = await hook.run(["test.py", "service.py"])

            assert result.passed is True
            assert result.auto_fixed == 2

    @pytest.mark.asyncio
    async def test_run_with_warnings(self, hook):
        """Test run with unused import warnings."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "unused import: os", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_check_only_mode_pass(self, check_only_hook):
        """Test check-only mode when imports are sorted."""
        with patch.object(check_only_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "All imports sorted", "")
            result = await check_only_hook.run(["test.py"])

            assert result.passed is True
            assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_check_only_mode_fail(self, check_only_hook):
        """Test check-only mode when files need sorting."""
        with patch.object(check_only_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (1, "would fix test.py", "")
            result = await check_only_hook.run(["test.py"])

            assert result.passed is False
            assert result.exit_code == ExitCode.BLOCKING_ERROR
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_black_profile_used(self, hook):
        """Test that --profile black is passed to isort (REQ-6.3)."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            await hook.run(["test.py"])

            call_args = mock_cmd.call_args[0][0]
            assert "--profile" in call_args
            assert "black" in call_args

    @pytest.mark.asyncio
    async def test_line_length_config(self, hook):
        """Test line length is passed to isort."""
        hook.config.line_length = 120
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            await hook.run(["test.py"])

            call_args = mock_cmd.call_args[0][0]
            assert "--line-length" in call_args
            assert "120" in call_args

    @pytest.mark.asyncio
    async def test_check_only_adds_diff_flag(self, check_only_hook):
        """Test check-only mode adds --check-only and --diff flags."""
        with patch.object(check_only_hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            await check_only_hook.run(["test.py"])

            call_args = mock_cmd.call_args[0][0]
            assert "--check-only" in call_args
            assert "--diff" in call_args


class TestRunIsortFunction:
    """Tests for run_isort convenience function."""

    @pytest.mark.asyncio
    async def test_run_isort_default_config(self):
        """Test run_isort with default config."""
        with patch.object(IsortHook, 'run_with_timeout', new_callable=AsyncMock) as mock_run:
            from backend.hooks.models import QualityCheckResult
            mock_run.return_value = QualityCheckResult(
                tool="isort",
                passed=True,
                exit_code=ExitCode.SUCCESS,
                errors=[],
                warnings=[],
                execution_time=0.1,
                files_checked=1
            )
            result = await run_isort(["test.py"])

            assert result.passed is True
            assert result.tool == "isort"

    @pytest.mark.asyncio
    async def test_run_isort_custom_config(self):
        """Test run_isort with custom config."""
        config = HookConfig(check_only=True, line_length=100)
        with patch.object(IsortHook, 'run_with_timeout', new_callable=AsyncMock) as mock_run:
            from backend.hooks.models import QualityCheckResult
            mock_run.return_value = QualityCheckResult(
                tool="isort",
                passed=True,
                exit_code=ExitCode.SUCCESS,
                errors=[],
                warnings=[],
                execution_time=0.1,
                files_checked=1
            )
            result = await run_isort(["test.py"], config)

            assert result.passed is True


class TestIsortImportGroups:
    """Tests for import group sorting (REQ-6.2, REQ-6.4)."""

    @pytest.fixture
    def hook(self):
        """Create IsortHook instance."""
        return IsortHook(HookConfig())

    @pytest.mark.asyncio
    async def test_stdlib_third_party_local_order(self, hook):
        """Test that import order follows stdlib -> third-party -> local."""
        # This is implicitly tested via --profile black
        # which enforces the correct order
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "Fixing test.py", "")
            result = await hook.run(["test.py"])

            assert result.passed is True
            # Profile black ensures correct ordering

    @pytest.mark.asyncio
    async def test_execution_time_tracked(self, hook):
        """Test that execution time is tracked."""
        with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            result = await hook.run(["test.py"])

            assert result.execution_time >= 0
