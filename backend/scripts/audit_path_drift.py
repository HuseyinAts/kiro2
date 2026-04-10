"""
Path naming drift auditor.

Compares backend OpenAPI paths against frontend fetch call sites to detect:
1. Frontend fetches a path that the backend does not expose (404 risk).
2. Backend exposes duplicate English + Turkish implementations of the same
   feature (e.g. /api/v1/teacher/* AND /api/v1/ogretmen/*), which forces
   frontend devs to guess.
3. Path segments that look like "Turkish prose" where ASCII English is the
   project convention (.claude/rules/case-convention.md Endpoint Gate).

Usage:
    python backend/scripts/audit_path_drift.py            # report only
    python backend/scripts/audit_path_drift.py --json     # machine readable
    python backend/scripts/audit_path_drift.py --fail     # exit 1 on drift
                                                          # (for CI gate)

Input sources:
    - Backend: live OpenAPI at http://localhost:8000/openapi.json
    - Frontend: grep `fetch(...)`, `apiClient(...)`, `axios.<method>(...)`
                under frontend/src/**

Output: markdown report on stdout (and docs/audits/ if --write)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = ROOT / "frontend" / "src"
AUDITS_DIR = ROOT / "docs" / "audits"

# Known Turkish segments that have an English counterpart in the backend.
# Add new entries as duplicate implementations are discovered; the goal is
# to drive this list to {} as legacy paths are removed.
TR_EN_SYNONYMS: dict[str, str] = {
    "ogretmen": "teacher",
    "ogrenci": "student",
    "veli": "parent",
    "soru": "question",
    "sorular": "questions",
    "konular": "topics",
    "rapor": "report",
    "raporlar": "reports",
    "bildirim": "notification",
    "bildirimler": "notifications",
    "istatistikler": "stats",
    "cocuklar": "children",
    "cocuk": "child",
    "sinav": "exam",
    "hesapla": "compute",
    "gecmis": "history",
    "profil": "profile",
    "onay-talebi-olustur": "approval-requests",
    "onay-talepleri": "approval-requests",
}

# Path segments that are legitimate Turkish domain terms (no English synonym
# in the backend) — do not flag these.
TR_ALLOWLIST = {
    "bilge-alp",  # product name
    "soru-meydani",  # product name
    "oba-seferleri",  # product name
    "birlikte-streak",  # product name
    "usta-cirak",  # product name
    "cozum-duellosu",  # product name
    "zpd-maarif",  # product name
    "kvkk",  # regulation
    "sinav-gecmisi",  # legacy fixed endpoint
    "profil-guncelle",  # legacy fixed endpoint
}


def _fetch_openapi_paths(url: str) -> set[str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
            spec = json.load(resp)
    except Exception as exc:
        print(f"ERROR: could not fetch {url}: {exc}", file=sys.stderr)
        sys.exit(2)
    return set(spec.get("paths", {}).keys())


_FETCH_RE = re.compile(
    r"(?:fetch|apiClient|api|axios\.(?:get|post|put|delete|patch))"
    r"\(\s*[\"'`]([^\"'`]+)[\"'`]"
)


def _scan_frontend_fetch_calls(src: Path) -> dict[str, list[str]]:
    """Return {path: [source_file:line, ...]}."""
    hits: dict[str, list[str]] = defaultdict(list)
    for fp in src.rglob("*.ts*"):
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in _FETCH_RE.finditer(content):
            raw = match.group(1)
            if not raw.startswith("/api"):
                continue
            # Strip query string and template placeholders for comparison
            path = raw.split("?", 1)[0]
            path = re.sub(r"\$\{[^}]+\}", "{x}", path)
            line = content[: match.start()].count("\n") + 1
            hits[path].append(f"{fp.relative_to(ROOT)}:{line}")
    return hits


def _normalize_path_pattern(path: str) -> str:
    """Normalize {param} and ${x} placeholders so frontend/backend can match."""
    return re.sub(r"\{[^}]+\}", "{x}", path)


def _detect_tr_en_duplicates(backend_paths: set[str]) -> list[tuple[str, str]]:
    """Return [(turkish_path, english_equivalent_or_'')...] pairs."""
    duplicates: list[tuple[str, str]] = []
    for bp in sorted(backend_paths):
        for tr, en in TR_EN_SYNONYMS.items():
            if tr in TR_ALLOWLIST:
                continue
            # Match whole segments only
            if re.search(rf"/{re.escape(tr)}(/|$)", bp):
                candidate = re.sub(rf"/{re.escape(tr)}(/|$)", f"/{en}\\1", bp)
                if candidate in backend_paths and candidate != bp:
                    duplicates.append((bp, candidate))
                else:
                    duplicates.append((bp, ""))
                break
    return duplicates


def _detect_frontend_404_risk(
    frontend: dict[str, list[str]], backend: set[str]
) -> list[tuple[str, list[str]]]:
    """Frontend calls a path that doesn't exist in OpenAPI."""
    backend_norm = {_normalize_path_pattern(p) for p in backend}
    missing: list[tuple[str, list[str]]] = []
    for path, callers in sorted(frontend.items()):
        norm = _normalize_path_pattern(path)
        if norm not in backend_norm:
            missing.append((path, callers))
    return missing


def build_report(openapi_url: str) -> tuple[str, int]:
    backend_paths = _fetch_openapi_paths(openapi_url)
    frontend_calls = _scan_frontend_fetch_calls(FRONTEND_SRC)

    duplicates = _detect_tr_en_duplicates(backend_paths)
    missing = _detect_frontend_404_risk(frontend_calls, backend_paths)

    drift_count = sum(1 for _, en in duplicates if en) + len(missing)

    lines = [
        f"# Path Naming Drift Report — {date.today().isoformat()}",
        "",
        f"**Source:** {openapi_url}",
        f"**Backend paths:** {len(backend_paths)}",
        f"**Frontend fetch sites:** {sum(len(v) for v in frontend_calls.values())}",
        f"**Unique frontend paths:** {len(frontend_calls)}",
        "",
        "## 1. TR/EN Duplicate Implementations (backend)",
        "",
        "Both Turkish and English variants exist in OpenAPI. Frontend must guess.",
        "Goal: drive this section to empty by removing the legacy Turkish variant.",
        "",
    ]
    real_dups = [(tr, en) for tr, en in duplicates if en]
    if real_dups:
        lines.append("| Legacy (TR) | Canonical (EN) |")
        lines.append("|---|---|")
        for tr, en in real_dups:
            lines.append(f"| `{tr}` | `{en}` |")
    else:
        lines.append("_None — clean._")
    lines.append("")

    lines.extend(
        [
            "## 2. Turkish-Only Backend Paths (no English equivalent)",
            "",
            "These exist only in Turkish form. Either rename to English or add",
            "to `TR_ALLOWLIST` if they are intentional product names.",
            "",
        ]
    )
    tr_only = [(tr, en) for tr, en in duplicates if not en]
    if tr_only:
        for tr, _ in tr_only:
            lines.append(f"- `{tr}`")
    else:
        lines.append("_None._")
    lines.append("")

    lines.extend(
        [
            "## 3. Frontend 404 Risk (fetch → missing endpoint)",
            "",
            "Frontend calls a path that is NOT in the backend OpenAPI.",
            "Either the endpoint was removed/renamed or the frontend has a typo.",
            "",
        ]
    )
    if missing:
        for path, callers in missing:
            lines.append(f"- `{path}`")
            for caller in callers[:3]:
                lines.append(f"  - {caller}")
            if len(callers) > 3:
                lines.append(f"  - … (+{len(callers) - 3} more)")
    else:
        lines.append("_None — clean._")
    lines.append("")

    lines.append(f"**Total drift items:** {drift_count}")
    return "\n".join(lines), drift_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="http://localhost:8000/openapi.json",
        help="OpenAPI URL (default: local backend)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON instead of markdown"
    )
    parser.add_argument(
        "--fail",
        action="store_true",
        help="Exit 1 if any drift is detected (CI gate mode)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Also write the report under {AUDITS_DIR}",
    )
    args = parser.parse_args()

    report, drift = build_report(args.url)

    if args.json:
        print(json.dumps({"drift_count": drift, "report": report}))
    else:
        print(report)

    if args.write:
        AUDITS_DIR.mkdir(parents=True, exist_ok=True)
        out = AUDITS_DIR / f"{date.today().isoformat()}_path-drift.md"
        out.write_text(report, encoding="utf-8")
        print(f"\n[written] {out}", file=sys.stderr)

    if args.fail and drift:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
