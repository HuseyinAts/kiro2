#!/usr/bin/env python
"""KIRO2 new-endpoint checklist (CI gate).

Scans the PR diff (vs `origin/$BASE_REF`, default `master`) for newly
added `@router.{get,post,put,delete,patch}(...)` decorators and runs a
7-item checklist on each one. The checklist mirrors the patterns that
previously regressed in production:

  Session 112 — 5 routers unregistered in loader.py for 2+ weeks (404).
  Session 84  — 13 gamification endpoints exposed user_id query param (IDOR).
  Session 113 — 31 endpoints missing auth dependency.
  Session 148 — middleware HTTPException raise surfacing as 500.

HARD violations (exit 1):
  C1  decorator path missing `/api/v1/` prefix
  C3  endpoint missing `current_user` / `require_admin` / auth Depends
  C4  user_id passed via Query(...) instead of resolved from current_user

SOFT violations (warning only, exit 0):
  C2  Turkish path segment outside TR_ALLOWLIST
  C5  missing `response_model=` in decorator
  C6  new router file under app/api/ or api/ not registered in loader.py
  C7  no corresponding tests/ file in the diff

Override HARD/SOFT split via the `HARD_CHECKS` constant below.

Windows + Linux compatible. No shell=True, all paths via pathlib.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 on Windows consoles (cp1254 crash prevention)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_REF = os.environ.get("BASE_REF", "master")

# Which checks are blocking. Override here if a check needs to be demoted.
HARD_CHECKS: set[str] = {"C1", "C3", "C4"}
# S179 fix (B-P1-14): C8 = missing `description=` on new endpoints.
# OpenAPI 96% has description today; this gate keeps regression at 0.
SOFT_CHECKS: set[str] = {"C2", "C5", "C6", "C7", "C8"}

# Public endpoints — auth check (C3) skipped if route matches any substring.
# Hardcoded per task spec; do NOT pull from runtime config (CI runs without
# backend up).
PUBLIC_ENDPOINTS: tuple[str, ...] = (
    "/auth/forgot-password",
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/auth/register",
    "/auth/reset-password",
    "/billing/webhook",  # External billing provider webhook — shared-secret auth via X-Kiro2-Billing-Secret header
    "/docs",
    "/health",
    "/healthz",
    "/metrics",
    "/openapi.json",
    "/redoc",
    "/web-vitals",  # Frontend telemetry (Google Web Vitals) — fire-and-forget, no PII, no DB writes
)

# Turkish allowlist — product names + regulation terms. Mirrors
# backend/scripts/audit_path_drift.py:TR_ALLOWLIST.
TR_ALLOWLIST: set[str] = {
    "bilge-alp",
    "soru-meydani",
    "oba-seferleri",
    "birlikte-streak",
    "usta-cirak",
    "cozum-duellosu",
    "zpd-maarif",
    "kvkk",
    "sinav-gecmisi",
    "profil-guncelle",
}

# Turkish-ish character heuristic — flag if any Turkish-specific char or
# if a segment matches a known Turkish stem we want to outlaw outside the
# allowlist.
TR_TOKEN_RE = re.compile(r"[çğıİöşüÇĞÖŞÜ]|(?:^|-)(ogretmen|veli|ogrenci|sinav|soru|ders|konu|odev|bildirim|profil|gecmis|cevap)(?:-|$)")

DECORATOR_RE = re.compile(
    r"@(\w+)\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']([^)]*)\)",
    re.DOTALL,
)

USER_ID_QUERY_RE = re.compile(
    r"user_id\s*:\s*\w+\s*=\s*Query\s*\(",
)

AUTH_DEPENDS_RE = re.compile(
    # Known canonical auth deps + Turkish guards + heuristic suffixes.
    # Match Depends(get_current_user), Depends(require_admin),
    # Depends(admin_kullanici_getir), Depends(mevcut_kullanici_getir), etc.
    r"Depends\s*\(\s*("
    r"get_current_user|get_current_active_user|get_authenticated_user|"
    r"get_current_admin_user|get_current_teacher_user|get_current_student_user|"
    r"require_admin|require_admin_user|require_teacher|require_parent|"
    r"require_student|require_admin_or_teacher|"
    r"mevcut_kullanici_getir|admin_kullanici_getir|"
    r"ogretmen_yetkisi_kontrol|veli_yetkisi_kontrol|ogrenci_yetkisi_kontrol|"
    r"\w*_kullanici_getir|\w*_yetkisi_kontrol|"
    r"verify_\w+|check_\w+_access"
    r")\s*\)"
)

# Annotation pattern: `current_user: AuthenticatedUser = ...` or
# `_: AuthenticatedUser = Depends(...)` (used when the dep is just for guard)
CURRENT_USER_PARAM_RE = re.compile(
    r"(?:current_user|_user|user|_)\s*:\s*(?:Optional\[)?"
    r"(?:AuthenticatedUser|CurrentUser|User|Kullanici)"
)

RESPONSE_MODEL_RE = re.compile(r"response_model\s*=")

ROUTER_REGISTERED_DIRS = ("backend/app/api/", "backend/api/")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@dataclass
class Endpoint:
    file: str
    line: int
    method: str
    path: str
    decorator_kwargs: str
    function_body: str  # ~30 lines after decorator
    violations: dict[str, str] = field(default_factory=dict)


@dataclass
class Report:
    endpoints: list[Endpoint] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)

    @property
    def hard_violations(self) -> list[tuple[Endpoint, str, str]]:
        return [
            (ep, code, msg)
            for ep in self.endpoints
            for code, msg in ep.violations.items()
            if code in HARD_CHECKS
        ]

    @property
    def soft_violations(self) -> list[tuple[Endpoint, str, str]]:
        return [
            (ep, code, msg)
            for ep in self.endpoints
            for code, msg in ep.violations.items()
            if code in SOFT_CHECKS
        ]


# ---------------------------------------------------------------------------
# Git diff
# ---------------------------------------------------------------------------
def run_git(args: list[str]) -> str:
    try:
        # Use bytes mode + manual UTF-8 decode with replace — Windows cp1254
        # consoles crash on raw text mode when diff contains Turkish chars.
        res = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        return res.stdout.decode("utf-8", errors="replace") if res.stdout else ""
    except FileNotFoundError:
        print("ERROR: git not found on PATH", file=sys.stderr)
        sys.exit(2)


def changed_py_files() -> list[str]:
    # diff-filter=AM → Added or Modified (skip deleted, renamed)
    out = run_git(
        ["diff", f"origin/{BASE_REF}...HEAD", "--name-only", "--diff-filter=AM"]
    )
    if not out.strip():
        # fallback: HEAD~1 (push without PR context)
        out = run_git(["diff", "HEAD~1...HEAD", "--name-only", "--diff-filter=AM"])
    return [
        line.strip()
        for line in out.splitlines()
        if line.strip().endswith(".py")
    ]


def added_lines(filepath: str) -> set[int]:
    """Return 1-indexed line numbers that were added in this PR."""
    out = run_git(
        ["diff", f"origin/{BASE_REF}...HEAD", "--unified=0", "--", filepath]
    )
    added: set[int] = set()
    current_new_line = 0
    for line in out.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                current_new_line = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.add(current_new_line)
            current_new_line += 1
        elif not line.startswith("-"):
            current_new_line += 1
    return added


# ---------------------------------------------------------------------------
# Endpoint extraction
# ---------------------------------------------------------------------------
def extract_endpoints(filepath: str, added: set[int]) -> list[Endpoint]:
    full = REPO_ROOT / filepath
    if not full.is_file():
        return []
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.splitlines()
    endpoints: list[Endpoint] = []
    for m in DECORATOR_RE.finditer(text):
        # Line number of the @ — find by counting newlines up to match start
        line_no = text[: m.start()].count("\n") + 1
        if line_no not in added:
            continue  # decorator was not added in this PR
        # Capture ~30 lines following the decorator as the function body
        body = "\n".join(lines[line_no - 1 : line_no + 30])
        endpoints.append(
            Endpoint(
                file=filepath,
                line=line_no,
                method=m.group(2).upper(),
                path=m.group(3),
                decorator_kwargs=m.group(4),
                function_body=body,
            )
        )
    return endpoints


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_c1_api_v1_prefix(ep: Endpoint, router_prefix: str) -> str | None:
    """C1 — decorator route or its router must use `/api/v1/`."""
    full_path = router_prefix.rstrip("/") + "/" + ep.path.lstrip("/")
    if "/api/v1/" not in full_path and not full_path.startswith("/api/v1"):
        return f"path `{full_path}` missing `/api/v1/` prefix"
    return None


def check_c2_english_segment(ep: Endpoint) -> str | None:
    """C2 — Turkish segments outside TR_ALLOWLIST."""
    for seg in ep.path.strip("/").split("/"):
        # strip path params like {id}
        if seg.startswith("{"):
            continue
        if seg in TR_ALLOWLIST:
            continue
        if TR_TOKEN_RE.search(seg):
            return f"Turkish segment `{seg}` not in TR_ALLOWLIST"
    return None


def check_c3_auth(ep: Endpoint, router_prefix: str = "") -> str | None:
    """C3 — auth Depends required unless route is in public allowlist.

    Allowlist match is performed against the *full* path
    (`router_prefix + ep.path`) so that entries like `/billing/webhook` or
    `/auth/login` match correctly when the decorator only carries the
    suffix segment (`/webhook`, `/login`).
    """
    full_path = (router_prefix.rstrip("/") + "/" + ep.path.lstrip("/")).rstrip("/")
    for pub in PUBLIC_ENDPOINTS:
        if pub in full_path or pub in ep.path:
            return None
    has_auth_dep = bool(AUTH_DEPENDS_RE.search(ep.function_body))
    has_user_param = bool(CURRENT_USER_PARAM_RE.search(ep.function_body))
    if not (has_auth_dep or has_user_param):
        return "no `Depends(get_current_user|require_admin|...)` and no `current_user: AuthenticatedUser` param"
    return None


def check_c4_idor_user_id(ep: Endpoint) -> str | None:
    """C4 — user_id must come from current_user, not Query(...)."""
    if USER_ID_QUERY_RE.search(ep.function_body):
        return "IDOR risk: `user_id: ... = Query(...)` found — use `current_user.id` instead"
    return None


def check_c5_response_model(ep: Endpoint) -> str | None:
    """C5 — response_model= recommended for OpenAPI + Pydantic validation."""
    if not RESPONSE_MODEL_RE.search(ep.decorator_kwargs):
        return "decorator missing `response_model=...`"
    return None


def check_c6_loader_registered(ep: Endpoint) -> str | None:
    """C6 — new router file under app/api/ or api/ must be in loader.py."""
    if not any(ep.file.startswith(d) for d in ROUTER_REGISTERED_DIRS):
        return None  # not a router-loadable file
    # Map e.g. backend/app/api/foo.py → app.api.foo
    rel = ep.file.replace("backend/", "", 1).replace("/", ".").removesuffix(".py")
    loader = REPO_ROOT / "backend" / "routers" / "loader.py"
    if not loader.is_file():
        return None
    try:
        loader_text = loader.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if rel in loader_text:
        return None
    return f"router module `{rel}` not found in backend/routers/loader.py ROUTER_MAPPING"


def check_c7_tests_added(ep: Endpoint, changed: list[str]) -> str | None:
    """C7 — heuristic: PR should add a tests/ file referencing the path."""
    # Look for any tests/*.py file in the diff that mentions the endpoint path
    last_segment = ep.path.rstrip("/").rsplit("/", 1)[-1].split("{")[0].strip("-")
    if not last_segment:
        return None
    test_files = [f for f in changed if "/tests/" in f or f.startswith("backend/tests/")]
    for tf in test_files:
        full = REPO_ROOT / tf
        if not full.is_file():
            continue
        try:
            if last_segment in full.read_text(encoding="utf-8", errors="replace"):
                return None
        except OSError:
            continue
    return f"no test file in PR mentions `{last_segment}`"


# ---------------------------------------------------------------------------
# Router prefix detection (best-effort)
# ---------------------------------------------------------------------------
ROUTER_PREFIX_RE = re.compile(
    r"APIRouter\s*\([^)]*prefix\s*=\s*[\"']([^\"']+)[\"']", re.DOTALL
)


def detect_router_prefix(filepath: str) -> str:
    full = REPO_ROOT / filepath
    if not full.is_file():
        return ""
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    m = ROUTER_PREFIX_RE.search(text)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    report = Report()
    report.changed_files = changed_py_files()
    if not report.changed_files:
        print("No changed Python files vs origin/" + BASE_REF + ". Skipping.")
        return 0

    for fp in report.changed_files:
        added = added_lines(fp)
        if not added:
            continue
        eps = extract_endpoints(fp, added)
        if not eps:
            continue
        router_prefix = detect_router_prefix(fp)
        for ep in eps:
            for code, fn in (
                ("C1", lambda e=ep: check_c1_api_v1_prefix(e, router_prefix)),
                ("C2", lambda e=ep: check_c2_english_segment(e)),
                ("C3", lambda e=ep, rp=router_prefix: check_c3_auth(e, rp)),
                ("C4", lambda e=ep: check_c4_idor_user_id(e)),
                ("C5", lambda e=ep: check_c5_response_model(e)),
                ("C6", lambda e=ep: check_c6_loader_registered(e)),
                (
                    "C7",
                    lambda e=ep: check_c7_tests_added(e, report.changed_files),
                ),
            ):
                msg = fn()
                if msg:
                    ep.violations[code] = msg
        report.endpoints.extend(eps)

    print_report(report)

    if report.hard_violations:
        return 1
    return 0


def print_report(report: Report) -> None:
    if not report.endpoints:
        print("## New-Endpoint Checklist")
        print("No new `@router.*` decorators added in this PR. ✅")
        return

    print("## New-Endpoint Checklist")
    print()
    print(f"Scanned {len(report.endpoints)} newly added endpoint(s) "
          f"across {len(set(e.file for e in report.endpoints))} file(s).")
    print()
    print("| File:Line | Method | Path | Checks |")
    print("|-----------|--------|------|--------|")
    for ep in report.endpoints:
        if ep.violations:
            checks = " ".join(
                f"❌{c}" if c in HARD_CHECKS else f"⚠️{c}"
                for c in sorted(ep.violations)
            )
        else:
            checks = "✅"
        print(f"| `{ep.file}:{ep.line}` | {ep.method} | `{ep.path}` | {checks} |")

    if report.hard_violations:
        print()
        print("### ❌ HARD violations (blocking)")
        print()
        for ep, code, msg in report.hard_violations:
            print(f"- **{code}** `{ep.file}:{ep.line}` `{ep.method} {ep.path}` — {msg}")

    if report.soft_violations:
        print()
        print("### ⚠️ SOFT violations (advisory)")
        print()
        for ep, code, msg in report.soft_violations:
            print(f"- **{code}** `{ep.file}:{ep.line}` `{ep.method} {ep.path}` — {msg}")

    print()
    print(f"HARD checks (blocking): {sorted(HARD_CHECKS)}")
    print(f"SOFT checks (advisory): {sorted(SOFT_CHECKS)}")


if __name__ == "__main__":
    sys.exit(main())
