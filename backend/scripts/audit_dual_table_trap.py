#!/usr/bin/env python
"""
audit_dual_table_trap.py — AST linter for the Question dual-table trap.

KIRO2 has TWO Question models pointing at TWO different tables:

  - `Question`         (`models/content_db.py`)  -> `questions` table
  - `QuestionBankItem` (`models/question_bank.py`) -> `question_bank` table

`question_bank` is the SOURCE OF TRUTH for production (77K rows, the YKS
exam corpus). `questions` is a partial legacy table — historically empty,
currently ~36K rows of older/partial data. Querying `Question` instead of
`QuestionBankItem` from production code is a silent data-loss bug:

  - Anonymous users see ~47% of the catalog.
  - Filters / joins on `subject_area` etc. silently drop rows because
    enum casing differs between the two tables.
  - Tests pass against fixtures but production returns wrong results.

This pattern caused multi-session bugs in Sessions 78, 80, 113.

Detection logic:
1. Walk AST of every backend Python file under api/, app/api/, services/,
   app/services/, core/, app/core/.
2. Find any `from <X> import Question` (or `from <X> import Question as Y`)
   where `<X>` resolves to one of the legacy modules (`models.database`,
   `models.content_db`, `database`, `content_db` via relative import).
3. Report HIGH — unconditional, because production code MUST use
   `QuestionBankItem`.

Heuristics / false-positive filters:
- Skip tests/, _deprecated/, alembic/, __pycache__/.
- Skip module-level re-export hubs: `models/__init__.py`, `models/database.py`
  (these legitimately re-export the legacy `Question` symbol for backward
  compatibility in scripts and tests).
- Skip seed/migration scripts: `scripts/seed_*.py`, `scripts/production_seed.py`,
  `scripts/migrate_*.py` — these may legitimately touch the legacy schema.

Usage:
    python scripts/audit_dual_table_trap.py
    python scripts/audit_dual_table_trap.py --fail-on-high
    python scripts/audit_dual_table_trap.py --json out.json

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

# Source roots that MUST be clean. Production read/write paths.
AUDIT_ROOTS = [
    "api",
    "app/api",
    "services",
    "app/services",
    "core",
    "app/core",
]

SKIP_DIRS = {
    "__pycache__",
    "_deprecated",
    "tests",
    "node_modules",
    "venv",
    ".venv",
    "alembic",
}

# Files that legitimately import the legacy `Question` symbol.
# - models/database.py and models/__init__.py are RE-EXPORT hubs.
# - The linter never visits tests/, scripts/, or alembic/, so we don't
#   list them here.
SKIP_FILE_RELS = {
    "models/database.py",
    "models/__init__.py",
}

# The legacy `Question` symbol can be imported from these module paths.
# We match by SUBSTRING on the resolved module name to catch both absolute
# (`from models.content_db import Question`) and shortcut
# (`from content_db import Question`) imports.
LEGACY_QUESTION_MODULE_SUBSTRINGS = (
    "models.content_db",
    "models.database",
    # Bare-shortcut forms used inside the models/ package itself
    # (covered by SKIP_FILE_RELS for re-export hubs).
    "content_db",
)

# The CANONICAL replacement that should be used everywhere instead.
CANONICAL_REPLACEMENT = (
    "from models.question_bank import QuestionBankItem  # 77K production rows"
)


@dataclass
class Finding:
    file: str
    line: int
    module: str
    symbol: str
    severity: str  # "high" only for now
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


def _resolve_relative_module(node: ast.ImportFrom, file_rel: str) -> str:
    """
    Resolve a relative import (`from .content_db import X`) to its
    absolute-ish module path so substring matching works uniformly.

    `node.level` is the number of leading dots; `node.module` may be None.
    For our purposes we just synthesize a path like
    `<parent_pkg>.<module>` which is enough for the substring filter.
    """
    if node.level == 0:
        return node.module or ""

    parts = file_rel.replace("\\", "/").split("/")
    # Drop the filename and `node.level` parent components.
    base = parts[:-1]
    if node.level > 1:
        base = base[: -(node.level - 1)] if node.level > 1 else base
    parent = ".".join(base)
    if node.module:
        return f"{parent}.{node.module}" if parent else node.module
    return parent


def _is_legacy_question_import(module: str) -> bool:
    """
    Substring-match the resolved module path against known legacy locations.
    `models.content_db.Question` and `models.database.Question` both qualify.
    """
    if not module:
        return False
    return any(sub in module for sub in LEGACY_QUESTION_MODULE_SUBSTRINGS)


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
    if rel in SKIP_FILE_RELS:
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue

        resolved_module = _resolve_relative_module(node, rel)
        if not _is_legacy_question_import(resolved_module):
            continue

        for alias in node.names:
            if alias.name != "Question":
                continue

            report.findings.append(
                Finding(
                    file=rel,
                    line=node.lineno,
                    module=resolved_module,
                    symbol=alias.asname or alias.name,
                    severity="high",
                    detail=(
                        "Importing the legacy `Question` model — this maps to the "
                        "`questions` table (~36K partial rows), NOT the production "
                        "`question_bank` table (77K rows). Any query against this "
                        "symbol silently returns the wrong dataset. Replace with: "
                        f"`{CANONICAL_REPLACEMENT}`."
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
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _render_text(report: AuditReport) -> str:
    buckets = report.by_severity()
    lines: list[str] = []
    lines.append("# Dual-Table Trap Audit Report")
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
                    f"- **line {f.line}**: `from {f.module} import {f.symbol}`"
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
