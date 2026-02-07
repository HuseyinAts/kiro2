"""Tests for PytestHook."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.hooks.pytest_hook import PytestHook
from backend.hooks.models import HookConfig, ExitCode


class TestPytestHook:
    """Tests for PytestHook."""

    @pytest.fixture
    def hook(self):
        """Create PytestHook instance."""
        return PytestHook(HookConfig())

    def test_name(self, hook):
        """Test hook name."""
        assert hook.name == "pytest"

    def test_get_test_candidates(self, hook):
        """Test test file candidates generation."""
        source_path = Path("/project/backend/services/user_service.py")
        candidates = hook._get_test_candidates(source_path)

        # Should include test_user_service.py patterns
        assert any("test_user_service.py" in str(c) for c in candidates)

    def test_parse_failures(self, hook):
        """Test failure parsing."""
        output = """
FAILED test_user.py::test_create_user
FAILED test_auth.py::test_login
"""
        failures = hook._parse_failures(output)
        assert len(failures) == 2
        assert "test_create_user" in failures[0].test_name
        assert "test_login" in failures[1].test_name

    def test_parse_errors(self, hook):
        """Test error parsing."""
        output = """
ERROR test_user.py::test_setup
"""
        errors = hook._parse_errors(output)
        assert len(errors) == 1
        assert "test_setup" in errors[0].test_name

    @pytest.mark.asyncio
    async def test_run_no_files(self, hook):
        """Test run with no Python files."""
        result = await hook.run([])
        assert result.passed is True
        assert result.files_checked == 0

    @pytest.mark.asyncio
    async def test_run_no_tests_found(self, hook):
        """Test run when no test files are found."""
        with patch.object(hook, '_find_related_tests', return_value=[]):
            result = await hook.run(["service.py"])

            assert result.passed is True
            assert len(result.warnings) > 0
            assert "No related test files" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_run_tests_pass(self, hook):
        """Test run when all tests pass."""
        with patch.object(hook, '_find_related_tests', return_value=["test_service.py"]):
            with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
                mock_cmd.return_value = (0, "1 passed", "")
                result = await hook.run(["service.py"])

                assert result.passed is True
                assert result.exit_code == ExitCode.SUCCESS

    @pytest.mark.asyncio
    async def test_run_tests_fail(self, hook):
        """Test run when tests fail."""
        failure_output = "FAILED test_service.py::test_create"
        with patch.object(hook, '_find_related_tests', return_value=["test_service.py"]):
            with patch.object(hook, '_run_command', new_callable=AsyncMock) as mock_cmd:
                mock_cmd.return_value = (1, failure_output, "")
                result = await hook.run(["service.py"])

                assert result.passed is False
                assert result.exit_code == ExitCode.BLOCKING_ERROR


class TestTestFileFinding:
    """Tests for test file finding logic."""

    @pytest.fixture
    def hook(self):
        """Create PytestHook instance."""
        return PytestHook(HookConfig())

    def test_test_file_is_included(self, hook):
        """Test that test files themselves are included."""
        files = ["test_user.py", "service.py"]
        with patch.object(Path, 'exists', return_value=False):
            # Test files should be included directly
            test_files = hook._find_related_tests(files)
            assert "test_user.py" in test_files

    def test_source_to_test_mapping(self, hook, tmp_path):
        """Test source file to test file mapping."""
        # Create test file
        test_file = tmp_path / "test_service.py"
        test_file.write_text("def test_something(): pass")

        source_file = tmp_path / "service.py"
        source_file.write_text("def something(): pass")

        # Mock the candidates to include our temp path
        with patch.object(hook, '_get_test_candidates') as mock_candidates:
            mock_candidates.return_value = [test_file]
            test_files = hook._find_related_tests([str(source_file)])
            assert str(test_file) in test_files
