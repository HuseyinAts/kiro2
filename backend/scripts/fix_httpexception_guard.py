"""Rule-of-eight automated fixer: insert `except HTTPException: raise` guard
before every `except Exception` handler that re-wraps as HTTPException.

Uses the audit results from audit_httpexception_guard.py — only touches
try blocks flagged as risky by the auditor, so it's safe to re-run.

Usage:
    python backend/scripts/fix_httpexception_guard.py --dry-run     # preview
    python backend/scripts/fix_httpexception_guard.py --apply       # modify
    python backend/scripts/fix_httpexception_guard.py --apply --only backend/api/foo.py

Idempotent: if a guard already exists for a given Try node, the auditor won't
flag it and the fixer will skip it. Safe to run multiple times.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# Reuse the audit logic
sys.path.insert(0, str(Path(__file__).parent))
from audit_httpexception_guard import audit_file


def detect_indent(source_line: str) -> str:
    """Return the leading whitespace of a source line."""
    return source_line[: len(source_line) - len(source_line.lstrip())]


def has_httpexception_import(lines: list[str]) -> bool:
    """Check if the file already imports HTTPException.
    Uses AST so multi-line `from fastapi import (... HTTPException ...)` is
    handled correctly."""
    try:
        tree = ast.parse("".join(lines))
    except SyntaxError:
        # Fallback to substring scan — better than nothing
        blob = "".join(lines[:120])
        return "HTTPException" in blob
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("fastapi")
        ):
            for alias in node.names:
                if alias.name == "HTTPException":
                    return True
    return False


def ensure_httpexception_import(lines: list[str]) -> tuple[list[str], bool]:
    """Add HTTPException to the fastapi import if not already present.
    Returns (new_lines, was_modified)."""
    if has_httpexception_import(lines):
        return lines, False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            stripped.startswith("from fastapi import ")
            and "HTTPException" not in stripped
        ):
            # Append to existing fastapi import
            lines[i] = line.rstrip("\n").rstrip() + ", HTTPException\n"
            return lines, True

    # No fastapi import found — shouldn't happen in an api file but be safe
    return lines, False


def insert_guards(path: Path, findings: list[dict], dry_run: bool = True) -> int:
    """Insert `except HTTPException: raise` before each flagged bare-except.
    Returns the number of guards inserted."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    # Sort by line number descending so insertions don't shift later indices
    sorted_findings = sorted(findings, key=lambda f: f["line"], reverse=True)

    inserted = 0
    for f in sorted_findings:
        # AST line is 1-based, list is 0-based
        idx = f["line"] - 1
        if idx < 0 or idx >= len(lines):
            continue

        target_line = lines[idx]
        # Sanity check: the target line must contain `except Exception`
        if "except Exception" not in target_line:
            print(
                f"  [SKIP] {path.name}:L{f['line']} — line content drift, "
                f"got {target_line.strip()[:60]!r}"
            )
            continue

        indent = detect_indent(target_line)
        guard_lines = [
            f"{indent}except HTTPException:\n",
            f"{indent}    raise\n",
        ]

        # Insert guard above the bare-except line
        lines = lines[:idx] + guard_lines + lines[idx:]
        inserted += 1

    if inserted == 0:
        return 0

    # Ensure HTTPException is importable
    lines, import_added = ensure_httpexception_import(lines)

    if dry_run:
        return inserted

    new_source = "".join(lines)
    path.write_text(new_source, encoding="utf-8")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing"
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes to disk")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Limit to a single file (path relative to repo root)",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("Must pass --dry-run or --apply")

    repo_root = Path(__file__).resolve().parents[2]
    api_dir = repo_root / "backend" / "api"

    if args.only:
        py_files = [repo_root / args.only]
    else:
        py_files = sorted(api_dir.rglob("*.py"))
        py_files = [p for p in py_files if "_deprecated" not in p.parts]

    total_inserted = 0
    files_modified = 0

    for py in py_files:
        findings = audit_file(py)
        if not findings:
            continue

        rel = py.relative_to(repo_root)
        count = insert_guards(py, findings, dry_run=args.dry_run)
        if count > 0:
            files_modified += 1
            total_inserted += count
            action = "WOULD INSERT" if args.dry_run else "INSERTED"
            print(f"  {action} {count:3d} guards in {rel}")

    print()
    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"[{mode}] Inserted {total_inserted} guards across {files_modified} files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
