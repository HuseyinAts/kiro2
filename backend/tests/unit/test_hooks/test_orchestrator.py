"""Tests for PostToolUseOrchestrator."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.hooks.models import ExitCode, QualityCheckResult
from backend.hooks.orchestrator import PostToolUseOrchestrator


class TestPostToolUseOrchestrator:
    """Tests for PostToolUseOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return PostToolUseOrchestrator(
            enable_pytest=False,
            enable_docstring=False
        )

    @pytest.fixture
    def full_orchestrator(self):
        """Create orchestrator with all hooks."""
        return PostToolUseOrchestrator()

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.ruff_hook is not None
        assert orchestrator.mypy_hook is not None
        assert orchestrator.black_hook is not None
        assert orchestrator.isort_hook is not None
        assert orchestrator.pytest_hook is None  # Disabled
        assert orchestrator.docstring_hook is None  # Disabled

    def test_full_initialization(self, full_orchestrator):
        """Test full orchestrator initialization."""
        assert full_orchestrator.pytest_hook is not None
        assert full_orchestrator.docstring_hook is not None

    @pytest.mark.asyncio
    async def test_run_all_checks_no_files(self, orchestrator):
        """Test run with no files."""
        with patch.object(orchestrator.file_watcher, 'get_changed_python_files', return_value=[]):
            result = await orchestrator.run_all_checks()
            assert result.total_checks == 0
            assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_all_checks_success(self, orchestrator):
        """Test successful run of all checks."""
        success_result = QualityCheckResult(
            tool="test",
            passed=True,
            exit_code=0,
            execution_time=0.5,
            files_checked=1
        )

        with patch.object(orchestrator.ruff_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_ruff:
            with patch.object(orchestrator.mypy_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_mypy:
                with patch.object(orchestrator.black_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_black:
                    with patch.object(orchestrator.isort_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_isort:
                        mock_ruff.return_value = success_result
                        mock_mypy.return_value = success_result
                        mock_black.return_value = success_result
                        mock_isort.return_value = success_result

                        result = await orchestrator.run_all_checks(["test.py"])

                        assert result.total_checks == 5  # 4 hooks + reward_hacking
                        assert result.passed_checks == 5
                        assert result.all_passed is True
                        assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_all_checks_with_failure(self, orchestrator):
        """Test run when one check fails."""
        success_result = QualityCheckResult(
            tool="test",
            passed=True,
            exit_code=0,
            execution_time=0.5,
            files_checked=1
        )
        failure_result = QualityCheckResult(
            tool="mypy",
            passed=False,
            exit_code=2,
            errors=["Type error"],
            execution_time=1.0,
            files_checked=1
        )

        with patch.object(orchestrator.ruff_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_ruff:
            with patch.object(orchestrator.mypy_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_mypy:
                with patch.object(orchestrator.black_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_black:
                    with patch.object(orchestrator.isort_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_isort:
                        mock_ruff.return_value = success_result
                        mock_mypy.return_value = failure_result
                        mock_black.return_value = success_result
                        mock_isort.return_value = success_result

                        result = await orchestrator.run_all_checks(["test.py"])

                        assert result.total_checks == 5  # 4 hooks + reward_hacking
                        assert result.passed_checks == 4  # 3 + reward_hacking
                        assert result.failed_checks == 1
                        assert result.all_passed is False
                        assert result.exit_code == ExitCode.BLOCKING_ERROR

    @pytest.mark.asyncio
    async def test_run_quick_checks(self, orchestrator):
        """Test quick checks (ruff, black, isort only)."""
        success_result = QualityCheckResult(
            tool="test",
            passed=True,
            exit_code=0,
            execution_time=0.5,
            files_checked=1
        )

        with patch.object(orchestrator.ruff_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_ruff:
            with patch.object(orchestrator.black_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_black:
                with patch.object(orchestrator.isort_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_isort:
                    mock_ruff.return_value = success_result
                    mock_black.return_value = success_result
                    mock_isort.return_value = success_result

                    result = await orchestrator.run_quick_checks(["test.py"])

                    assert result.total_checks == 3
                    assert result.all_passed is True

    def test_format_results_success(self, orchestrator):
        """Test result formatting for success."""
        from backend.hooks.models import AggregatedResult

        result = AggregatedResult()
        result.add_result(QualityCheckResult(
            tool="ruff",
            passed=True,
            exit_code=0,
            execution_time=1.0,
            files_checked=5
        ))

        output = orchestrator.format_results(result)
        assert "[OK]" in output
        assert "ruff" in output
        assert "SUCCESS" in output

    def test_format_results_failure(self, orchestrator):
        """Test result formatting for failure."""
        from backend.hooks.models import AggregatedResult

        result = AggregatedResult()
        result.add_result(QualityCheckResult(
            tool="mypy",
            passed=False,
            exit_code=2,
            errors=["Type error found"],
            execution_time=2.0,
            files_checked=3
        ))

        output = orchestrator.format_results(result)
        assert "[FAIL]" in output
        assert "mypy" in output
        assert "FAILED" in output


class TestOrchestratorExceptionHandling:
    """Tests for exception handling in orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return PostToolUseOrchestrator(
            enable_pytest=False,
            enable_docstring=False
        )

    @pytest.mark.asyncio
    async def test_handle_hook_exception(self, orchestrator):
        """Test handling of hook exceptions."""
        success_result = QualityCheckResult(
            tool="test",
            passed=True,
            exit_code=0,
            execution_time=0.5,
            files_checked=1
        )

        with patch.object(orchestrator.ruff_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_ruff:
            with patch.object(orchestrator.mypy_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_mypy:
                with patch.object(orchestrator.black_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_black:
                    with patch.object(orchestrator.isort_hook, 'run_with_timeout', new_callable=AsyncMock) as mock_isort:
                        mock_ruff.side_effect = Exception("Ruff crashed")
                        mock_mypy.return_value = success_result
                        mock_black.return_value = success_result
                        mock_isort.return_value = success_result

                        result = await orchestrator.run_all_checks(["test.py"])

                        # Should still complete with error captured
                        assert result.total_checks == 5  # 4 hooks + reward_hacking
                        assert result.failed_checks == 1
                        assert result.exit_code == ExitCode.BLOCKING_ERROR
