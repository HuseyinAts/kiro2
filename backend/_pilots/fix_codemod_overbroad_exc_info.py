"""Remove `exc_info=True` from logger.error() calls that are NOT inside an
`except` handler. The original codemod over-applied the kwarg.

This script uses AST to identify the bad sites, then surgically removes
the `, exc_info=True` portion using textual edit on the matching line.

It's intentionally conservative: only touches single-line logger.error()
calls. Multi-line calls are left alone (low count, manual is safer).
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


def find_outside_except_sites(root: Path) -> list[tuple[Path, int]]:
    sites: list[tuple[Path, int]] = []
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts or "_deprecated" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.in_except = 0

            def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
                self.in_except += 1
                self.generic_visit(node)
                self.in_except -= 1

            def visit_Call(self, node: ast.Call) -> None:
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "error"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "logger"
                    and any(
                        isinstance(k, ast.keyword) and k.arg == "exc_info"
                        for k in node.keywords
                    )
                    and self.in_except == 0
                ):
                    sites.append((path, node.lineno))
                self.generic_visit(node)

        Visitor().visit(tree)
    return sites


# Match `, exc_info=True` (with or without trailing comma) on a single line.
PATTERN = re.compile(r",\s*exc_info=True")


def strip_overbroad(path: Path, lineno: int) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    idx = lineno - 1
    if idx >= len(lines):
        return False
    line = lines[idx]
    if "exc_info=True" not in line:
        # Multi-line call — too risky to auto-fix.
        return False
    new_line = PATTERN.sub("", line, count=1)
    if new_line == line:
        return False
    lines[idx] = new_line
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    services_root = root / "services"
    sites = find_outside_except_sites(services_root)
    print(f"Found {len(sites)} outside-except logger.error(exc_info=True) sites")
    fixed = 0
    skipped = 0
    for path, lineno in sites:
        if strip_overbroad(path, lineno):
            fixed += 1
        else:
            skipped += 1
            print(f"  SKIP (multi-line): {path}:{lineno}")
    print(f"--- Fixed {fixed}, skipped {skipped} ---")

    # Verify no new SyntaxErrors introduced.
    import py_compile

    broken = []
    for path in services_root.rglob("*.py"):
        if "__pycache__" in path.parts or "_deprecated" in path.parts:
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            broken.append(f"{path}: {e}")
    if broken:
        print("BROKEN AFTER FIX:")
        for b in broken:
            print(f"  {b}")
        return 1
    print("All services/ files still syntactically valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
