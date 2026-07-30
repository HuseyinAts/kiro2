"""
AST (Abstract Syntax Tree) Analyzer for Python code analysis.

Provides deep code analysis beyond regex pattern matching.
"""

from __future__ import annotations

import ast
from collections.abc import Generator
from dataclasses import dataclass

from ..exceptions import ASTParseError


@dataclass
class ASTMatch:
    """Result of an AST analysis match."""

    node_type: str
    line_number: int
    column: int
    code: str
    message: str
    confidence: float = 1.0


class ASTAnalyzer:
    """
    AST-based code analyzer for deep Python analysis.

    Provides methods to detect patterns that are difficult or
    impossible to detect with regex alone.
    """

    def __init__(self, content: str, file_path: str = "<unknown>"):
        """
        Initialize AST analyzer with Python source code.

        Args:
            content: Python source code as string
            file_path: Path to source file (for error messages)

        Raises:
            ASTParseError: If the code cannot be parsed
        """
        self.content = content
        self.file_path = file_path
        self._tree: ast.AST | None = None
        self._lines: list[str] = content.split("\n")

    def parse(self) -> bool:
        """
        Parse the source code into an AST.

        Returns:
            True if parsing succeeded, False otherwise

        Raises:
            ASTParseError: If parsing fails
        """
        try:
            self._tree = ast.parse(self.content, filename=self.file_path)
            return True
        except SyntaxError as e:
            raise ASTParseError(
                file_path=self.file_path, message=str(e), line_number=e.lineno
            )

    def _walk(self) -> Generator[ast.AST, None, None]:
        """Walk all nodes in the AST."""
        if self._tree is None:
            return
        yield from ast.walk(self._tree)

    def _get_line(self, lineno: int) -> str:
        """Get source line by line number (1-indexed)."""
        if 1 <= lineno <= len(self._lines):
            return self._lines[lineno - 1]
        return ""

    def find_assert_true(self) -> list[ASTMatch]:
        """
        Find assert True statements using AST analysis.

        Detects:
        - assert True
        - assert 1 == 1 (tautologies)
        - assert "x" == "x" (string tautologies)

        Returns:
            List of ASTMatch objects
        """
        if self._tree is None:
            self.parse()

        results: list[ASTMatch] = []

        for node in self._walk():
            if isinstance(node, ast.Assert):
                # Check for `assert True`
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    results.append(
                        ASTMatch(
                            node_type="Assert",
                            line_number=node.lineno,
                            column=node.col_offset,
                            code=self._get_line(node.lineno),
                            message="Fake assertion: assert True",
                            confidence=1.0,
                        )
                    )

                # Check for tautologies like `assert 1 == 1`
                elif isinstance(node.test, ast.Compare):
                    if self._is_tautology(node.test):
                        results.append(
                            ASTMatch(
                                node_type="Assert",
                                line_number=node.lineno,
                                column=node.col_offset,
                                code=self._get_line(node.lineno),
                                message="Fake assertion: tautology comparison",
                                confidence=0.9,
                            )
                        )

        return results

    def _is_tautology(self, compare: ast.Compare) -> bool:
        """Check if a comparison is a tautology (e.g., 1 == 1)."""
        if len(compare.ops) == 1 and isinstance(compare.ops[0], ast.Eq):
            left = compare.left
            right = compare.comparators[0]

            # Check if both sides are the same constant
            # bool(): ast.Constant.value tipi Any, mypy --strict no-any-return
            # veriyor. Onceden var olan durum; dosya #455 icin degistigi icin
            # kapiya ilk kez girdi.
            if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):
                return bool(left.value == right.value)

        return False

    def find_empty_functions(self) -> list[ASTMatch]:
        """
        Find functions with only pass or ellipsis body.

        Returns:
            List of ASTMatch objects
        """
        if self._tree is None:
            self.parse()

        results: list[ASTMatch] = []

        for node in self._walk():
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body

                # Check if body is only pass, ellipsis, or docstring + pass
                if self._is_placeholder_body(body):
                    results.append(
                        ASTMatch(
                            node_type="FunctionDef",
                            line_number=node.lineno,
                            column=node.col_offset,
                            code=self._get_line(node.lineno),
                            message=f"Empty function: {node.name}",
                            confidence=0.95,
                        )
                    )

        return results

    def _is_placeholder_body(self, body: list[ast.stmt]) -> bool:
        """Check if function body is just a placeholder."""
        if not body:
            return True

        # Filter out docstrings
        non_docstring = [
            stmt
            for stmt in body
            if not (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            )
        ]

        if not non_docstring:
            return False  # Only docstring is OK

        # Check for pass or ellipsis
        if len(non_docstring) == 1:
            stmt = non_docstring[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if stmt.value.value is ...:  # Ellipsis
                    return True

        return False

    def find_empty_except_handlers(self) -> list[ASTMatch]:
        """
        Find except handlers with empty or pass-only bodies.

        Returns:
            List of ASTMatch objects
        """
        if self._tree is None:
            self.parse()

        results: list[ASTMatch] = []

        for node in self._walk():
            if isinstance(node, ast.ExceptHandler):
                if self._is_placeholder_body(node.body):
                    exc_type = (
                        "bare except" if node.type is None else ast.unparse(node.type)
                    )
                    results.append(
                        ASTMatch(
                            node_type="ExceptHandler",
                            line_number=node.lineno,
                            column=node.col_offset,
                            code=self._get_line(node.lineno),
                            message=f"Empty exception handler: {exc_type}",
                            confidence=0.95,
                        )
                    )

        return results

    def find_skip_decorators(self) -> list[ASTMatch]:
        """
        Find @pytest.mark.skip and similar decorators without reason.

        Returns:
            List of ASTMatch objects
        """
        if self._tree is None:
            self.parse()

        results: list[ASTMatch] = []

        for node in self._walk():
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    skip_match = self._check_skip_decorator(decorator)
                    if skip_match:
                        results.append(
                            ASTMatch(
                                node_type="Decorator",
                                line_number=decorator.lineno,
                                column=decorator.col_offset,
                                code=self._get_line(decorator.lineno),
                                message=f"Skip decorator without reason: {node.name}",
                                confidence=0.9,
                            )
                        )

        return results

    def _check_skip_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is a skip without reason."""
        # @pytest.mark.skip without call
        if isinstance(decorator, ast.Attribute):
            if decorator.attr in ("skip", "skipif"):
                return True

        # @pytest.mark.skip() with empty args
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ("skip", "skipif"):
                    # Check if reason is provided
                    has_reason = any(kw.arg == "reason" for kw in decorator.keywords)
                    if not has_reason and not decorator.args:
                        return True

        return False

    def find_raise_not_implemented(self) -> list[ASTMatch]:
        """
        Find raise NotImplementedError statements.

        Returns:
            List of ASTMatch objects
        """
        if self._tree is None:
            self.parse()

        results: list[ASTMatch] = []

        for node in self._walk():
            if isinstance(node, ast.Raise):
                if node.exc is not None:
                    # Check for NotImplementedError
                    if isinstance(node.exc, ast.Call):
                        if isinstance(node.exc.func, ast.Name):
                            if node.exc.func.id == "NotImplementedError":
                                results.append(
                                    ASTMatch(
                                        node_type="Raise",
                                        line_number=node.lineno,
                                        column=node.col_offset,
                                        code=self._get_line(node.lineno),
                                        message="Placeholder: raise NotImplementedError",
                                        confidence=0.9,
                                    )
                                )
                    elif isinstance(node.exc, ast.Name):
                        if node.exc.id == "NotImplementedError":
                            results.append(
                                ASTMatch(
                                    node_type="Raise",
                                    line_number=node.lineno,
                                    column=node.col_offset,
                                    code=self._get_line(node.lineno),
                                    message="Placeholder: raise NotImplementedError",
                                    confidence=0.9,
                                )
                            )

        return results

    def count_mock_usage(self) -> tuple[int, int]:
        """
        Count mock usage vs total function calls in test files.

        `mock_count <= total_calls` bir INVARYANTTIR. Eskiden bozuktu: ayrı bir
        `node.decorator_list` döngüsü `@patch(...)` dekoratörlerini ikinci kez
        sayıyordu, çünkü `@patch(...)` zaten bir `ast.Call` düğümüdür ve
        `ast.walk` onu aşağıdaki dalda ziyaret ediyor. Ölçüldü (30 Tem 2026, #455):
        iki dekoratörlü bir dosyada `mock_count=4 / total_calls=2` → **%200**;
        bekçinin canlı çıktısı "High mock ratio (125%) (5/4)" basıyordu.
        `MOCK_RATIO_THRESHOLD = 0.8` böyle bir sayaçla mock yoğunluğunu değil
        dekoratör sayısını ölçer.

        Kaldırılan döngünün yakaladığı, aşağıdaki dalın kaçırdığı vaka YOK:
        bare `@patch` bir `ast.Name`'dir (Call değil), `@patch.object(...)` ise
        `func.attr == "object"` olduğu için iki yolda da sayılmıyordu.

        Sözleşme: tests/hooks/reward_hacking/test_mock_ratio.py

        Returns:
            Tuple of (mock_count, total_calls)
        """
        if self._tree is None:
            self.parse()

        mock_count = 0
        total_calls = 0

        for node in self._walk():
            if isinstance(node, ast.Call):
                total_calls += 1

                # Check for Mock/MagicMock calls (@patch(...) dahil — o da bir Call)
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("Mock", "MagicMock", "patch", "mock"):
                        mock_count += 1
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("Mock", "MagicMock", "patch"):
                        mock_count += 1

        return (mock_count, total_calls)
