"""
Docstring Validation Hook - REQ-7.1 to REQ-7.6

Validates Google-style docstrings for public functions.
Reports coverage percentage.
"""

from __future__ import annotations

import ast
import re

from .base import BaseHook
from .models import (
    DocstringInfo,
    ExitCode,
    HookConfig,
    QualityCheckResult,
)


class DocstringHook(BaseHook):
    """
    Docstring validation hook.

    REQ-7.1: Scan all public functions
    REQ-7.2: Warn on missing docstrings with function name and line
    REQ-7.3: Validate Google-style docstring format
    REQ-7.4: Check all parameters are documented
    REQ-7.5: Check return type is documented
    REQ-7.6: Calculate docstring coverage percentage
    """

    name = "docstring"

    # Google-style docstring patterns
    ARGS_PATTERN = re.compile(r"^\s*Args:\s*$", re.MULTILINE)
    RETURNS_PATTERN = re.compile(r"^\s*Returns:\s*$", re.MULTILINE)
    PARAM_PATTERN = re.compile(r"^\s+(\w+)(?:\s*\([^)]+\))?:\s*.+$", re.MULTILINE)

    async def run(self, files: list[str]) -> QualityCheckResult:
        """
        Validate docstrings in files.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with validation results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Analyze all files
        all_functions: list[DocstringInfo] = []
        errors: list[str] = []
        warnings: list[str] = []

        for file_path in python_files:
            try:
                file_info = self._analyze_file(file_path)
                all_functions.extend(file_info)
            except Exception as e:
                warnings.append(f"Could not analyze {file_path}: {e!s}")

        # Calculate coverage
        total = len(all_functions)
        with_docstring = sum(1 for f in all_functions if f.has_docstring)
        coverage = (with_docstring / total * 100) if total > 0 else 100.0

        # Find issues
        for func in all_functions:
            if not func.has_docstring:
                errors.append(
                    f"{func.file}:{func.line}: Missing docstring for '{func.function_name}'"
                )
            elif func.missing_params:
                warnings.append(
                    f"{func.file}:{func.line}: '{func.function_name}' missing param docs: "
                    f"{', '.join(func.missing_params)}"
                )
            elif not func.has_returns_doc:
                warnings.append(
                    f"{func.file}:{func.line}: '{func.function_name}' missing Returns section"
                )

        # Add coverage to warnings
        coverage_msg = f"Docstring coverage: {coverage:.1f}% ({with_docstring}/{total} functions)"
        warnings.insert(0, coverage_msg)

        execution_time = self._stop_timer()

        # Determine pass/fail (coverage >= 90% is success per spec)
        passed = coverage >= 90.0 and len(errors) == 0

        return QualityCheckResult(
            tool=self.name,
            passed=passed,
            exit_code=ExitCode.SUCCESS if passed else ExitCode.BLOCKING_ERROR,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            files_checked=len(python_files)
        )

    def _analyze_file(self, file_path: str) -> list[DocstringInfo]:
        """Analyze a single file for docstrings."""
        functions: list[DocstringInfo] = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private functions (starting with _)
                    if node.name.startswith("_") and not node.name.startswith("__"):
                        continue

                    # Skip dunder methods except __init__
                    if node.name.startswith("__") and node.name != "__init__":
                        continue

                    info = self._analyze_function(node, file_path)
                    functions.append(info)

        except SyntaxError:
            pass  # Skip files with syntax errors

        return functions

    def _analyze_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str
    ) -> DocstringInfo:
        """Analyze a single function for docstring."""
        docstring = ast.get_docstring(node)

        # Get function parameters (excluding self, cls)
        params: set[str] = set()
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                params.add(arg.arg)

        info = DocstringInfo(
            function_name=node.name,
            file=file_path,
            line=node.lineno,
            has_docstring=docstring is not None,
            style="google"
        )

        if docstring:
            # Check for Args section
            has_args = bool(self.ARGS_PATTERN.search(docstring))
            info.has_args_doc = has_args

            # Check for Returns section
            info.has_returns_doc = bool(self.RETURNS_PATTERN.search(docstring))

            # Check documented parameters
            if has_args:
                documented_params = set(
                    m.group(1) for m in self.PARAM_PATTERN.finditer(docstring)
                )
                info.missing_params = list(params - documented_params)
            else:
                info.missing_params = list(params) if params else []

        return info


async def run_docstring_check(
    files: list[str],
    config: HookConfig | None = None
) -> QualityCheckResult:
    """
    Convenience function to run docstring validation.

    Args:
        files: Files to check
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = DocstringHook(config)
    return await hook.run_with_timeout(files)
