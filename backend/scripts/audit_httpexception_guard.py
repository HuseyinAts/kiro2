"""Rule-of-eight audit: find `except Exception` handlers that re-wrap as
HTTPException but lack an `except HTTPException: raise` guard above them.

The anti-pattern (confirmed 8+ times in the Golden Flow sweeps GF22, GF56,
GF57, GF77, GF81, GF82, GF85, GF88):

    try:
        # ... calls that may raise HTTPException(4xx/503) from a helper ...
    except Exception as e:
        raise HTTPException(status_code=500, ...)   # ← silently swallows 4xx!

The fix is to add an `except HTTPException: raise` clause *before* the
generic `except Exception`:

    try:
        ...
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, ...)

This script walks every `backend/api/**/*.py` file with ast, enumerates
every Try node, and reports the ones where:
- A generic `except Exception` handler exists
- The generic handler re-raises as HTTPException(5xx)
- There is NO `except HTTPException` handler before it in the same Try

Run:
    python backend/scripts/audit_httpexception_guard.py
    python backend/scripts/audit_httpexception_guard.py --fail  # CI mode
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def is_exception_name(node: ast.expr | None, target: str) -> bool:
    """Return True if `node` is a Name matching `target` (Exception / HTTPException)."""
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id == target
    if isinstance(node, ast.Attribute):
        return node.attr == target
    return False


def is_bare_exception_handler(handler: ast.ExceptHandler) -> bool:
    """Match `except Exception` and `except Exception as e` (not subclasses)."""
    return is_exception_name(handler.type, "Exception")


def is_httpexception_handler(handler: ast.ExceptHandler) -> bool:
    """Match `except HTTPException` and `except HTTPException as e`."""
    return is_exception_name(handler.type, "HTTPException")


def handler_reraises_http_500(handler: ast.ExceptHandler) -> bool:
    """Return True if body raises HTTPException (any status, not a bare re-raise)."""
    for child in ast.walk(ast.Module(body=handler.body, type_ignores=[])):
        if isinstance(child, ast.Raise):
            # bare `raise` is fine — it re-raises the original exception
            if child.exc is None:
                return False
            # raise HTTPException(...) or raise HTTPException
            exc = child.exc
            if isinstance(exc, ast.Call):
                func = exc.func
                if is_exception_name(func, "HTTPException"):
                    return True
            if is_exception_name(exc, "HTTPException"):
                return True
    return False


def find_enclosing_function(tree: ast.Module, try_node: ast.Try) -> str | None:
    """Walk tree to find which function contains this Try node."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is try_node:
                    return node.name
    return None


def audit_file(path: Path) -> list[dict]:
    """Return list of risky try/except blocks in this file."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[dict] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue

        # Find the generic `except Exception` handler (last match wins if dupe)
        bare_handlers = [h for h in node.handlers if is_bare_exception_handler(h)]
        if not bare_handlers:
            continue

        bare = bare_handlers[-1]
        if not handler_reraises_http_500(bare):
            continue

        # Look for an `except HTTPException` handler earlier in the list
        bare_idx = node.handlers.index(bare)
        has_http_guard = any(
            is_httpexception_handler(h) for h in node.handlers[:bare_idx]
        )
        if has_http_guard:
            continue

        func_name = find_enclosing_function(tree, node)
        findings.append(
            {
                "file": str(path),
                "line": bare.lineno,
                "function": func_name or "<module>",
            }
        )

    return findings


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    api_dir = repo_root / "backend" / "api"

    py_files = sorted(api_dir.rglob("*.py"))
    # Skip _deprecated — we don't care
    py_files = [p for p in py_files if "_deprecated" not in p.parts]

    all_findings: list[dict] = []
    for py in py_files:
        all_findings.extend(audit_file(py))

    if not all_findings:
        print("[OK] No risky try/except blocks found.")
        return 0

    # Group by file
    by_file: dict[str, list[dict]] = {}
    for f in all_findings:
        by_file.setdefault(f["file"], []).append(f)

    print(
        f"[WARN] Found {len(all_findings)} risky try/except blocks "
        f"across {len(by_file)} files:\n"
    )

    for fpath in sorted(by_file):
        rel = Path(fpath).relative_to(repo_root)
        findings = by_file[fpath]
        print(f"  {rel}  ({len(findings)} risky)")
        for f in findings:
            print(f"    L{f['line']:4d}  {f['function']}()")
        print()

    if "--fail" in sys.argv:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
