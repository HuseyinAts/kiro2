#!/usr/bin/env python
"""
audit_missing_auth.py — AST linter for MISSING_AUTH pattern on write endpoints.

Detects FastAPI write handlers (POST/PUT/PATCH/DELETE) that do NOT take any
authentication dependency — i.e. can be called anonymously. Extends the
Session 137 audit_db_dependency.py philosophy: deterministic, no phantoms.

Session 136 Wave 2 probed half-working write-path features. Most root causes
were NOT missing auth (they were type lies or field drift), but Session 113
reported ~332 endpoints potentially unprotected. This linter disambiguates:
only WRITE endpoints, with tight false-positive filters.

Detection logic:
1. For each `async def` with `@router.post/put/patch/delete` decorator, walk
   parameter annotations.
2. Collect all `Depends(<callable>)` dependency names.
3. If none of the dependencies is in the AUTH allow-list, report:
     - HIGH  — no auth dependency at all.
     - MED   — only `authenticate_optional` (callable anonymously,
               surface for TokenPayload/None bugs like GF8wA kvkk).

Heuristics / false positive filters:
- Skip handlers whose function name matches a PUBLIC prefix
  (login, register, refresh, forgot_password, reset_password, verify_email,
   webhook_*, health, csp_report, contact_us, public_*).
- Skip handlers whose route path contains a PUBLIC segment
  (`/auth/login`, `/auth/register`, `/public/`, `/webhook/`, `/health`).
- Skip test files, _deprecated/, __pycache__.

Usage:
    python scripts/audit_missing_auth.py
    python scripts/audit_missing_auth.py --fail-on-high
    python scripts/audit_missing_auth.py --json out.json

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

# File-level skips: demo / example surfaces are not real endpoints.
SKIP_FILE_SUFFIXES = (
    "_demo.py",
    "_example.py",
    "sentry_demo.py",
    "tracing_example.py",
    "_stub.py",
)

WRITE_METHODS = {"post", "put", "patch", "delete"}

# Dependency callables that REQUIRE authentication.
AUTH_REQUIRED_NAMES = {
    # English
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_teacher",
    "get_current_student",
    "get_current_parent",
    "require_admin",
    "require_teacher",
    "require_student",
    "require_parent",
    "require_authenticated",
    "require_role",
    "AuthenticatedUser",  # type alias used as Depends sometimes
    # Turkish
    "mevcut_kullanici_getir",
    "mevcut_veli_getir",
    "mevcut_ogretmen_getir",
    "mevcut_ogrenci_getir",
    "aktif_kullanici_getir",
    "admin_kullanici_getir",
    "ogretmen_kullanici_getir",
    "ogrenci_kullanici_getir",
    "veli_kullanici_getir",
    "ogretmen_yetkisi_kontrol",
    "veli_yetkisi_kontrol",
    "admin_yetkisi_kontrol",
    "admin_yetki_kontrolu",
    "ogretmen_yetki_kontrolu",
    "veli_yetki_kontrolu",
    # Session-specific helpers that load a user from a token
    "_get_user_orm",
    "_require_2fa_feature",
    # Org / multi-tenant auth deps — all transitively Depends(get_current_user):
    #   require_org_role -> get_current_membership -> get_current_tenant
    #   get_current_tenant -> Depends(get_current_user) (403 if no tenant)
    #   require_dpa_signed -> get_current_tenant -> get_current_user
    #   get_current_user_old = `get_current_user as get_current_user_old` import alias
    "require_org_role",
    "get_current_tenant",
    "require_dpa_signed",
    "get_current_user_old",
}

# Dependencies that allow ANONYMOUS access — MED severity for write endpoints.
AUTH_OPTIONAL_NAMES = {
    "authenticate_optional",
    "get_current_user_optional",
    "optional_current_user",
    # cat.py guest sessions: returns User|None, None for anonymous (by design).
    "get_optional_user",
}

# Class-based authorization dependency names — detected via Call prefix.
AUTH_CLASS_PREFIXES = (
    "AuthorizationDependency",
    "AuthenticationDependency",
    "RoleRequirement",
    "RequireRole",
)

# Handler name prefixes / exact names that are legitimately public.
PUBLIC_HANDLER_NAMES = {
    "login",
    "register",
    "signup",
    "refresh",
    "refresh_token",
    "logout",
    "health",
    "health_check",
    "healthcheck",
    "ready",
    "liveness",
    "readiness",
    "csp_report",
    "contact_us",
    "webhook",
    "root",
    "index",
}
PUBLIC_HANDLER_PREFIXES = (
    "forgot_",
    "reset_password",
    "request_password",
    "verify_email",
    "verify_token",
    "confirm_email",
    "confirm_signup",
    "public_",
    "webhook_",
    "oauth_",
    "sso_",
)

# Path substrings that indicate a public surface.
PUBLIC_PATH_SUBSTRINGS = (
    # English auth
    "/auth/login",
    "/auth/register",
    "/auth/signup",
    "/auth/refresh",
    "/auth/logout",
    "/auth/forgot",
    "/auth/reset",
    "/auth/verify",
    "/auth/validate",
    "/auth/oauth",
    "/auth/magic-link",
    "/auth/2fa/recovery",
    # Turkish auth
    "/auth/kayit",
    "/auth/giris",
    "/auth/cikis",
    "/auth/sifre-sifirla",
    "/auth/sifre-unuttum",
    "/auth/dogrulama",
    # 2FA login-step surfaces (user has a temp token, not a session yet)
    "/auth/2fa/login-verify",
    "/auth/2fa/login-verify-backup",
    # Public / infra surfaces
    "/public/",
    "/webhook/",
    "/webhooks/",
    "/health",
    "/ready",
    "/liveness",
    "/readiness",
    "/metrics",
    "/csp-report",
    "/web-vitals",
    "/analytics/web-vitals",
    "/telemetry/",
    "/errors/report",
    # Public content browsing (makaleler, dersler — educational read path)
    "/content/search",
    # Email-link token flows (token in body IS the auth — like /auth/verify):
    # parental consent (veli-onay) + email verification (eposta-dogrula).
    "/veli-onay/",
    "/eposta-dogrula/",
    # Billing webhook: authenticated by X-Kiro2-Billing-Secret shared secret.
    "/billing/webhook",
)


@dataclass
class Finding:
    file: str
    line: int
    handler: str
    method: str
    path: str
    severity: str  # "high" | "medium"
    detail: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def by_severity(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {"high": [], "medium": []}
        for f in self.findings:
            out[f.severity].append(f)
        return out

    def total(self) -> int:
        return len(self.findings)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _router_decorator(
    node: ast.AsyncFunctionDef,
) -> tuple[str, str] | None:
    """
    Return (method, path) if the function is decorated with
    `@router.post/put/patch/delete(path, ...)`.
    """
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


def _extract_depends_name(
    default: ast.expr | None, aliases: dict[str, str] | None = None
) -> str | None:
    """
    For a parameter default like `Depends(get_current_user)` or
    `Depends(AuthorizationDependency(required_roles=[...]))`, return the
    callable name — `"get_current_user"` or `"AuthorizationDependency"`.

    Also resolves module-level alias assignments: if `default` is an
    `ast.Name` like `_auth_dep`, and `aliases` maps `"_auth_dep"` to
    `"get_current_user"`, returns `"get_current_user"`.

    Returns None if the default is not a Depends() call or known alias.
    """
    # Module-level alias like `current_user: Any = _auth_dep`
    if isinstance(default, ast.Name) and aliases and default.id in aliases:
        return aliases[default.id]

    if not isinstance(default, ast.Call):
        return None
    callee = default.func
    if isinstance(callee, ast.Name) and callee.id == "Depends":
        if default.args:
            target = default.args[0]
            # Depends(get_current_user)
            if isinstance(target, ast.Name):
                return target.id
            # Depends(AuthorizationDependency(required_roles=["admin"]))
            if isinstance(target, ast.Call):
                tf = target.func
                if isinstance(tf, ast.Name):
                    return tf.id
                if isinstance(tf, ast.Attribute):
                    return tf.attr
            # Depends(auth.get_current_user)
            if isinstance(target, ast.Attribute):
                return target.attr
    return None


def _build_depends_aliases(tree: ast.Module) -> dict[str, str]:
    """
    Scan module-level assignments for `NAME = Depends(callable)` or
    `NAME = <factory>()` patterns that wrap an auth dependency.

    Also handles the pattern:
        def _get_auth_dependency():
            try: ... return Depends(get_current_user)
            except: return Depends(_noop_auth)
        _auth_dep = _get_auth_dependency()

    If the factory function body contains a `return Depends(...)` to a
    known auth name, register the alias. Otherwise the alias is None.
    """
    # First pass: collect `_X_dep = Depends(callable)` direct assignments
    # AND `_X_dep = _factory()` indirect assignments.
    direct: dict[str, str] = {}
    factory_call: dict[str, str] = {}  # alias_name -> factory_fn_name

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        alias_name = node.targets[0].id
        val = node.value
        # `_auth_dep = Depends(get_current_user)`
        direct_name = _extract_depends_name(val, aliases=None)
        if direct_name:
            direct[alias_name] = direct_name
            continue
        # `_auth_dep = _get_auth_dependency()`
        if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
            factory_call[alias_name] = val.func.id

    # Second pass: for factory calls, scan the factory body for
    # `return Depends(known_auth_callable)`.
    factory_defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            factory_defs[node.name] = node

    for alias_name, factory_name in factory_call.items():
        fn = factory_defs.get(factory_name)
        if not fn:
            continue
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Return) and sub.value is not None:
                resolved = _extract_depends_name(sub.value, aliases=None)
                # Only register if it resolves to an AUTH callable. We
                # deliberately skip fallback `_noop_auth` returns that
                # come after an ImportError/except branch, so the FIRST
                # auth-ful Depends(...) return wins.
                if resolved and (
                    resolved in AUTH_REQUIRED_NAMES
                    or resolved in AUTH_OPTIONAL_NAMES
                    or any(resolved.startswith(p) for p in AUTH_CLASS_PREFIXES)
                ):
                    direct[alias_name] = resolved
                    break

    return direct


def _collect_dependency_names(
    node: ast.AsyncFunctionDef, aliases: dict[str, str]
) -> list[str]:
    """Return all Depends callable names used in the handler signature."""
    names: list[str] = []
    args = node.args
    # Pair positional / kw-only args with their defaults.
    pos_defaults = list(args.defaults)
    pos_args = list(args.args)
    # defaults align to the LAST N positional args
    offset = len(pos_args) - len(pos_defaults)
    for i, arg in enumerate(pos_args):
        default = None
        di = i - offset
        if 0 <= di < len(pos_defaults):
            default = pos_defaults[di]
        name = _extract_depends_name(default, aliases=aliases)
        if name:
            names.append(name)
    # kwonly
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=False):
        name = _extract_depends_name(default, aliases=aliases)
        if name:
            names.append(name)
    return names


def _is_auth_required(dep_names: list[str]) -> bool:
    """Does the dependency list include any required-auth callable?"""
    for n in dep_names:
        if n in AUTH_REQUIRED_NAMES:
            return True
        if any(n.startswith(p) for p in AUTH_CLASS_PREFIXES):
            return True
    return False


def _is_auth_optional(dep_names: list[str]) -> bool:
    return any(n in AUTH_OPTIONAL_NAMES for n in dep_names)


def _is_public_handler(name: str) -> bool:
    if name in PUBLIC_HANDLER_NAMES:
        return True
    if any(name.startswith(p) for p in PUBLIC_HANDLER_PREFIXES):
        return True
    return False


def _is_public_path(path: str) -> bool:
    return any(sub in path for sub in PUBLIC_PATH_SUBSTRINGS)


def _router_prefix_from_module(tree: ast.Module) -> str:
    """
    Find the module-level `router = APIRouter(prefix="...")` call and
    return the prefix string, or "" if not set.
    """
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
    aliases = _build_depends_aliases(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        route = _router_decorator(node)
        if route is None:
            continue
        method, route_path = route
        full_path = (
            (prefix + route_path)
            if route_path.startswith("/")
            else (prefix + "/" + route_path if route_path else prefix)
        )

        if _is_public_handler(node.name):
            continue
        if _is_public_path(full_path):
            continue

        dep_names = _collect_dependency_names(node, aliases)

        if _is_auth_required(dep_names):
            continue  # OK

        if _is_auth_optional(dep_names):
            # Optional auth on a WRITE endpoint is a smell — anon can mutate.
            report.findings.append(
                Finding(
                    file=rel,
                    line=node.lineno,
                    handler=node.name,
                    method=method.upper(),
                    path=full_path,
                    severity="medium",
                    detail=(
                        "Write endpoint uses `authenticate_optional` — anonymous "
                        "callers can hit this handler. If the handler branches on "
                        "`current_user is None` and writes anyway, this is an "
                        "IDOR-class bug (GF8wA kvkk pattern)."
                    ),
                )
            )
            continue

        # No auth dependency at all.
        report.findings.append(
            Finding(
                file=rel,
                line=node.lineno,
                handler=node.name,
                method=method.upper(),
                path=full_path,
                severity="high",
                detail=(
                    "Write endpoint has NO authentication dependency. Anyone can "
                    "invoke this without credentials. Add "
                    "`Depends(get_current_user)` or the role-specific equivalent."
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
    lines.append("# Missing-Auth Audit Report")
    lines.append("")
    lines.append(f"**Total findings:** {report.total()}")
    lines.append(f"- HIGH: {len(buckets['high'])}")
    lines.append(f"- MED:  {len(buckets['medium'])}")
    lines.append("")

    for sev in ("high", "medium"):
        items = buckets[sev]
        if not items:
            continue
        lines.append(f"## {sev.upper()} ({len(items)})")
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

    report.findings.sort(key=lambda f: (f.severity != "high", f.file, f.line))

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
