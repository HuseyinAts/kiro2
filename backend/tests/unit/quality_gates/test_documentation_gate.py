"""
Unit Tests for DocumentationGate
================================

Tests for README, API docs, and docstring coverage.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity
from backend.core.quality_gates.gates.documentation import DocumentationGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> DocumentationGate:
    """Create DocumentationGate instance."""
    return DocumentationGate()


@pytest.fixture
def context(tmp_path: Path, gate: DocumentationGate) -> GateContext:
    """Create gate context with sample files."""
    # Create README
    (tmp_path / "README.md").write_text(
        "# Project\n\n## Description\n\nTest project.\n\n## Installation\n\n## Usage\n\n"
    )

    return GateContext(
        working_dir=tmp_path,
        config=gate.get_default_config(),
        commit_hash="abc123",
        branch="main",
        changed_files=[],
        previous_result=None,
        extra={},
    )


# =============================================================================
# Test Cases: Configuration
# =============================================================================

class TestConfiguration:
    """Tests for gate configuration."""

    def test_get_name(self, gate: DocumentationGate):
        """Gate name should be 'documentation'."""
        assert gate.get_name() == "documentation"

    def test_default_config_non_blocking(self, gate: DocumentationGate):
        """Documentation should be non-blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is False

    def test_dependencies(self, gate: DocumentationGate):
        """Should depend on code_quality."""
        deps = gate.get_dependencies()

        assert "code_quality" in deps


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked checks."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: DocumentationGate, context: GateContext):
        """Execute with good documentation."""
        with patch.object(gate, "_check_readme", new_callable=AsyncMock) as mock_readme, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_api_docs", new_callable=AsyncMock) as mock_api, \
             patch.object(gate, "_check_examples", new_callable=AsyncMock) as mock_examples:

            mock_readme.return_value = {
                "score": 9.0,
                "issues": [],
            }
            mock_docs.return_value = {
                "score": 8.0,
                "coverage": 80.0,
                "total": 100,
                "documented": 80,
                "issues": [],
            }
            mock_api.return_value = {
                "score": 9.0,
                "issues": [],
            }
            mock_examples.return_value = {
                "score": 10.0,
                "issues": [],
            }

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_missing_readme(
        self, gate: DocumentationGate, context: GateContext
    ):
        """Execute with missing README."""
        with patch.object(gate, "_check_readme", new_callable=AsyncMock) as mock_readme, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_api_docs", new_callable=AsyncMock) as mock_api, \
             patch.object(gate, "_check_examples", new_callable=AsyncMock) as mock_examples:

            mock_readme.return_value = {
                "score": 0.0,
                "issues": [
                    gate.create_issue(
                        file="README",
                        rule="NO_README",
                        message="README file not found",
                        severity=GateSeverity.HIGH,
                    )
                ],
            }
            mock_docs.return_value = {"score": 8.0, "coverage": 80.0, "issues": []}
            mock_api.return_value = {"score": 9.0, "issues": []}
            mock_examples.return_value = {"score": 10.0, "issues": []}

            result = await gate.execute(context)

            assert len(result.issues) > 0
            assert any("readme" in str(i.message).lower() for i in result.issues)

    @pytest.mark.asyncio
    async def test_execute_low_docstring_coverage(
        self, gate: DocumentationGate, context: GateContext
    ):
        """Execute with low docstring coverage."""
        with patch.object(gate, "_check_readme", new_callable=AsyncMock) as mock_readme, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_api_docs", new_callable=AsyncMock) as mock_api, \
             patch.object(gate, "_check_examples", new_callable=AsyncMock) as mock_examples:

            mock_readme.return_value = {"score": 8.0, "issues": []}
            mock_docs.return_value = {
                "score": 3.0,
                "coverage": 30.0,
                "total": 100,
                "documented": 30,
                "issues": [
                    gate.create_issue(
                        file=".",
                        rule="LOW_DOCSTRING_COVERAGE",
                        message="Docstring coverage 30.0% below minimum 70%",
                        severity=GateSeverity.MEDIUM,
                    )
                ],
            }
            mock_api.return_value = {"score": 9.0, "issues": []}
            mock_examples.return_value = {"score": 10.0, "issues": []}

            result = await gate.execute(context)

            assert result.score < 10.0


# =============================================================================
# Test Cases: README Checks
# =============================================================================

class TestReadmeChecks:
    """Tests for README completeness checks."""

    @pytest.mark.asyncio
    async def test_check_readme_exists(self, gate: DocumentationGate, tmp_path: Path):
        """Check README exists."""
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n## Description\n\nTest project description.\n\n"
            "## Installation\n\n```pip install project```\n\n"
            "## Usage\n\n```python\nimport project\n```\n" * 20
        )

        result = await gate._check_readme(
            tmp_path,
            min_length=100,
            required_sections=["installation", "usage"],
        )

        assert result["score"] > 0
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_check_readme_missing(self, gate: DocumentationGate, tmp_path: Path):
        """Check missing README."""
        result = await gate._check_readme(
            tmp_path,
            min_length=100,
            required_sections=[],
        )

        assert result["score"] == 0.0
        assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_check_readme_too_short(self, gate: DocumentationGate, tmp_path: Path):
        """Check too short README."""
        readme = tmp_path / "README.md"
        readme.write_text("# Short readme")

        result = await gate._check_readme(
            tmp_path,
            min_length=500,
            required_sections=[],
        )

        assert result["score"] < 10.0


# =============================================================================
# Test Cases: Docstring Coverage
# =============================================================================

class TestDocstringCoverage:
    """Tests for docstring coverage checks."""

    @pytest.mark.asyncio
    async def test_check_docstrings_high_coverage(self, gate: DocumentationGate, tmp_path: Path):
        """Check high docstring coverage."""
        # Create file with documented functions
        test_file = tmp_path / "module.py"
        test_file.write_text('''
"""Module docstring."""

def func1():
    """Function 1 docstring."""
    pass

def func2():
    """Function 2 docstring."""
    pass

class MyClass:
    """Class docstring."""
    pass
''')

        result = await gate._check_docstrings(tmp_path, min_coverage=70)

        assert "coverage" in result
        assert result["coverage"] >= 70

    @pytest.mark.asyncio
    async def test_check_docstrings_low_coverage(self, gate: DocumentationGate, tmp_path: Path):
        """Check low docstring coverage."""
        # Create file with undocumented functions
        test_file = tmp_path / "module.py"
        test_file.write_text('''
def func1():
    pass

def func2():
    pass

def func3():
    pass

class MyClass:
    pass
''')

        result = await gate._check_docstrings(tmp_path, min_coverage=70)

        assert result["coverage"] < 70
        assert len(result["issues"]) > 0


# =============================================================================
# Test Cases: Non-Blocking Behavior
# =============================================================================

class TestNonBlockingBehavior:
    """Tests for non-blocking behavior."""

    def test_gate_is_advisory(self, gate: DocumentationGate):
        """Documentation gate should be advisory (non-blocking)."""
        assert gate.is_blocking() is False

    @pytest.mark.asyncio
    async def test_low_score_does_not_fail_pipeline(
        self, gate: DocumentationGate, context: GateContext
    ):
        """Low documentation score should not fail pipeline."""
        with patch.object(gate, "_check_readme", new_callable=AsyncMock) as mock_readme, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_api_docs", new_callable=AsyncMock) as mock_api, \
             patch.object(gate, "_check_examples", new_callable=AsyncMock) as mock_examples:

            mock_readme.return_value = {"score": 0.0, "issues": []}
            mock_docs.return_value = {"score": 0.0, "coverage": 0.0, "issues": []}
            mock_api.return_value = {"score": 0.0, "issues": []}
            mock_examples.return_value = {"score": 0.0, "issues": []}

            result = await gate.execute(context)

            # Even with score 0, it should not be blocking
            assert result.blocking is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
