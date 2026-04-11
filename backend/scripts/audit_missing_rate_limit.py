#!/usr/bin/env python
"""
audit_missing_rate_limit.py — AST linter for cost-abuse rate-limit gaps
on LLM/TTS/embedding endpoints.

Background
----------
Session 138 (Category B1) plugged the missing-auth holes on cost-abuse
endpoints (Gemini, OpenAI, Claude, Qwen, gTTS, embedding services). Auth
prevents *anonymous* abuse, but it doesn't prevent a single authenticated
user from issuing 1,000 requests in 60 seconds. The second layer of
defense is a per-key / per-IP rate limit (slowapi `@limiter.limit` or the
local `@rate_limit` helper used in learning_path_v2.py).

This linter catches handlers that:
1. Live in a file whose module-level imports include an LLM / TTS /
   embedding sentinel (`core.llm_*`, `services.llm.*`, `gtts`, `openai`,
   `anthropic`, `google.generativeai`, `dashscope`, `litellm`, ...).
2. Are decorated with a WRITE HTTP method (POST/PUT/PATCH/DELETE) —
   compute always happens on the write path; GET is filtered out so we
   don't catch health/info/listing handlers that merely import a sentinel
   for type hints or status checks.
3. Live on a non-status path (skip `/health`, `/info`, `/voices`,
   `/sessions`, `/metrics`, `/llm-pool`, `/vector-store`, `/cache`,
   `/rag-pipeline`, `/stats`).
4. Do NOT carry any of the recognized rate-limit decorators:
     - `@rate_limit("...")`               (local helper, learning_path_v2)
     - `@limiter.limit("...")`            (slowapi direct)
     - `@limit("...")`                    (re-exported alias)

Severity
--------
HIGH only. The current production baseline is 16 — every finding is a
real cost-abuse exposure. The gate is intentionally NOT wired into CI
yet; a follow-up sweep should add `@limiter.limit(...)` to the 16
endpoints, after which `--fail-on-high` can be enabled.

Usage
-----
    python scripts/audit_missing_rate_limit.py
    python scripts/audit_missing_rate_limit.py --fail-on-high
    python scripts/audit_missing_rate_limit.py --json out.json

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

# Handler-only scope.
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

# WRITE methods only — compute happens on the write path. Status/info
# handlers are GET and skipped automatically.
WRITE_METHODS = {"post", "put", "patch", "delete"}

# Internal sentinel module path prefixes / substrings. A handler file
# whose module-level imports touch any of these is treated as compute-
# bearing.
SENTINEL_INTERNAL_SUBSTRINGS = (
    "core.llm_",
    "core.embedding_",
    "core.hybrid_llm",
    "core.langchain_llm",
    "core.gemini",
    "core.qwen",
    "core.dashscope",
    "core.text_to_speech",
    "services.llm.",
    "services.embedding_service",
    "services.tts_",
    "services.question_parser.gemini_ocr",
)

# Third-party sentinel packages. We match exact name OR `<name>.<sub>`.
SENTINEL_THIRD_PARTY = (
    "openai",
    "anthropic",
    "google.generativeai",
    "google.genai",
    "gtts",
    "dashscope",
    "litellm",
)

# Path substrings that indicate a status / info / listing handler — even
# on a WRITE method, these are not LLM-compute paths and are skipped to
# avoid false positives.
SKIP_PATH_SUBSTRINGS = (
    "/health",
    "/ready",
    "/live",
    "/info",
    "/metrics",
    "/voices",
    "/sessions",
    "/llm-pool",
    "/vector-store",
    "/cache",
    "/rag-pipeline",
    "/stats",
)


@dataclass
class Finding:
    file: str
    line: int
    handler: str
    method: str
    path: str
    sentinel: str
    severity: str  # "high"
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


def _is_sentinel(module: str) -> bool:
    if not module:
        return False
    if any(s in module for s in SENTINEL_INTERNAL_SUBSTRINGS):
        return True
    for tp in SENTINEL_THIRD_PARTY:
        if module == tp or module.startswith(tp + "."):
            return True
    return False


def _file_imports_sentinel(tree: ast.Module) -> str | None:
    """Return the first sentinel module name imported, or None."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if _is_sentinel(node.module or ""):
                return node.module or "<unknown>"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _is_sentinel(alias.name):
                    return alias.name
    return None


def _router_decorator(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> tuple[str, str] | None:
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in ("router", "app")
            and func.attr in WRITE_METHODS
        ):
            method = func.attr
            path = ""
            if dec.args and isinstance(dec.args[0], ast.Constant):
                val = dec.args[0].value
                if isinstance(val, str):
                    path = val
            return method, path
    return None


def _has_rate_limit_decorator(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> bool:
    """
    Recognises:
      - @rate_limit("...")
      - @limiter.limit("...")
      - @limit("...")  (rare alias)
    """
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            f = dec.func
            if isinstance(f, ast.Name) and f.id in ("rate_limit", "limit"):
                return True
            if isinstance(f, ast.Attribute) and f.attr == "limit":
                # @limiter.limit(...) — accept any `<NAME>.limit(...)`
                # (`limiter`, `slow_limiter`, etc.) and module-attr forms.
                return True
        elif isinstance(dec, ast.Name) and dec.id in ("rate_limit", "limit"):
            return True
    return False


def _router_prefix_from_module(tree: ast.Module) -> str:
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

    sentinel = _file_imports_sentinel(tree)
    if sentinel is None:
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

        if any(sub in full_path.lower() for sub in SKIP_PATH_SUBSTRINGS):
            continue

        if _has_rate_limit_decorator(fn):
            continue

        report.findings.append(
            Finding(
                file=rel,
                line=fn.lineno,
                handler=fn.name,
                method=method.upper(),
                path=full_path,
                sentinel=sentinel,
                severity="high",
                detail=(
                    f"Cost-bearing write endpoint imports `{sentinel}` but "
                    "carries no rate-limit decorator. An authenticated user "
                    "can issue unlimited requests, burning LLM / TTS / "
                    'embedding API quota. Add `@limiter.limit("10/minute")` '
                    "from `core.ddos_protection` (also requires a "
                    "`request: Request` parameter — slowapi convention). For "
                    'the local helper, use `@rate_limit("key")` and add '
                    "`key` to RATE_LIMITS in the same module."
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
    lines.append("# Missing Rate-Limit Audit Report")
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
            lines.append(f"_sentinel: `{entries[0].sentinel}`_")
            for f in entries:
                lines.append(
                    f"- **{f.method} {f.path}** -> `{f.handler}()` (line {f.line})"
                )
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
