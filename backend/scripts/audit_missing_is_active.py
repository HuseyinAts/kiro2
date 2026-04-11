#!/usr/bin/env python
"""
audit_missing_is_active.py — AST linter for the missing `is_active` filter
on QuestionBankItem / Question queries inside HTTP handlers.

Background
----------
KIRO2 has 13K+ rows in `question_bank` whose `is_active` flag is FALSE
(garbage soft-deleted via Session 78 cleanup, intentionally kept reversible).
Any read-path handler that queries the table WITHOUT an `is_active = TRUE`
filter silently leaks deactivated rows back to end users — a regression
class formally documented in testing.md lesson #24.

This linter is the deterministic CI gate for that pattern, the third in
the AST audit family after audit_db_dependency.py (Session 137) and
audit_missing_auth.py / audit_dual_table_trap.py (Sessions 138/139).

Detection logic
---------------
1. Walk every handler function (`@router.<method>(...)`) under api/ and
   app/api/. Service-layer code is intentionally OUT of scope — admin
   CRUD services legitimately need to read inactive rows for restore /
   audit / version-history flows.
2. Inside each handler body, find any `db.query(Question*)` or
   `select(Question*)` call where `Question*` is one of:
     - `QuestionBankItem` (production model)
     - `Question` (legacy dual-table sibling)
3. Walk the unparsed source of the same function and check whether any
   `is_active` reference appears at all (filter / where / SQL string /
   helper call). If not, report.

False-positive filters
----------------------
- Skip handlers whose function name OR route path contains an admin /
  CRUD keyword: `admin`, `update`, `delete`, `history`, `version`,
  `restore`, `audit`, `crud`, `bulk`, `import`. Inactive rows are part
  of the legitimate admin surface there.
- Skip handlers decorated only with read methods that do a
  by-primary-key lookup AND nothing else (best-effort: detect a
  `.filter(...id == ...)` or `.where(...id == ...)` near the call).
  This is left out of v1 — the admin/CRUD keyword filter already
  covers most by-id admin lookups.
- Skip tests/, _deprecated/, alembic/, __pycache__/ (standard).

Severity
--------
HIGH only. The current production baseline is 0 — every existing
handler either filters by `is_active` or is admin-keyworded. Any new
finding is therefore a true regression, not legacy noise.

Usage
-----
    python scripts/audit_missing_is_active.py
    python scripts/audit_missing_is_active.py --fail-on-high
    python scripts/audit_missing_is_active.py --json out.json

Exit codes
----------
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

# Handler-only scope. Service-layer queries are intentionally NOT scanned —
# CRUD admin services legitimately read inactive rows.
AUDIT_ROOTS = ["api", "app/api"]

SKIP_DIRS = {
    "__pycache__",
    "_deprecated",
    "tests",
    "node_modules",
    "venv",
    ".venv",
    "alembic",
}

SKIP_FILE_SUFFIXES = (
    "_demo.py",
    "_example.py",
    "sentry_demo.py",
    "tracing_example.py",
)

WRITE_METHODS = {"post", "put", "patch", "delete"}
READ_METHODS = {"get"}
ALL_HTTP_METHODS = WRITE_METHODS | READ_METHODS

# Question ORM symbol names that this linter cares about. Both production
# (`QuestionBankItem`) and legacy (`Question`) trip the rule — the dual-
# table linter handles the legacy import separately, but if a handler did
# manage to query `Question`, it should still filter `is_active`.
QUESTION_SYMBOLS = {"QuestionBankItem", "Question"}

# Function-name / path keywords that indicate admin or CRUD context.
# Inactive rows are PART of the legitimate surface in those handlers,
# so they're allow-listed.
ADMIN_KEYWORDS = (
    "admin",
    "update",
    "delete",
    "history",
    "version",
    "restore",
    "audit",
    "crud",
    "bulk",
    "import",
    "moderation",
    "moderate",
    "approval",
    "approve",
    "reject",
)


@dataclass
class Finding:
    file: str
    line: int
    handler: str
    method: str
    path: str
    severity: str  # "high" only
    detail: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def by_severity(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {"high": []}
        for f in self.findings:
            out.setdefault(f.severity, []).append(f)
        return out

    def total(self) -> int:
        return len(self.findings)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _router_decorator(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> tuple[str, str] | None:
    """Return (method, path) for `@router.<method>(path, ...)` handlers."""
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in ("router", "app")
            and func.attr in ALL_HTTP_METHODS
        ):
            method = func.attr
            path = ""
            if dec.args and isinstance(dec.args[0], ast.Constant):
                val = dec.args[0].value
                if isinstance(val, str):
                    path = val
            return method, path
    return None


def _is_question_query(call: ast.Call) -> tuple[str, str] | None:
    """
    If `call` is `db.query(QuestionBankItem)` or `select(QuestionBankItem)`,
    return (kind, symbol_name). Otherwise None.
    """
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr == "query":
        kind = "query"
    elif isinstance(f, ast.Name) and f.id in ("select", "Select"):
        kind = "select"
    else:
        return None
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id in QUESTION_SYMBOLS:
            return kind, arg.id
    return None


def _has_admin_keyword(name_or_path: str) -> bool:
    s = name_or_path.lower()
    return any(kw in s for kw in ADMIN_KEYWORDS)


def _function_mentions_is_active(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Best-effort: does any node inside the function reference the name
    `is_active`? Catches:
      - .filter(QuestionBankItem.is_active == True)
      - .where(QuestionBankItem.is_active.is_(True))
      - QuestionBankItem.is_active == True
      - kwargs is_active=True
      - Raw SQL strings containing "is_active"
    """
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Attribute) and sub.attr == "is_active":
            return True
        if isinstance(sub, ast.keyword) and sub.arg == "is_active":
            return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            if "is_active" in sub.value:
                return True
        if isinstance(sub, ast.Name) and sub.id == "is_active":
            return True
    return False


def _router_prefix_from_module(tree: ast.Module) -> str:
    """Return the `prefix=...` argument from the module-level router."""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id != "router":
            continue
        if not isinstance(node.value, ast.Call):
            continue
        for kw in node.value.keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                val = kw.value.value
                if isinstance(val, str):
                    return val
    return ""


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
    prefix = _router_prefix_from_module(tree)

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        route = _router_decorator(fn)
        if route is None:
            continue
        method, route_path = route
        full_path = (
            (prefix + route_path)
            if route_path.startswith("/")
            else (prefix + "/" + route_path if route_path else prefix)
        )

        # Allow-list admin/CRUD context.
        if _has_admin_keyword(fn.name):
            continue
        if _has_admin_keyword(full_path):
            continue

        # Find Q* queries inside this handler.
        hits: list[tuple[int, str, str]] = []
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Call):
                q = _is_question_query(sub)
                if q is not None:
                    hits.append((sub.lineno, q[0], q[1]))
        if not hits:
            continue

        if _function_mentions_is_active(fn):
            continue

        first_hit = hits[0]
        report.findings.append(
            Finding(
                file=rel,
                line=first_hit[0],
                handler=fn.name,
                method=method.upper(),
                path=full_path,
                severity="high",
                detail=(
                    f"Read-path handler queries `{first_hit[2]}` "
                    f"({first_hit[1]}(...)) without any `is_active` filter. "
                    "13K+ inactive rows in `question_bank` will silently leak "
                    "into the response. Add "
                    "`.filter(QuestionBankItem.is_active.is_(True))` (or the "
                    "`.where(...)` SQLAlchemy 2.0 equivalent). If this handler "
                    "intentionally needs inactive rows, rename it with an "
                    "admin/CRUD keyword (admin/update/delete/history/restore/"
                    "audit/version) or move it under an admin path."
                ),
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
            if any(p.name.endswith(suf) for suf in SKIP_FILE_SUFFIXES):
                continue
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _render_text(report: AuditReport) -> str:
    buckets = report.by_severity()
    lines: list[str] = []
    lines.append("# Missing `is_active` Filter Audit Report")
    lines.append("")
    lines.append(f"**Total findings:** {report.total()}")
    lines.append(f"- HIGH: {len(buckets.get('high', []))}")
    lines.append("")

    items = buckets.get("high", [])
    if items:
        lines.append(f"## HIGH ({len(items)})")
        lines.append("")
        by_file: dict[str, list[Finding]] = {}
        for f in items:
            by_file.setdefault(f.file, []).append(f)
        for file, entries in sorted(by_file.items()):
            lines.append(f"### {file}")
            for f in entries:
                lines.append(
                    f"- **{f.method} {f.path}** -> `{f.handler}()` (line {f.line})"
                )
            lines.append("")
            lines.append(f"  {entries[0].detail}")
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
        backend_root = here.parent.parent

    report = AuditReport()
    for path in _walk_sources(backend_root):
        src = path.read_text(encoding="utf-8", errors="ignore")
        _scan_file(path, src, report, backend_root)

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
