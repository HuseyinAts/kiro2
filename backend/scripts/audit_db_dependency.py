#!/usr/bin/env python
"""
audit_db_dependency.py — AST linter for Pattern A + Pattern B.

Session 136 Golden Flow sweep surfaced two recurring half-working feature
traps. This linter turns them into a deterministic CI gate.

Pattern A — sync `get_db` / async handler mismatch
    `from core.database import get_db` returns a SYNC generator (yields
    sqlalchemy.orm.Session). Any FastAPI handler annotated with
    `db: AsyncSession = Depends(get_db)` silently gets a sync Session
    injected. First `await db.execute(...)` raises MissingGreenlet → 500.

Pattern B — `TokenPayload.id` AttributeError
    `core.jwt_auth.get_current_user` returns a Pydantic `TokenPayload`
    whose user_id field is `sub`, not `id`. Any handler doing
    `current_user.id` on a TokenPayload raises AttributeError → 500.

Usage:
    python scripts/audit_db_dependency.py                 # report
    python scripts/audit_db_dependency.py --fail          # exit 1 on hits
    python scripts/audit_db_dependency.py --json report.json

Exit codes:
    0  — clean (or report-only mode)
    1  — violations found AND --fail passed
    2  — internal parse error
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Only audit production source under these roots (not tests, not _deprecated)
AUDIT_ROOTS = ["api", "app/api", "app/services", "core", "services", "analytics"]
SKIP_DIRS = {"__pycache__", "_deprecated", "tests", "node_modules", "venv", ".venv"}

# The import signature that is the root cause of Pattern A.
# `from core.database import get_db` — sync generator yielding sync Session.
BAD_SYNC_GET_DB_MODULE = "core.database"


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    pattern: str  # "A-await-db" | "A-type-mismatch" | "B-tokenpayload-id"
    file: str
    line: int
    handler: str | None  # function name if inside a function
    detail: str
    severity: str  # "high" | "medium" | "low"


@dataclass
class AuditReport:
    pattern_a_broken: list[Finding] = field(default_factory=list)
    pattern_a_typed_mismatch: list[Finding] = field(default_factory=list)
    pattern_b: list[Finding] = field(default_factory=list)

    def total(self) -> int:
        return (
            len(self.pattern_a_broken)
            + len(self.pattern_a_typed_mismatch)
            + len(self.pattern_b)
        )

    def by_file(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {}
        for f in self.pattern_a_broken + self.pattern_a_typed_mismatch + self.pattern_b:
            out.setdefault(f.file, []).append(f)
        return out


# ---------------------------------------------------------------------------
# Pattern A detector
# ---------------------------------------------------------------------------


def _is_depends_get_db(default: ast.expr | None) -> bool:
    """Return True if default expression is `Depends(get_db)`."""
    if not isinstance(default, ast.Call):
        return False
    func = default.func
    if (isinstance(func, ast.Name) and func.id == "Depends") or (
        isinstance(func, ast.Attribute) and func.attr == "Depends"
    ):
        pass
    else:
        return False
    if len(default.args) != 1:
        return False
    arg = default.args[0]
    return isinstance(arg, ast.Name) and arg.id == "get_db"


def _annotation_is_async_session(ann: ast.expr | None) -> bool:
    if ann is None:
        return False
    try:
        return ast.unparse(ann) == "AsyncSession"
    except Exception:
        return False


def _handler_uses_await_db(node: ast.AsyncFunctionDef, db_name: str) -> bool:
    """Does the handler body contain `await db.something(...)`?"""
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Await):
            continue
        target = sub.value
        # Pattern: await db.execute(...) / await db.commit() / await db.refresh()
        if isinstance(target, ast.Call):
            callee = target.func
            if (
                isinstance(callee, ast.Attribute)
                and isinstance(callee.value, ast.Name)
                and callee.value.id == db_name
            ):
                return True
        # Pattern: await db.something (rare)
        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name) and target.value.id == db_name:
                return True
    return False


def _imports_sync_get_db(tree: ast.Module) -> bool:
    """Does this module import `get_db` from `core.database`?"""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != BAD_SYNC_GET_DB_MODULE:
            continue
        for alias in node.names:
            if alias.name == "get_db":
                return True
    return False


def _scan_pattern_a(
    path: Path, src: str, tree: ast.Module, report: AuditReport
) -> None:
    if not _imports_sync_get_db(tree):
        return  # file uses async get_db — not a candidate

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue

        # Find args with `AsyncSession = Depends(get_db)` signature.
        # Build arg_name -> (annotation, default) map.
        args_list = list(node.args.args) + list(node.args.kwonlyargs)
        defaults_list = list(node.args.defaults) + list(node.args.kw_defaults)
        # Pad defaults to match args
        pad = len(node.args.args) - len(node.args.defaults)
        normal_defaults: list[ast.expr | None] = [None] * pad + list(node.args.defaults)
        kw_defaults = list(node.args.kw_defaults)
        all_args = list(node.args.args) + list(node.args.kwonlyargs)
        all_defaults: list[ast.expr | None] = normal_defaults + kw_defaults

        for arg, default in zip(all_args, all_defaults, strict=False):
            if default is None:
                continue
            if not _is_depends_get_db(default):
                continue
            if not _annotation_is_async_session(arg.annotation):
                continue
            # MATCH — this is a Pattern A mismatch. Check if handler actually
            # awaits on that variable (high severity) or not (medium — type lie).
            db_name = arg.arg
            if _handler_uses_await_db(node, db_name):
                report.pattern_a_broken.append(
                    Finding(
                        pattern="A-await-db",
                        file=str(path).replace("\\", "/"),
                        line=node.lineno,
                        handler=node.name,
                        detail=(
                            f"`{db_name}: AsyncSession = Depends(get_db)` and the "
                            f"handler does `await {db_name}.*(...)`. get_db from "
                            f"core.database is a SYNC generator — this will "
                            f"MissingGreenlet-500 on first call."
                        ),
                        severity="high",
                    )
                )
            else:
                report.pattern_a_typed_mismatch.append(
                    Finding(
                        pattern="A-type-mismatch",
                        file=str(path).replace("\\", "/"),
                        line=node.lineno,
                        handler=node.name,
                        detail=(
                            f"`{db_name}: AsyncSession = Depends(get_db)` but "
                            f"handler does not `await {db_name}.*`. Type lie: "
                            f"annotation says AsyncSession, runtime gets sync "
                            f"Session. Working today but undefined if migrated."
                        ),
                        severity="medium",
                    )
                )


# ---------------------------------------------------------------------------
# Pattern B detector
# ---------------------------------------------------------------------------


def _imports_jwt_get_current_user(tree: ast.Module) -> bool:
    """Does this module import get_current_user from core.jwt_auth?"""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "core.jwt_auth":
            continue
        for alias in node.names:
            if alias.name == "get_current_user":
                return True
    return False


def _find_token_payload_id_uses(tree: ast.Module, source: str) -> list[tuple[int, str]]:
    """
    Walk module looking for `<var>.id` where <var> is annotated as TokenPayload
    OR where the default is `Depends(get_current_user)` in a handler that
    imported from core.jwt_auth.

    Simpler heuristic: find all handlers with either:
      - `current_user: TokenPayload = Depends(get_current_user)`
      - `current_user = Depends(get_current_user)` (no annotation, implicit TokenPayload)
    Then look for `current_user.id` in that handler body.
    """
    out: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Find parameter named current_user with Depends(get_current_user)
        args_list = list(node.args.args) + list(node.args.kwonlyargs)
        pad = len(node.args.args) - len(node.args.defaults)
        normal_defaults: list[ast.expr | None] = [None] * pad + list(node.args.defaults)
        kw_defaults = list(node.args.kw_defaults)
        all_defaults: list[ast.expr | None] = normal_defaults + kw_defaults

        suspect_name: str | None = None
        for arg, default in zip(args_list, all_defaults, strict=False):
            if default is None:
                continue
            if not isinstance(default, ast.Call):
                continue
            func = default.func
            name = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )
            if name != "Depends":
                continue
            if not default.args:
                continue
            a0 = default.args[0]
            if not (isinstance(a0, ast.Name) and a0.id == "get_current_user"):
                continue
            # core.jwt_auth.get_current_user ALWAYS returns TokenPayload at
            # runtime, regardless of annotation. So any .id access on this
            # parameter is a bug — TokenPayload only has .sub. The annotation
            # is a type-lie that mypy can't catch because it never runs the
            # FastAPI dep resolver. Only exception: if the annotation is
            # explicitly AuthenticatedUser — that means the developer is
            # aware there's a mismatch and is shadowing the return value via
            # a wrapper dependency (we'd still want a separate check but
            # that's rare; skip it).
            try:
                ann = ast.unparse(arg.annotation) if arg.annotation else ""
            except Exception:
                ann = ""
            if "AuthenticatedUser" in ann:
                continue  # explicit wrapper — separate concern
            suspect_name = arg.arg

        if suspect_name is None:
            continue

        # Walk body looking for `<suspect_name>.id` attribute access.
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.Attribute)
                and sub.attr == "id"
                and isinstance(sub.value, ast.Name)
                and sub.value.id == suspect_name
            ):
                out.append((sub.lineno, node.name))

    return out


def _scan_pattern_b(
    path: Path, src: str, tree: ast.Module, report: AuditReport
) -> None:
    if not _imports_jwt_get_current_user(tree):
        return

    hits = _find_token_payload_id_uses(tree, src)
    for lineno, handler in hits:
        report.pattern_b.append(
            Finding(
                pattern="B-tokenpayload-id",
                file=str(path).replace("\\", "/"),
                line=lineno,
                handler=handler,
                detail=(
                    "`current_user.id` on a TokenPayload (jwt_auth.get_current_user "
                    "returns Pydantic TokenPayload whose user_id field is `sub`). "
                    "Use `current_user.sub` or re-type annotation to AuthenticatedUser."
                ),
                severity="high",
            )
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def iter_python_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for audit_sub in AUDIT_ROOTS:
        base = root / audit_sub
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(".py"):
                    out.append(Path(dirpath) / fn)
    return out


def audit(root: Path) -> AuditReport:
    report = AuditReport()
    for path in iter_python_files(root):
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"  parse error: {path}: {e}", file=sys.stderr)
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        _scan_pattern_a(rel, src, tree, report)
        _scan_pattern_b(rel, src, tree, report)
    return report


def format_report(report: AuditReport) -> str:
    out: list[str] = []
    out.append(
        "# DB Dependency Audit — Pattern A (sync get_db) + Pattern B (TokenPayload.id)"
    )
    out.append("")
    total = report.total()
    out.append(f"**Total findings:** {total}")
    out.append(f"  - Pattern A (broken, await db.*): {len(report.pattern_a_broken)}")
    out.append(
        f"  - Pattern A (type lie, no await): {len(report.pattern_a_typed_mismatch)}"
    )
    out.append(f"  - Pattern B (TokenPayload.id): {len(report.pattern_b)}")
    out.append("")

    by_file = report.by_file()
    if not by_file:
        out.append("_Clean — no Pattern A/B mismatches detected._")
        return "\n".join(out)

    out.append("## Findings by file")
    out.append("")
    for file_path in sorted(by_file.keys()):
        findings = by_file[file_path]
        high = sum(1 for f in findings if f.severity == "high")
        med = sum(1 for f in findings if f.severity == "medium")
        out.append(f"### {file_path}  (high={high}, medium={med})")
        for f in findings:
            prefix = "[HIGH]" if f.severity == "high" else "[MED] "
            handler = f.handler or "<module>"
            out.append(f"  {prefix} :{f.line}  {handler}()  — {f.pattern}")
            out.append(f"         {f.detail}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail", action="store_true", help="Exit 1 if findings > 0")
    parser.add_argument("--json", type=str, help="Write JSON report to path")
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Backend root (default: parent of this script's dir)",
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parents[1]
    if not (root / "core").exists():
        print(f"error: root does not look like backend/: {root}", file=sys.stderr)
        return 2

    report = audit(root)
    text = format_report(report)
    # Force UTF-8 on Windows terminals
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")

    if args.json:
        data = {
            "pattern_a_broken": [asdict(f) for f in report.pattern_a_broken],
            "pattern_a_typed_mismatch": [
                asdict(f) for f in report.pattern_a_typed_mismatch
            ],
            "pattern_b": [asdict(f) for f in report.pattern_b],
            "totals": {
                "a_broken": len(report.pattern_a_broken),
                "a_typed": len(report.pattern_a_typed_mismatch),
                "b": len(report.pattern_b),
                "all": report.total(),
            },
        }
        Path(args.json).write_text(json.dumps(data, indent=2), encoding="utf-8")

    if args.fail and report.total() > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
