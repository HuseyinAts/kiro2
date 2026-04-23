"""
Quality Gates Dependency Graph
==============================

Topological sort and parallel execution level calculation.
Handles gate dependencies and circular detection.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


class CircularDependencyError(Exception):
    """Raised when circular dependency detected."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


@dataclass
class ExecutionLevel:
    """Gates that can run in parallel at same level."""

    level: int
    gates: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.gates)


class DependencyGraph(Generic[T]):
    """
    Dependency graph for gate execution ordering.

    Supports:
    - Topological sort for execution order
    - Parallel execution levels
    - Circular dependency detection
    - Transitive dependency resolution
    """

    def __init__(self) -> None:
        self._nodes: dict[str, T] = {}
        self._edges: dict[str, set[str]] = defaultdict(set)  # node -> dependencies
        self._reverse_edges: dict[str, set[str]] = defaultdict(set)  # node -> dependents

    def add_node(self, name: str, data: T) -> None:
        """Add a node to the graph."""
        self._nodes[name] = data
        if name not in self._edges:
            self._edges[name] = set()
        if name not in self._reverse_edges:
            self._reverse_edges[name] = set()

    def add_dependency(self, node: str, depends_on: str) -> None:
        """Add dependency: node depends on depends_on."""
        if node not in self._nodes:
            raise ValueError(f"Node '{node}' not found in graph")
        if depends_on not in self._nodes:
            raise ValueError(f"Dependency '{depends_on}' not found in graph")

        self._edges[node].add(depends_on)
        self._reverse_edges[depends_on].add(node)

    def get_dependencies(self, node: str) -> set[str]:
        """Get direct dependencies of a node."""
        return self._edges.get(node, set()).copy()

    def get_dependents(self, node: str) -> set[str]:
        """Get nodes that depend on this node."""
        return self._reverse_edges.get(node, set()).copy()

    def get_all_dependencies(self, node: str) -> set[str]:
        """Get all transitive dependencies of a node."""
        result: set[str] = set()
        stack = list(self._edges.get(node, set()))

        while stack:
            dep = stack.pop()
            if dep not in result:
                result.add(dep)
                stack.extend(self._edges.get(dep, set()))

        return result

    def detect_circular(self) -> list[str] | None:
        """
        Detect circular dependencies using DFS.

        Returns:
            List of nodes forming cycle, or None if no cycle.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(self._nodes, WHITE)
        parent: dict[str, str | None] = dict.fromkeys(self._nodes)

        def dfs(node: str) -> list[str] | None:
            color[node] = GRAY
            for dep in self._edges[node]:
                if color[dep] == GRAY:
                    # Found cycle - reconstruct it
                    cycle = [dep, node]
                    current = node
                    while parent[current] and parent[current] != dep:
                        current = parent[current]
                        cycle.append(current)
                    cycle.append(dep)
                    return list(reversed(cycle))
                elif color[dep] == WHITE:
                    parent[dep] = node
                    result = dfs(dep)
                    if result:
                        return result
            color[node] = BLACK
            return None

        for node in self._nodes:
            if color[node] == WHITE:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def topological_sort(self) -> list[str]:
        """
        Return nodes in topological order (dependencies first).

        Raises:
            CircularDependencyError: If circular dependency exists.
        """
        cycle = self.detect_circular()
        if cycle:
            raise CircularDependencyError(cycle)

        in_degree: dict[str, int] = dict.fromkeys(self._nodes, 0)
        for node in self._nodes:
            for dep in self._edges[node]:
                in_degree[node] += 1

        # Start with nodes that have no dependencies
        queue = [n for n, d in in_degree.items() if d == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree of dependents
            for dependent in self._reverse_edges[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def get_execution_levels(self) -> list[ExecutionLevel]:
        """
        Get execution levels for parallel execution.

        Nodes at same level have no dependencies on each other.
        Level N nodes only depend on nodes from levels < N.

        Returns:
            List of ExecutionLevel objects.
        """
        cycle = self.detect_circular()
        if cycle:
            raise CircularDependencyError(cycle)

        levels: list[ExecutionLevel] = []
        remaining = set(self._nodes.keys())
        completed: set[str] = set()
        level_num = 0

        while remaining:
            # Find nodes whose dependencies are all completed
            ready = []
            for node in remaining:
                deps = self._edges[node]
                if deps <= completed:  # All deps are completed
                    ready.append(node)

            if not ready:
                # Should not happen if no cycles
                break

            levels.append(ExecutionLevel(level=level_num, gates=sorted(ready)))
            completed.update(ready)
            remaining -= set(ready)
            level_num += 1

        return levels

    def get_node(self, name: str) -> T | None:
        """Get node data by name."""
        return self._nodes.get(name)

    def has_node(self, name: str) -> bool:
        """Check if node exists."""
        return name in self._nodes

    @property
    def nodes(self) -> list[str]:
        """Get all node names."""
        return list(self._nodes.keys())

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, name: str) -> bool:
        return name in self._nodes


def build_gate_graph(
    gates: dict[str, dict],
) -> DependencyGraph[dict]:
    """
    Build dependency graph from gate configurations.

    Args:
        gates: Dict of gate_name -> gate_config with 'depends_on' key

    Returns:
        DependencyGraph with gates as nodes
    """
    graph: DependencyGraph[dict] = DependencyGraph()

    # Add all gates as nodes first
    for name, config in gates.items():
        graph.add_node(name, config)

    # Add dependencies
    for name, config in gates.items():
        depends_on = config.get("depends_on", [])
        for dep in depends_on:
            if dep in gates:
                graph.add_dependency(name, dep)

    return graph


# Default gate dependency configuration
DEFAULT_GATE_DEPENDENCIES: dict[str, list[str]] = {
    "code_quality": [],  # No dependencies - runs first
    "test_coverage": ["code_quality"],  # Needs code to pass lint
    "security": ["code_quality"],  # Parallel with test_coverage
    "architecture": ["code_quality"],  # Parallel with test_coverage
    "documentation": ["code_quality"],  # Parallel with test_coverage
    "performance": ["test_coverage", "security"],  # After parallel group
    "compliance": ["security", "architecture"],  # Near end
}
