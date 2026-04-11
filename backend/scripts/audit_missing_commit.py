#!/usr/bin/env python
"""
audit_missing_commit.py — AST linter for MISSING_COMMIT pattern.

Session 138 extended audit_db_dependency.py to catch sync/async type lies.
This linter catches a DIFFERENT class of half-working feature bug:

Pattern — handler calls `db.add(obj)` / `session.add(obj)` but NEVER
commits in the function body, AND does not delegate to a service that
would commit. Result: FastAPI handler returns 200 OK, autocommit is
off, transaction is rolled back at the end of the request, the new
row is silently dropped. Frontend sees success, database is empty.

This is the bug pattern Session 136 surfaced in gamification points,
ai_chat image upload, teacher classroom, kvkk consent, and others.

Detection logic:
1. For each `async def` FastAPI handler (decorator `@router.*` or
   inside an APIRouter module with no decorator but signature matches),
   walk the body AST.
2. Collect all `*.add(obj)` call sites where the callee is either
   `db`, `session`, `self.db`, or an arg named similarly.
3. If at least one `.add(...)` call is found, check if the same
   function body also contains a `.commit()` call on the same object.
4. If no commit found AND no service delegation (call that passes
   `db`/`session` to another object), report as MISSING_COMMIT.

Heuristics / false positive filters:
- If the handler name starts with `get_` / `list_` / `fetch_` → skip
  (unlikely to mutate).
- If the function uses `async with ... context` creating its OWN db
  session → we trust the context manager's commit semantics.
- If the function passes `db` to a service method and that method is
  known to commit (e.g., `Service(db).create_*()`), lower severity to
  MED (still worth reviewing).
- Skip test files, _deprecated/, __pycache__.

Usage:
    python scripts/audit_missing_commit.py              # report
    python scripts/audit_missing_commit.py --fail-on-high  # exit 1 on HIGH
    python scripts/audit_missing_commit.py --json out.json

Exit codes:
    0 — clean or report-only
    1 — HIGH findings AND --fail-on-high
    2 — internal parse error
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

AUDIT_ROOTS = ["api", "app/api"]
SKIP_DIRS = {"__pycache__", "_deprecated", "tests", "node_modules", "venv", ".venv"}

# Parameter names that typically refer to a DB session.
DB_ARG_NAMES = {"db", "session", "db_session", "async_db"}

# Handler name prefixes that are read-only — skip.
READONLY_PREFIXES = ("get_", "list_", "fetch_", "read_", "view_", "search_", "find_")


@dataclass
class Finding:
    file: str
    line: int
    handler: str
    severity: str  # "high" | "medium" | "low"
    detail: str
    add_line: int
    add_target: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def by_severity(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {"high": [], "medium": [], "low": []}
        for f in self.findings:
            out[f.severity].append(f)
        return out

    def total(self) -> int:
        return len(self.findings)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _is_router_decorated(node: ast.AsyncFunctionDef) -> bool:
    """Does the function have a `@router.get/post/put/delete/patch(...)` decorator?"""
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in ("router", "app")
                and func.attr
                in ("get", "post", "put", "delete", "patch", "head", "options")
            ):
                return True
    return False


def _get_handler_db_args(node: ast.AsyncFunctionDef) -> set[str]:
    """Return names of handler parameters that look like DB sessions."""
    out: set[str] = set()
    for arg in node.args.args + node.args.kwonlyargs:
        if arg.arg in DB_ARG_NAMES:
            out.add(arg.arg)
    return out


def _is_add_call(call: ast.Call, db_names: set[str]) -> str | None:
    """Return the target name if this is `<db>.add(...)`, else None."""
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "add":
        return None
    # Handle direct `db.add(...)`
    if isinstance(func.value, ast.Name) and func.value.id in db_names:
        return func.value.id
    # Handle `self.db.add(...)` — rarely inside FastAPI handlers
    if (
        isinstance(func.value, ast.Attribute)
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == "self"
        and func.value.attr in DB_ARG_NAMES
    ):
        return f"self.{func.value.attr}"
    return None


def _has_commit_call(node: ast.AsyncFunctionDef, db_names: set[str]) -> bool:
    """Does the function body call `db.commit()` or `await db.commit()`?"""
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if not isinstance(func, ast.Attribute) or func.attr != "commit":
            continue
        if isinstance(func.value, ast.Name) and func.value.id in db_names:
            return True
        # `self.db.commit()`
        if (
            isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "self"
            and func.value.attr in DB_ARG_NAMES
        ):
            return True
    return False


def _delegates_to_service(node: ast.AsyncFunctionDef, db_names: set[str]) -> bool:
    """
    Does the function pass `db` to a service constructor or method?

    Example: `Service(db).create_something(...)` or
    `service.method(..., db=db)` — the service may commit internally.
    """
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        # Positional args
        for a in sub.args:
            if isinstance(a, ast.Name) and a.id in db_names:
                return True
        # Keyword args
        for kw in sub.keywords:
            if isinstance(kw.value, ast.Name) and kw.value.id in db_names:
                return True
    return False


def _uses_own_session_context(node: ast.AsyncFunctionDef) -> bool:
    """
    Does the function create its own session via `async with get_db_session_context()`?

    If yes, we trust the context manager's commit semantics and skip this
    function entirely (the handler's own `db` parameter is unused for writes).
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.AsyncWith):
            for item in sub.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Call):
                    func = ctx.func
                    if isinstance(func, ast.Name) and "session_context" in func.id:
                        return True
                    if (
                        isinstance(func, ast.Attribute)
                        and "session_context" in func.attr
                    ):
                        return True
    return False


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def _scan_file(path: Path, src: str, report: AuditReport, root: Path) -> None:
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"[parse-error] {path}: {e}", file=sys.stderr)
        return

    rel = str(path.relative_to(root)).replace("\\", "/")

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if not _is_router_decorated(node):
            continue
        if any(node.name.startswith(p) for p in READONLY_PREFIXES):
            continue
        db_names = _get_handler_db_args(node)
        if not db_names:
            continue

        # Skip if handler creates its own session context (trusts context mgr)
        if _uses_own_session_context(node):
            continue

        # Find db.add() calls
        add_calls: list[tuple[int, str]] = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                target = _is_add_call(sub, db_names)
                if target:
                    add_calls.append((sub.lineno, target))

        if not add_calls:
            continue

        has_commit = _has_commit_call(node, db_names)
        delegates = _delegates_to_service(node, db_names)

        if has_commit:
            continue  # OK

        # No commit found. Severity depends on delegation.
        severity = "medium" if delegates else "high"
        first_add = add_calls[0]
        detail = (
            f"`{first_add[1]}.add(...)` at line {first_add[0]} but no "
            f"`{first_add[1]}.commit()` found in handler body. "
            + (
                "Handler does pass db to another callable — service may commit internally (MED)."
                if delegates
                else "Handler does NOT delegate db to a service. Row will be silently rolled back (HIGH)."
            )
        )
        report.findings.append(
            Finding(
                file=rel,
                line=node.lineno,
                handler=node.name,
                severity=severity,
                detail=detail,
                add_line=first_add[0],
                add_target=first_add[1],
            )
        )


def _walk_sources(root: Path) -> list[Path]:
    out: list[Path] = []
    for sub in AUDIT_ROOTS:
        base = root / sub
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _render_text(report: AuditReport) -> str:
    buckets = report.by_severity()
    lines: list[str] = []
    lines.append("# Missing-Commit Audit Report")
    lines.append("")
    lines.append(f"**Total findings:** {report.total()}")
    lines.append(f"- HIGH: {len(buckets['high'])}")
    lines.append(f"- MED:  {len(buckets['medium'])}")
    lines.append(f"- LOW:  {len(buckets['low'])}")
    lines.append("")

    for sev in ("high", "medium", "low"):
        items = buckets[sev]
        if not items:
            continue
        lines.append(f"## {sev.upper()} ({len(items)})")
        lines.append("")
        # Group by file
        by_file: dict[str, list[Finding]] = {}
        for f in items:
            by_file.setdefault(f.file, []).append(f)
        for file, entries in sorted(by_file.items()):
            lines.append(f"### {file}")
            for f in entries:
                lines.append(f"- **{f.handler}()** (line {f.line}) — {f.detail}")
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="exit 1 if any HIGH findings (for CI)",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="write findings as JSON to PATH",
    )
    parser.add_argument(
        "--root",
        metavar="PATH",
        default=None,
        help="backend source root (default: auto-detect)",
    )
    args = parser.parse_args()

    if args.root:
        backend_root = Path(args.root).resolve()
    else:
        here = Path(__file__).resolve()
        # scripts/audit_missing_commit.py -> backend/
        backend_root = here.parent.parent

    report = AuditReport()
    for path in _walk_sources(backend_root):
        src = path.read_text(encoding="utf-8", errors="ignore")
        _scan_file(path, src, report, backend_root)

    # Sort for stable output
    report.findings.sort(key=lambda f: (f.file, f.line))

    print(_render_text(report))

    if args.json:
        Path(args.json).write_text(
            json.dumps([asdict(f) for f in report.findings], indent=2),
            encoding="utf-8",
        )

    if args.fail_on_high and any(f.severity == "high" for f in report.findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
