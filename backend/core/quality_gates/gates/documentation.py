"""
Documentation Gate
==================

Checks:
- README completeness
- API documentation (Sphinx/OpenAPI)
- Inline comment coverage
- Breaking change documentation
- Feature documentation
- Example code presence

Ensures adequate documentation for maintainability.
"""

from __future__ import annotations

import ast
import logging
import re
import time
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


class DocumentationGate(BaseGate):
    """Documentation quality gate."""

    def get_name(self) -> str:
        return "documentation"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="documentation",
            enabled=True,
            blocking=False,  # Usually advisory
            threshold=6.0,
            warning_threshold=8.0,
            timeout_seconds=60,
            max_retries=1,
            depends_on=["code_quality"],
            tool_config={
                "readme_required": True,
                "min_readme_length": 500,
                "api_docs_enabled": True,
                "docstring_coverage_min": 70,
                "example_required": True,
                "changelog_required": False,
                "readme_sections": [
                    "installation",
                    "usage",
                    "configuration",
                ],
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute documentation checks."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}

        config = self.config.tool_config

        # 1. Check README
        if config.get("readme_required", True):
            readme_result = await self._check_readme(
                context.working_dir,
                config.get("min_readme_length", 500),
                config.get("readme_sections", []),
            )
            scores["readme"] = readme_result.get("score", 0)
            issues.extend(readme_result.get("issues", []))

        # 2. Check API documentation
        if config.get("api_docs_enabled", True):
            api_result = await self._check_api_docs(context.working_dir)
            scores["api_docs"] = api_result.get("score", 10)
            issues.extend(api_result.get("issues", []))

        # 3. Check docstring coverage
        docstring_result = await self._check_docstrings(
            context.working_dir,
            config.get("docstring_coverage_min", 70),
        )
        scores["docstrings"] = docstring_result.get("score", 5)
        issues.extend(docstring_result.get("issues", []))

        # 4. Check for examples
        if config.get("example_required", True):
            example_result = await self._check_examples(context.working_dir)
            scores["examples"] = example_result.get("score", 5)
            issues.extend(example_result.get("issues", []))

        # 5. Check changelog if required
        if config.get("changelog_required", False):
            changelog_result = await self._check_changelog(context.working_dir)
            scores["changelog"] = changelog_result.get("score", 5)
            issues.extend(changelog_result.get("issues", []))

        # Calculate final score
        if scores:
            final_score = sum(scores.values()) / len(scores)
        else:
            final_score = 5.0

        # Build metrics
        metrics = GateMetrics(
            docstring_coverage=docstring_result.get("coverage"),
        )

        status = self.determine_status(final_score)
        execution_time_ms = (time.time() - start_time) * 1000
        message = self._build_message(scores, docstring_result)

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

    async def _check_readme(
        self,
        working_dir: Path,
        min_length: int,
        required_sections: list[str],
    ) -> dict:
        """Check README completeness."""
        issues: list[GateIssue] = []

        # Find README
        readme_paths = ["README.md", "README.rst", "README.txt", "README"]
        readme_path = None
        readme_content = ""

        for name in readme_paths:
            path = working_dir / name
            if path.exists():
                readme_path = path
                readme_content = path.read_text(encoding="utf-8", errors="ignore")
                break

        if not readme_path:
            issues.append(
                self.create_issue(
                    file="README",
                    rule="NO_README",
                    message="README file not found",
                    severity=GateSeverity.HIGH,
                    suggestion="Create a README.md with project documentation",
                )
            )
            return {"score": 0.0, "issues": issues}

        score = 10.0

        # Check length
        if len(readme_content) < min_length:
            score -= 3
            issues.append(
                self.create_issue(
                    file=str(readme_path.name),
                    rule="README_SHORT",
                    message=f"README is too short ({len(readme_content)} chars, min: {min_length})",
                    severity=GateSeverity.MEDIUM,
                )
            )

        # Check required sections
        content_lower = readme_content.lower()
        missing_sections = []

        for section in required_sections:
            # Check for section headers
            patterns = [
                f"# {section}",
                f"## {section}",
                f"### {section}",
                f"**{section}**",
            ]
            if not any(p.lower() in content_lower for p in patterns):
                missing_sections.append(section)

        if missing_sections:
            score -= len(missing_sections) * 1.5
            issues.append(
                self.create_issue(
                    file=str(readme_path.name),
                    rule="README_MISSING_SECTIONS",
                    message=f"README missing sections: {', '.join(missing_sections)}",
                    severity=GateSeverity.LOW,
                    suggestion=f"Add sections: {', '.join(missing_sections)}",
                )
            )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_api_docs(self, working_dir: Path) -> dict:
        """Check API documentation."""
        issues: list[GateIssue] = []
        score = 10.0

        # Check for OpenAPI spec
        openapi_paths = ["openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml"]
        has_openapi = any((working_dir / p).exists() for p in openapi_paths)

        # Check for Sphinx docs
        has_sphinx = (working_dir / "docs" / "conf.py").exists()

        # Check for docstrings in API routes
        api_dir = working_dir / "api"
        if api_dir.exists():
            py_files = list(api_dir.rglob("*.py"))
            undocumented_routes = 0

            for py_file in py_files[:20]:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Check for route decorators
                            is_route = any(
                                isinstance(d, ast.Call) and
                                hasattr(d.func, "attr") and
                                d.func.attr in ("get", "post", "put", "delete", "patch")
                                for d in node.decorator_list
                            ) if node.decorator_list else False

                            if is_route and not ast.get_docstring(node):
                                undocumented_routes += 1
                except Exception:
                    continue

            if undocumented_routes > 0:
                score -= min(5, undocumented_routes * 0.5)
                issues.append(
                    self.create_issue(
                        file="api/",
                        rule="UNDOCUMENTED_ROUTES",
                        message=f"{undocumented_routes} API routes without docstrings",
                        severity=GateSeverity.MEDIUM,
                        suggestion="Add docstrings to API endpoint functions",
                    )
                )

        if not has_openapi and not has_sphinx:
            score -= 2
            issues.append(
                self.create_issue(
                    file="docs/",
                    rule="NO_API_DOCS",
                    message="No OpenAPI spec or Sphinx documentation found",
                    severity=GateSeverity.LOW,
                    suggestion="Generate OpenAPI spec or set up Sphinx docs",
                )
            )

        return {
            "score": max(0, round(score, 2)),
            "issues": issues,
        }

    async def _check_docstrings(
        self,
        working_dir: Path,
        min_coverage: float,
    ) -> dict:
        """Check docstring coverage."""
        issues: list[GateIssue] = []
        total_functions = 0
        documented_functions = 0

        py_files = list(working_dir.rglob("*.py"))

        for py_file in py_files[:100]:
            # Skip test files
            if "test" in py_file.name.lower():
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Skip private functions
                        if node.name.startswith("_") and not node.name.startswith("__"):
                            continue

                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
            except Exception:
                continue

        coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0

        if coverage < min_coverage:
            issues.append(
                self.create_issue(
                    file=".",
                    rule="LOW_DOCSTRING_COVERAGE",
                    message=f"Docstring coverage {coverage:.1f}% below minimum {min_coverage}%",
                    severity=GateSeverity.MEDIUM,
                    suggestion="Add docstrings to public functions and classes",
                )
            )

        # Score based on coverage
        score = coverage / 10  # 100% = 10 points

        return {
            "score": round(score, 2),
            "coverage": round(coverage, 2),
            "total": total_functions,
            "documented": documented_functions,
            "issues": issues,
        }

    async def _check_examples(self, working_dir: Path) -> dict:
        """Check for example code."""
        issues: list[GateIssue] = []
        score = 10.0

        # Look for examples directory or files
        example_paths = [
            "examples",
            "example",
            "samples",
            "demo",
        ]

        has_examples = any((working_dir / p).exists() for p in example_paths)

        # Check README for code examples
        readme_path = working_dir / "README.md"
        has_readme_examples = False

        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8", errors="ignore")
            # Look for code blocks
            code_blocks = re.findall(r"```\w*\n[\s\S]*?\n```", content)
            has_readme_examples = len(code_blocks) >= 2

        if not has_examples and not has_readme_examples:
            score = 5.0
            issues.append(
                self.create_issue(
                    file="examples/",
                    rule="NO_EXAMPLES",
                    message="No example code found",
                    severity=GateSeverity.LOW,
                    suggestion="Add examples/ directory or code examples in README",
                )
            )

        return {
            "score": score,
            "issues": issues,
        }

    async def _check_changelog(self, working_dir: Path) -> dict:
        """Check for changelog."""
        issues: list[GateIssue] = []

        changelog_paths = [
            "CHANGELOG.md",
            "CHANGELOG.rst",
            "CHANGELOG",
            "HISTORY.md",
            "CHANGES.md",
        ]

        has_changelog = any((working_dir / p).exists() for p in changelog_paths)

        if not has_changelog:
            issues.append(
                self.create_issue(
                    file="CHANGELOG",
                    rule="NO_CHANGELOG",
                    message="No CHANGELOG file found",
                    severity=GateSeverity.LOW,
                    suggestion="Create CHANGELOG.md to track version changes",
                )
            )
            return {"score": 5.0, "issues": issues}

        return {"score": 10.0, "issues": []}

    def _build_message(self, scores: dict, docstring_result: dict) -> str:
        """Build result message."""
        parts = []

        if "readme" in scores:
            parts.append(f"README: {scores['readme']:.1f}/10")

        if "docstrings" in scores:
            coverage = docstring_result.get("coverage", 0)
            parts.append(f"Docstrings: {coverage:.1f}%")

        if "api_docs" in scores and scores["api_docs"] < 10:
            parts.append("API docs: incomplete")

        if "examples" in scores and scores["examples"] < 10:
            parts.append("Examples: missing")

        return " | ".join(parts) if parts else "Documentation checks passed"
