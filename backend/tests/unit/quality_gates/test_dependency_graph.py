"""
Unit Tests for DependencyGraph
==============================

Tests for topological sorting, circular detection, and execution levels.
"""

from __future__ import annotations

import pytest

from backend.core.quality_gates.dependency_graph import (
    DependencyGraph,
    CircularDependencyError,
    build_gate_graph,
    DEFAULT_GATE_DEPENDENCIES,
)


# =============================================================================
# Test Cases: Basic Operations
# =============================================================================

class TestBasicOperations:
    """Tests for basic graph operations."""

    def test_add_node(self):
        """Add a node to the graph."""
        graph = DependencyGraph()
        graph.add_node("A", {"name": "A"})

        assert "A" in graph.nodes
        assert graph.get_node("A") == {"name": "A"}

    def test_add_multiple_nodes(self):
        """Add multiple nodes."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})

        assert len(graph.nodes) == 3

    def test_add_dependency(self):
        """Add a dependency between nodes."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_dependency("B", "A")  # B depends on A

        deps = graph.get_dependencies("B")
        assert "A" in deps

    def test_get_dependencies_empty(self):
        """Get dependencies for node with no deps."""
        graph = DependencyGraph()
        graph.add_node("A", {})

        deps = graph.get_dependencies("A")
        assert deps == set()

    def test_get_dependents(self):
        """Get nodes that depend on a given node."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")

        dependents = graph.get_dependents("A")
        assert set(dependents) == {"B", "C"}


# =============================================================================
# Test Cases: Topological Sort
# =============================================================================

class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_sort_no_dependencies(self):
        """Sort graph with no dependencies."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})

        sorted_nodes = graph.topological_sort()

        # All nodes should be present
        assert set(sorted_nodes) == {"A", "B", "C"}

    def test_sort_linear_chain(self):
        """Sort linear dependency chain: A -> B -> C."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})
        graph.add_dependency("B", "A")  # B depends on A
        graph.add_dependency("C", "B")  # C depends on B

        sorted_nodes = graph.topological_sort()

        # A must come before B, B must come before C
        assert sorted_nodes.index("A") < sorted_nodes.index("B")
        assert sorted_nodes.index("B") < sorted_nodes.index("C")

    def test_sort_diamond_dependency(self):
        """Sort diamond dependency: A -> B,C -> D."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})
        graph.add_node("D", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")
        graph.add_dependency("D", "B")
        graph.add_dependency("D", "C")

        sorted_nodes = graph.topological_sort()

        # A must be first
        assert sorted_nodes.index("A") < sorted_nodes.index("B")
        assert sorted_nodes.index("A") < sorted_nodes.index("C")
        # D must be last
        assert sorted_nodes.index("D") > sorted_nodes.index("B")
        assert sorted_nodes.index("D") > sorted_nodes.index("C")

    def test_sort_empty_graph(self):
        """Sort empty graph."""
        graph = DependencyGraph()
        sorted_nodes = graph.topological_sort()

        assert sorted_nodes == []


# =============================================================================
# Test Cases: Circular Dependency Detection
# =============================================================================

class TestCircularDetection:
    """Tests for circular dependency detection."""

    def test_no_circular_dependency(self):
        """Graph without circular dependencies."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_dependency("B", "A")

        cycle = graph.detect_circular()
        assert cycle is None

    def test_simple_circular_dependency(self):
        """Detect simple circular dependency: A -> B -> A."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("A", "B")

        cycle = graph.detect_circular()
        assert cycle is not None
        assert len(cycle) > 0

    def test_self_dependency(self):
        """Detect self-dependency: A -> A."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_dependency("A", "A")

        cycle = graph.detect_circular()
        assert cycle is not None

    def test_long_circular_chain(self):
        """Detect circular dependency in long chain."""
        graph = DependencyGraph()
        for node in ["A", "B", "C", "D"]:
            graph.add_node(node, {})

        graph.add_dependency("B", "A")
        graph.add_dependency("C", "B")
        graph.add_dependency("D", "C")
        graph.add_dependency("A", "D")  # Creates cycle

        cycle = graph.detect_circular()
        assert cycle is not None

    def test_topological_sort_raises_on_cycle(self):
        """Topological sort should raise on circular dependency."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("A", "B")

        with pytest.raises(CircularDependencyError):
            graph.topological_sort()


# =============================================================================
# Test Cases: Execution Levels
# =============================================================================

class TestExecutionLevels:
    """Tests for parallel execution levels."""

    def test_single_level(self):
        """All independent nodes at level 0."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})

        levels = graph.get_execution_levels()

        assert len(levels) == 1
        assert set(levels[0].gates) == {"A", "B", "C"}
        assert levels[0].level == 0

    def test_two_levels(self):
        """Two execution levels."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")

        levels = graph.get_execution_levels()

        assert len(levels) == 2
        # Level 0: A
        assert "A" in levels[0].gates
        # Level 1: B, C
        assert set(levels[1].gates) == {"B", "C"}

    def test_three_levels(self):
        """Three execution levels."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_node("C", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "B")

        levels = graph.get_execution_levels()

        assert len(levels) == 3
        assert levels[0].gates == ["A"]
        assert levels[1].gates == ["B"]
        assert levels[2].gates == ["C"]

    def test_complex_levels(self):
        """Complex dependency graph."""
        graph = DependencyGraph()
        for node in ["A", "B", "C", "D", "E"]:
            graph.add_node(node, {})

        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")
        graph.add_dependency("D", "B")
        graph.add_dependency("D", "C")
        graph.add_dependency("E", "D")

        levels = graph.get_execution_levels()

        # Level 0: A
        # Level 1: B, C
        # Level 2: D
        # Level 3: E
        assert len(levels) == 4


# =============================================================================
# Test Cases: Build Gate Graph
# =============================================================================

class TestBuildGateGraph:
    """Tests for build_gate_graph factory."""

    def test_build_default_graph(self):
        """Build graph with default dependencies."""
        # Build gates dict from DEFAULT_GATE_DEPENDENCIES
        gates = {
            name: {"depends_on": deps}
            for name, deps in DEFAULT_GATE_DEPENDENCIES.items()
        }
        graph = build_gate_graph(gates)

        # Should have all gates
        assert "code_quality" in graph.nodes
        assert "test_coverage" in graph.nodes
        assert "security" in graph.nodes

    def test_build_with_custom_deps(self):
        """Build graph with custom dependencies."""
        gates = {
            "gate_a": {"depends_on": []},
            "gate_b": {"depends_on": ["gate_a"]},
        }
        graph = build_gate_graph(gates)

        assert "gate_a" in graph.nodes
        assert "gate_b" in graph.nodes
        assert "gate_a" in graph.get_dependencies("gate_b")

    def test_default_dependencies_structure(self):
        """Verify default dependencies are valid."""
        # code_quality has no deps
        assert DEFAULT_GATE_DEPENDENCIES.get("code_quality", []) == []

        # test_coverage depends on code_quality
        assert "code_quality" in DEFAULT_GATE_DEPENDENCIES.get("test_coverage", [])


# =============================================================================
# Test Cases: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_get_nonexistent_node(self):
        """Get data for nonexistent node."""
        graph = DependencyGraph()
        data = graph.get_node("nonexistent")

        assert data is None

    def test_dependency_on_nonexistent_node(self):
        """Add dependency to nonexistent node."""
        graph = DependencyGraph()
        graph.add_node("A", {})

        # Should raise ValueError for nonexistent dependency
        with pytest.raises(ValueError, match="not found in graph"):
            graph.add_dependency("A", "nonexistent")

    def test_duplicate_dependency(self):
        """Adding same dependency twice."""
        graph = DependencyGraph()
        graph.add_node("A", {})
        graph.add_node("B", {})
        graph.add_dependency("B", "A")
        graph.add_dependency("B", "A")  # Duplicate

        deps = graph.get_dependencies("B")
        # Should only have one "A" (set deduplicates)
        assert len(deps) == 1
        assert "A" in deps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
