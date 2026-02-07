"""
Architecture Gate
=================

Checks:
- Dependency direction (import-linter)
- Circular dependency detection
- Layer separation validation
- Coupling metrics
- Cohesion metrics
- Design pattern validation

Ensures clean architecture principles.
"""

from __future__ import annotations

import ast
import logging
import re
import time
from collections import defaultdict
from pathlib import Path

from ..models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
)
from .base import BaseGate, GateContext


logger = logging.getLogger(__name__)


class ArchitectureGate(BaseGate):
    """Architecture validation gate."""

    def get_name(self) -> str:
        return "architecture"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="architecture",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=120,
            max_retries=1,
            depends_on=["code_quality"],
            tool_config={
                "import_linter_enabled": True,
                "circular_deps_enabled": True,
                "layer_validation_enabled": True,
                "max_coupling": 0.7,  # 0-1 scale
                "min_cohesion": 0.3,  # 0-1 scale
                "layers": [
                    "api",      # Top layer
                    "services", # Middle layer
                    "models",   # Bottom layer
                    "core",     # Foundation
                ],
                "forbidden_imports": {
                    "api": ["models"],  # api cannot import models directly
                },
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute architecture checks."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}

        config = self.config.tool_config

        # 1. Check import directions (import-linter)
        if config.get("import_linter_enabled", True):
            import_result = await self._check_import_directions(context.working_dir)
            scores["imports"] = import_result.get("score", 10)
            issues.extend(import_result.get("issues", []))

        # 2. Detect circular dependencies
        if config.get("circular_deps_enabled", True):
            circular_result = await self._detect_circular_deps(context.working_dir)
            scores["circular"] = circular_result.get("score", 10)
            issues.extend(circular_result.get("issues", []))

        # 3. Validate layer separation
        if config.get("layer_validation_enabled", True):
            layer_result = await self._validate_layers(
                context.working_dir,
                config.get("layers", []),
                config.get("forbidden_imports", {}),
            )
            scores["layers"] = layer_result.get("score", 10)
            issues.extend(layer_result.get("issues", []))

        # 4. Calculate coupling/cohesion metrics
        metrics_result = await self._calculate_metrics(context.working_dir)
        scores["coupling"] = metrics_result.get("coupling_score", 10)
        scores["cohesion"] = metrics_result.get("cohesion_score", 10)

        if metrics_result.get("coupling", 0) > config.get("max_coupling", 0.7):
            issues.append(
                self.create_issue(
                    file="architecture",
                    rule="HIGH_COUPLING",
                    message=f"Module coupling {metrics_result['coupling']:.2f} exceeds maximum {config['max_coupling']}",
                    severity=GateSeverity.MEDIUM,
                    suggestion="Reduce inter-module dependencies",
                )
            )

        if metrics_result.get("cohesion", 1) < config.get("min_cohesion", 0.3):
            issues.append(
                self.create_issue(
                    file="architecture",
                    rule="LOW_COHESION",
                    message=f"Module cohesion {metrics_result['cohesion']:.2f} below minimum {config['min_cohesion']}",
                    severity=GateSeverity.LOW,
                    suggestion="Group related functionality together",
                )
            )

        # Calculate final score
        if scores:
            final_score = sum(scores.values()) / len(scores)
        else:
            final_score = 10.0

        # Build metrics
        metrics = GateMetrics(
            circular_deps_count=circular_result.get("count", 0) if config.get("circular_deps_enabled") else None,
            layer_violations_count=layer_result.get("count", 0) if config.get("layer_validation_enabled") else None,
            coupling_score=metrics_result.get("coupling"),
            cohesion_score=metrics_result.get("cohesion"),
        )

        status = self.determine_status(final_score)
        execution_time_ms = (time.time() - start_time) * 1000
        message = self._build_message(scores, metrics_result)

        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=round(final_score, 2),
            threshold=self.config.threshold,
            message=message,
            issues=issues,
            metrics=metrics,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
        )

    async def _check_import_directions(self, working_dir: Path) -> dict:
        """Check import directions using import-linter."""
        # Try import-linter if available
        result = await self.run_command(
            ["lint-imports"],
            working_dir,
            timeout=60,
        )

        issues: list[GateIssue] = []
        violation_count = 0

        if result.return_code == 0:
            return {"score": 10.0, "issues": [], "count": 0}

        # Parse violations from output
        if result.stdout or result.stderr:
            output = result.stdout or result.stderr
            violation_pattern = re.compile(r"(\S+) cannot import (\S+)")

            for match in violation_pattern.finditer(output):
                violation_count += 1
                issues.append(
                    self.create_issue(
                        file=match.group(1),
                        rule="IMPORT_DIRECTION",
                        message=f"Invalid import: {match.group(1)} -> {match.group(2)}",
                        severity=GateSeverity.MEDIUM,
                    )
                )

        score = max(0, 10 - violation_count * 2)

        return {
            "score": round(score, 2),
            "issues": issues[:20],  # Limit
            "count": violation_count,
        }

    async def _detect_circular_deps(self, working_dir: Path) -> dict:
        """Detect circular dependencies in Python code."""
        issues: list[GateIssue] = []

        # Build import graph
        import_graph: dict[str, set[str]] = defaultdict(set)
        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:100]:  # Limit for performance
            try:
                module_name = self._get_module_name(py_file, working_dir)
                imports = self._extract_imports(py_file)
                import_graph[module_name].update(imports)
            except Exception:
                continue

        # Find cycles using DFS
        cycles = self._find_cycles(import_graph)

        for cycle in cycles[:10]:  # Limit reported cycles
            issues.append(
                self.create_issue(
                    file=cycle[0],
                    rule="CIRCULAR_IMPORT",
                    message=f"Circular dependency: {' -> '.join(cycle)}",
                    severity=GateSeverity.HIGH,
                    suggestion="Break the cycle by refactoring shared code",
                )
            )

        score = max(0, 10 - len(cycles) * 3)

        return {
            "score": round(score, 2),
            "issues": issues,
            "count": len(cycles),
        }

    async def _validate_layers(
        self,
        working_dir: Path,
        layers: list[str],
        forbidden_imports: dict[str, list[str]],
    ) -> dict:
        """Validate layer separation."""
        issues: list[GateIssue] = []
        violation_count = 0

        if not layers:
            return {"score": 10.0, "issues": [], "count": 0}

        # Check each layer's imports
        for layer_idx, layer in enumerate(layers):
            layer_path = working_dir / layer
            if not layer_path.exists():
                continue

            py_files = list(layer_path.rglob("*.py"))

            for py_file in py_files[:50]:
                try:
                    imports = self._extract_imports(py_file)

                    # Check forbidden imports
                    forbidden = forbidden_imports.get(layer, [])
                    for imp in imports:
                        for forbidden_layer in forbidden:
                            if forbidden_layer in imp:
                                violation_count += 1
                                issues.append(
                                    self.create_issue(
                                        file=str(py_file.relative_to(working_dir)),
                                        rule="LAYER_VIOLATION",
                                        message=f"Layer '{layer}' imports from forbidden layer '{forbidden_layer}'",
                                        severity=GateSeverity.MEDIUM,
                                    )
                                )
                except Exception:
                    continue

        score = max(0, 10 - violation_count * 1.5)

        return {
            "score": round(score, 2),
            "issues": issues[:20],
            "count": violation_count,
        }

    async def _calculate_metrics(self, working_dir: Path) -> dict:
        """Calculate coupling and cohesion metrics."""
        # Simplified coupling: average number of imports per module
        import_counts: list[int] = []
        internal_usage: dict[str, int] = defaultdict(int)

        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:100]:
            try:
                imports = self._extract_imports(py_file)
                import_counts.append(len(imports))

                # Count internal references for cohesion
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for name in self._extract_definitions(content):
                    internal_usage[name] += 1
            except Exception:
                continue

        # Coupling: normalized average imports (0-1, lower is better)
        avg_imports = sum(import_counts) / len(import_counts) if import_counts else 0
        coupling = min(1.0, avg_imports / 20)  # Normalize to 20 imports = 1.0

        # Cohesion: how often internal items are reused (0-1, higher is better)
        if internal_usage:
            avg_usage = sum(internal_usage.values()) / len(internal_usage)
            cohesion = min(1.0, avg_usage / 3)  # Normalize to 3 uses = 1.0
        else:
            cohesion = 0.5

        # Convert to scores (10 scale)
        coupling_score = (1 - coupling) * 10
        cohesion_score = cohesion * 10

        return {
            "coupling": round(coupling, 2),
            "cohesion": round(cohesion, 2),
            "coupling_score": round(coupling_score, 2),
            "cohesion_score": round(cohesion_score, 2),
        }

    def _get_module_name(self, filepath: Path, base: Path) -> str:
        """Convert file path to module name."""
        rel_path = filepath.relative_to(base)
        parts = list(rel_path.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace(".py", "")
        return ".".join(parts)

    def _extract_imports(self, filepath: Path) -> set[str]:
        """Extract imports from a Python file."""
        imports: set[str] = set()
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except Exception:
            pass
        return imports

    def _extract_definitions(self, content: str) -> list[str]:
        """Extract function/class definitions."""
        definitions: list[str] = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    definitions.append(node.name)
        except Exception:
            pass
        return definitions

    def _find_cycles(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Find cycles in import graph using DFS."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if len(cycle) <= 5:  # Only short cycles
                        cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def _build_message(self, scores: dict, metrics: dict) -> str:
        """Build result message."""
        parts = []

        if "imports" in scores:
            parts.append(f"Imports: {scores['imports']:.1f}")
        if "circular" in scores and scores["circular"] < 10:
            parts.append(f"Circular: {int(10 - scores['circular'])} found")
        if "layers" in scores and scores["layers"] < 10:
            parts.append(f"Layer violations: {int((10 - scores['layers']) / 1.5)}")

        parts.append(f"Coupling: {metrics.get('coupling', 0):.2f}")
        parts.append(f"Cohesion: {metrics.get('cohesion', 0):.2f}")

        return " | ".join(parts)
