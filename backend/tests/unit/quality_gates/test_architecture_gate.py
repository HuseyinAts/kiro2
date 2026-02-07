"""
Unit Tests for ArchitectureGate
===============================

Tests for import analysis, coupling metrics, and layer separation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity
from backend.core.quality_gates.gates.architecture import ArchitectureGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> ArchitectureGate:
    """Create ArchitectureGate instance."""
    return ArchitectureGate()


@pytest.fixture
def context(tmp_path: Path, gate: ArchitectureGate) -> GateContext:
    """Create gate context."""
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

    def test_get_name(self, gate: ArchitectureGate):
        """Gate name should be 'architecture'."""
        assert gate.get_name() == "architecture"

    def test_default_config_blocking(self, gate: ArchitectureGate):
        """Architecture should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_dependencies(self, gate: ArchitectureGate):
        """Should depend on code_quality."""
        deps = gate.get_dependencies()

        assert "code_quality" in deps

    def test_default_config_has_layers(self, gate: ArchitectureGate):
        """Default config should define layers."""
        config = gate.get_default_config()
        layers = config.tool_config.get("layers", [])

        assert len(layers) > 0
        assert "api" in layers


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked checks."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: ArchitectureGate, context: GateContext):
        """Execute with good architecture."""
        with patch.object(gate, "_check_import_directions", new_callable=AsyncMock) as mock_imports, \
             patch.object(gate, "_detect_circular_deps", new_callable=AsyncMock) as mock_circular, \
             patch.object(gate, "_validate_layers", new_callable=AsyncMock) as mock_layers, \
             patch.object(gate, "_calculate_metrics", new_callable=AsyncMock) as mock_metrics:

            mock_imports.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_circular.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_layers.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_metrics.return_value = {
                "coupling": 0.3,
                "cohesion": 0.8,
                "coupling_score": 7.0,
                "cohesion_score": 8.0,
            }

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_import_violations(
        self, gate: ArchitectureGate, context: GateContext
    ):
        """Execute with import violations."""
        with patch.object(gate, "_check_import_directions", new_callable=AsyncMock) as mock_imports, \
             patch.object(gate, "_detect_circular_deps", new_callable=AsyncMock) as mock_circular, \
             patch.object(gate, "_validate_layers", new_callable=AsyncMock) as mock_layers, \
             patch.object(gate, "_calculate_metrics", new_callable=AsyncMock) as mock_metrics:

            mock_imports.return_value = {
                "score": 4.0,
                "issues": [
                    gate.create_issue(
                        file="api/routes.py",
                        rule="IMPORT_DIRECTION",
                        message="Invalid import: api.routes -> models",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
                "count": 3,
            }
            mock_circular.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_layers.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_metrics.return_value = {
                "coupling": 0.3, "cohesion": 0.8,
                "coupling_score": 7.0, "cohesion_score": 8.0,
            }

            result = await gate.execute(context)

            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_circular_dependency(
        self, gate: ArchitectureGate, context: GateContext
    ):
        """Execute with circular dependencies."""
        with patch.object(gate, "_check_import_directions", new_callable=AsyncMock) as mock_imports, \
             patch.object(gate, "_detect_circular_deps", new_callable=AsyncMock) as mock_circular, \
             patch.object(gate, "_validate_layers", new_callable=AsyncMock) as mock_layers, \
             patch.object(gate, "_calculate_metrics", new_callable=AsyncMock) as mock_metrics:

            mock_imports.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_circular.return_value = {
                "score": 7.0,
                "issues": [
                    gate.create_issue(
                        file="module_a",
                        rule="CIRCULAR_IMPORT",
                        message="Circular dependency: module_a -> module_b -> module_a",
                        severity=GateSeverity.HIGH,
                    ),
                ],
                "count": 1,
            }
            mock_layers.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_metrics.return_value = {
                "coupling": 0.3, "cohesion": 0.8,
                "coupling_score": 7.0, "cohesion_score": 8.0,
            }

            result = await gate.execute(context)

            assert any("circular" in str(i.message).lower() for i in result.issues)

    @pytest.mark.asyncio
    async def test_execute_high_coupling(self, gate: ArchitectureGate, context: GateContext):
        """Execute with high coupling."""
        with patch.object(gate, "_check_import_directions", new_callable=AsyncMock) as mock_imports, \
             patch.object(gate, "_detect_circular_deps", new_callable=AsyncMock) as mock_circular, \
             patch.object(gate, "_validate_layers", new_callable=AsyncMock) as mock_layers, \
             patch.object(gate, "_calculate_metrics", new_callable=AsyncMock) as mock_metrics:

            mock_imports.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_circular.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_layers.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_metrics.return_value = {
                "coupling": 0.9,  # High coupling
                "cohesion": 0.2,  # Low cohesion
                "coupling_score": 1.0,
                "cohesion_score": 2.0,
            }

            result = await gate.execute(context)

            # Score should be reduced due to poor metrics
            assert result.score < 10.0


# =============================================================================
# Test Cases: Internal Methods
# =============================================================================

class TestInternalMethods:
    """Tests for internal helper methods."""

    def test_get_module_name(self, gate: ArchitectureGate, tmp_path: Path):
        """Convert file path to module name."""
        # Create test file
        (tmp_path / "services").mkdir()
        test_file = tmp_path / "services" / "user_service.py"
        test_file.write_text("# test")

        module_name = gate._get_module_name(test_file, tmp_path)

        assert module_name == "services.user_service"

    def test_get_module_name_init(self, gate: ArchitectureGate, tmp_path: Path):
        """Convert __init__.py to package name."""
        (tmp_path / "services").mkdir()
        init_file = tmp_path / "services" / "__init__.py"
        init_file.write_text("")

        module_name = gate._get_module_name(init_file, tmp_path)

        assert module_name == "services"

    def test_extract_imports(self, gate: ArchitectureGate, tmp_path: Path):
        """Extract imports from Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Optional
""")

        imports = gate._extract_imports(test_file)

        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports

    def test_extract_definitions(self, gate: ArchitectureGate):
        """Extract function and class definitions."""
        content = '''
def my_function():
    pass

class MyClass:
    def method(self):
        pass

async def async_func():
    pass
'''

        definitions = gate._extract_definitions(content)

        assert "my_function" in definitions
        assert "MyClass" in definitions
        assert "async_func" in definitions

    def test_find_cycles_no_cycle(self, gate: ArchitectureGate):
        """Find cycles in acyclic graph."""
        graph = {
            "a": {"b"},
            "b": {"c"},
            "c": set(),
        }

        cycles = gate._find_cycles(graph)

        assert len(cycles) == 0

    def test_find_cycles_with_cycle(self, gate: ArchitectureGate):
        """Find cycles in cyclic graph."""
        graph = {
            "a": {"b"},
            "b": {"c"},
            "c": {"a"},  # Creates cycle
        }

        cycles = gate._find_cycles(graph)

        assert len(cycles) > 0


# =============================================================================
# Test Cases: Real File Analysis
# =============================================================================

class TestRealFileAnalysis:
    """Tests with actual Python files."""

    @pytest.mark.asyncio
    async def test_check_import_directions(self, gate: ArchitectureGate, tmp_path: Path):
        """Check import directions on real files."""
        # Create a test file
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "routes.py").write_text("import json\n")

        result = await gate._check_import_directions(tmp_path)

        # Should return a dict with score
        assert "score" in result
        assert isinstance(result["score"], (int, float))

    @pytest.mark.asyncio
    async def test_detect_circular_deps(self, gate: ArchitectureGate, tmp_path: Path):
        """Detect circular dependencies."""
        # Create test files without circular deps
        (tmp_path / "module_a.py").write_text("import json\n")
        (tmp_path / "module_b.py").write_text("import os\n")

        result = await gate._detect_circular_deps(tmp_path)

        assert "score" in result
        assert "count" in result
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_calculate_metrics(self, gate: ArchitectureGate, tmp_path: Path):
        """Calculate coupling and cohesion metrics."""
        # Create test files
        (tmp_path / "module_a.py").write_text("import json\ndef func(): pass\n")
        (tmp_path / "module_b.py").write_text("import os\nclass Cls: pass\n")

        result = await gate._calculate_metrics(tmp_path)

        assert "coupling" in result
        assert "cohesion" in result
        assert 0 <= result["coupling"] <= 1
        assert 0 <= result["cohesion"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
