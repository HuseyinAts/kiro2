"""
Feature Inventory Extractor (Aşama 0, Session 140)
==================================================

Parses `backend/routers/loader.py` ROUTER_MAPPING, walks each referenced
router module via AST, and emits a structured inventory table:

  router | method | full_path | handler | auth | write | body_model | gf_covered

Cross-references `backend/tests/e2e/test_golden_flows.py` to mark which
endpoints already have a Golden Flow probe.

This script is pure static analysis — it does NOT import the routers.
That means it works even when imports are broken, and produces a stable
baseline independent of runtime wiring.

Output:
  - stdout: summary counters
  - --write: docs/audits/2026-04-11_feature-inventory.md

Usage:
  python backend/scripts/extract_feature_inventory.py
  python backend/scripts/extract_feature_inventory.py --write
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
LOADER = BACKEND / "routers" / "loader.py"
GF_TEST = BACKEND / "tests" / "e2e" / "test_golden_flows.py"
OUTPUT = REPO_ROOT / "docs" / "audits" / "2026-04-11_feature-inventory.md"

# --- Known FastAPI dependency/annotation sentinels --------------------------

AUTH_PARAM_NAMES = {
    "current_user",
    "_current_user",
    "admin_user",
    "_admin_user",
    "teacher_user",
    "parent_user",
    "mevcut_kullanici",
    "mevcut_kullanıcı",
    "ogretmen",
    "admin",
}
AUTH_DEPENDENCY_NAMES = {
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "get_teacher_user",
    "get_parent_user",
    "require_admin",
    "require_teacher",
    "require_student",
    "require_parent",
    "mevcut_kullanici_getir",
    "ogretmen_yetkisi_kontrol",
    "veli_yetkisi_kontrol",
    "require_authenticated",
    "AuthenticatedUser",
}
AUTH_ANNOTATION_NAMES = {"AuthenticatedUser", "User", "CurrentUser"}

# Types that are NOT a Pydantic body param (used to eliminate false positives)
NON_BODY_ANNOTATIONS = {
    "Request",
    "Response",
    "WebSocket",
    "BackgroundTasks",
    "UploadFile",
    "File",
    "Form",
    "Query",
    "Path",
    "Header",
    "Cookie",
    "Body",
    "Depends",
    "Security",
    "AsyncSession",
    "Session",
    "db",
    "AuthenticatedUser",
    "User",
    "CurrentUser",
    "int",
    "str",
    "bool",
    "float",
    "bytes",
    "dict",
    "list",
    "Any",
    "None",
    "Optional",
    "TokenPayload",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
WRITE_METHODS = {"post", "put", "patch", "delete"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Endpoint:
    router_module: str
    category: str
    file_path: str
    method: str
    route_path: str  # as written in decorator
    full_path: str  # prefix + route_path
    handler: str
    has_auth: bool
    is_write: bool
    body_model: str | None
    gf_covered: bool = False
    line: int = 0


@dataclass
class RouterFile:
    module: str
    category: str
    file_path: Path
    prefix: str = ""
    endpoints: list[Endpoint] = field(default_factory=list)
    load_error: str | None = None


# ---------------------------------------------------------------------------
# Loader parsing
# ---------------------------------------------------------------------------


def parse_loader_mapping() -> list[tuple[str, str]]:
    """Extract (module, category) pairs from ROUTER_MAPPING."""
    src = LOADER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    pairs: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ROUTER_MAPPING":
                    if isinstance(node.value, ast.Dict):
                        for key_node, val_node in zip(
                            node.value.keys, node.value.values
                        ):
                            if not isinstance(key_node, ast.Constant):
                                continue
                            key = key_node.value
                            category = ""
                            # value is a Tuple(category, module) literal
                            if (
                                isinstance(val_node, ast.Tuple)
                                and len(val_node.elts) >= 1
                            ):
                                first = val_node.elts[0]
                                if isinstance(first, ast.Constant):
                                    category = first.value
                            pairs.append((key, category))
    return pairs


def module_to_path(module: str) -> Path | None:
    """Resolve `api.foo.bar` → `backend/api/foo/bar.py`."""
    parts = module.split(".")
    candidate = BACKEND.joinpath(*parts).with_suffix(".py")
    if candidate.exists():
        return candidate
    # Fallback: package __init__.py
    init = BACKEND.joinpath(*parts) / "__init__.py"
    if init.exists():
        return init
    return None


# ---------------------------------------------------------------------------
# Router file AST parsing
# ---------------------------------------------------------------------------


def _extract_router_prefix(tree: ast.AST) -> str:
    """Find `router = APIRouter(prefix="...")` and return the prefix string."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "router":
                    call = node.value
                    if isinstance(call, ast.Call):
                        for kw in call.keywords:
                            if kw.arg == "prefix" and isinstance(
                                kw.value, ast.Constant
                            ):
                                return kw.value.value or ""
    return ""


def _dep_name_from_call(call: ast.Call) -> str | None:
    """Extract the name inside `Depends(xxx)` / `Security(xxx)`."""
    if not isinstance(call.func, ast.Name):
        return None
    if call.func.id not in {"Depends", "Security"}:
        return None
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, ast.Name):
        return arg.id
    if isinstance(arg, ast.Attribute):
        return arg.attr
    return None


def _annotation_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    return None


def _handler_has_auth(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Heuristic: a handler is considered auth-protected if *any* of
    - an argument name matches AUTH_PARAM_NAMES,
    - an argument annotation matches AUTH_ANNOTATION_NAMES,
    - an argument default is Depends(<AUTH_DEPENDENCY_NAME>).
    """
    all_args = list(func.args.args) + list(func.args.kwonlyargs)
    for a in all_args:
        if a.arg in AUTH_PARAM_NAMES:
            return True
        anno = _annotation_name(a.annotation)
        if anno and anno in AUTH_ANNOTATION_NAMES:
            return True

    # defaults are positional; kw_defaults are keyword-only
    for default in list(func.args.defaults) + list(func.args.kw_defaults or []):
        if isinstance(default, ast.Call):
            name = _dep_name_from_call(default)
            if name and name in AUTH_DEPENDENCY_NAMES:
                return True
    # Module-level _auth_dep alias pattern: arg default = _auth_dep (Name)
    for default in list(func.args.defaults) + list(func.args.kw_defaults or []):
        if isinstance(default, ast.Name) and default.id in {
            "_auth_dep",
            "AUTH_DEP",
            "auth_dep",
        }:
            return True
    return False


def _body_model(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Best-effort: return the first parameter whose annotation looks like
    a Pydantic body (not a sentinel type, not a Depends default)."""
    args = list(func.args.args) + list(func.args.kwonlyargs)
    for i, a in enumerate(args):
        anno = _annotation_name(a.annotation)
        if not anno:
            continue
        if anno in NON_BODY_ANNOTATIONS:
            continue
        # Skip if default is a Depends/Query/Path/etc call
        default = None
        if i < len(func.args.args):
            offset = len(func.args.args) - len(func.args.defaults)
            if i >= offset:
                default = func.args.defaults[i - offset]
        else:
            kw_i = i - len(func.args.args)
            if kw_i < len(func.args.kw_defaults or []):
                default = func.args.kw_defaults[kw_i]
        if isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
            if default.func.id in {
                "Depends",
                "Security",
                "Query",
                "Path",
                "Header",
                "Cookie",
                "Body",
                "File",
                "Form",
            }:
                continue
        return anno
    return None


def _is_router_decorator(dec: ast.expr) -> tuple[str, str] | None:
    """If decorator is `@router.<method>(path, ...)` return (method, path)."""
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if not isinstance(func, ast.Attribute):
        return None
    method = func.attr.lower()
    if method not in HTTP_METHODS:
        return None
    if not isinstance(func.value, ast.Name):
        return None
    if func.value.id != "router":
        return None
    if not dec.args:
        return None
    path_arg = dec.args[0]
    if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
        return (method, path_arg.value)
    return None


def parse_router_file(rf: RouterFile) -> None:
    try:
        src = rf.file_path.read_text(encoding="utf-8")
    except Exception as e:
        rf.load_error = f"read: {e!s}"
        return
    try:
        tree = ast.parse(src, filename=str(rf.file_path))
    except SyntaxError as e:
        rf.load_error = f"syntax: {e!s}"
        return

    rf.prefix = _extract_router_prefix(tree)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            info = _is_router_decorator(dec)
            if info is None:
                continue
            method, path = info
            full_path = (rf.prefix.rstrip("/") + "/" + path.lstrip("/")).rstrip(
                "/"
            ) or "/"
            ep = Endpoint(
                router_module=rf.module,
                category=rf.category,
                file_path=str(rf.file_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                method=method,
                route_path=path,
                full_path=full_path,
                handler=node.name,
                has_auth=_handler_has_auth(node),
                is_write=method in WRITE_METHODS,
                body_model=_body_model(node),
                line=node.lineno,
            )
            rf.endpoints.append(ep)


# ---------------------------------------------------------------------------
# Golden Flow coverage
# ---------------------------------------------------------------------------


def extract_gf_paths() -> set[str]:
    """Pull every `"/api/..."` string literal out of the GF test file."""
    if not GF_TEST.exists():
        return set()
    src = GF_TEST.read_text(encoding="utf-8")
    paths: set[str] = set()
    for m in re.finditer(r'["\'](/api/[^"\'?\s{]+)', src):
        paths.add(m.group(1).rstrip("/"))
    return paths


def _match_gf(endpoint_full_path: str, gf_paths: set[str]) -> bool:
    """Match if the endpoint's literal path (with any FastAPI `{param}`
    placeholders replaced by a glob) appears in a GF test string."""
    # Normalize FastAPI param syntax `/{session_id}/` → `/` for matching
    normalized = (
        re.sub(r"\{[^}]+\}", "", endpoint_full_path).replace("//", "/").rstrip("/")
    )
    for gf in gf_paths:
        gfn = gf.rstrip("/")
        if gfn == normalized:
            return True
        # Also accept "startswith" match — GF test often hits a sub-path
        if gfn.startswith(normalized + "/") or normalized.startswith(gfn + "/"):
            return True
        # Accept fuzzy match when one side contains {param} that was normalized
        if normalized and normalized in gfn:
            return True
    return False


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def build_report(routers: list[RouterFile], gf_paths: set[str]) -> str:
    all_eps: list[Endpoint] = []
    for rf in routers:
        for ep in rf.endpoints:
            ep.gf_covered = _match_gf(ep.full_path, gf_paths)
            all_eps.append(ep)

    total = len(all_eps)
    write_eps = [e for e in all_eps if e.is_write]
    read_eps = [e for e in all_eps if not e.is_write]
    auth_yes = sum(1 for e in all_eps if e.has_auth)
    auth_no = total - auth_yes
    gf_write_covered = sum(1 for e in write_eps if e.gf_covered)
    gf_read_covered = sum(1 for e in read_eps if e.gf_covered)

    # Per-category roll-up
    by_cat: dict[str, dict[str, int]] = {}
    for e in all_eps:
        c = e.category or "uncategorized"
        bucket = by_cat.setdefault(
            c,
            {
                "total": 0,
                "write": 0,
                "write_auth": 0,
                "write_gf": 0,
                "read": 0,
                "read_auth": 0,
            },
        )
        bucket["total"] += 1
        if e.is_write:
            bucket["write"] += 1
            if e.has_auth:
                bucket["write_auth"] += 1
            if e.gf_covered:
                bucket["write_gf"] += 1
        else:
            bucket["read"] += 1
            if e.has_auth:
                bucket["read_auth"] += 1

    load_errors = [(rf.module, rf.load_error) for rf in routers if rf.load_error]

    out: list[str] = []
    out.append("# Feature Inventory — Aşama 0 (Session 140)")
    out.append("")
    out.append("**Tarih:** 11 Nisan 2026  ")
    out.append("**Kaynak:** `backend/routers/loader.py` ROUTER_MAPPING  ")
    out.append("**Metot:** AST parse (no import), GF cross-reference  ")
    out.append("")
    out.append(
        "Bu rapor **probe envanteri** — hangi endpoint'lerin Golden Flow kapsamı"
    )
    out.append("var, hangileri meçhul. Aşama 1 (probe-first genişletme) için input.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 1. Özet")
    out.append("")
    out.append(f"- **Toplam tracked router:** {len(routers)}")
    out.append(f"- **Toplam endpoint:** {total}")
    out.append(f"- **Write (POST/PUT/PATCH/DELETE):** {len(write_eps)}")
    out.append(f"- **Read (GET/HEAD/OPTIONS):** {len(read_eps)}")
    out.append(
        f"- **Auth'lu endpoint:** {auth_yes} ({auth_yes / total * 100:.1f}% - heuristic)"
    )
    out.append(f"- **Anonim (auth yok):** {auth_no}")
    out.append("")
    out.append("### Golden Flow kapsamı")
    out.append("")
    out.append(
        f"- **Write endpoint'lerin kapsamı:** {gf_write_covered}/{len(write_eps)} "
        f"({gf_write_covered / max(1, len(write_eps)) * 100:.1f}%)"
    )
    out.append(
        f"- **Read endpoint'lerin kapsamı:** {gf_read_covered}/{len(read_eps)} "
        f"({gf_read_covered / max(1, len(read_eps)) * 100:.1f}%)"
    )
    out.append(
        f"- **Probe'lanmamış write count:** **{len(write_eps) - gf_write_covered}** "
        "← Aşama 1 hedefi"
    )
    out.append("")
    if load_errors:
        out.append(f"- **Parse edilemeyen router:** {len(load_errors)}")
        for mod, err in load_errors:
            out.append(f"  - `{mod}`: {err}")
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 2. Kategori bazlı roll-up")
    out.append("")
    out.append(
        "| Kategori | Toplam | Write | Write+Auth | Write+GF | Read | Read+Auth | Probe gap |"
    )
    out.append("|---|---|---|---|---|---|---|---|")
    for cat in sorted(by_cat.keys()):
        b = by_cat[cat]
        gap = b["write"] - b["write_gf"]
        out.append(
            f"| {cat} | {b['total']} | {b['write']} | {b['write_auth']} | "
            f"{b['write_gf']} | {b['read']} | {b['read_auth']} | **{gap}** |"
        )
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 3. Probe'lanmamış write endpoint'ler")
    out.append("")
    out.append("Aşama 1 batch hedefleri — her satır 1 Golden Flow write probe'u demek.")
    out.append("")
    out.append("| # | Kategori | Method | Path | Handler | Auth | Body | Dosya |")
    out.append("|---|---|---|---|---|---|---|---|")
    uncovered_writes = sorted(
        [e for e in write_eps if not e.gf_covered],
        key=lambda x: (x.category or "", x.full_path),
    )
    for i, e in enumerate(uncovered_writes, 1):
        auth_mark = "✅" if e.has_auth else "❌"
        body = e.body_model or "—"
        out.append(
            f"| {i} | {e.category} | {e.method.upper()} | `{e.full_path}` | "
            f"`{e.handler}` | {auth_mark} | `{body}` | `{e.file_path}:{e.line}` |"
        )
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 4. Tam endpoint listesi")
    out.append("")
    out.append("<details>")
    out.append("<summary>Tüm endpoint'leri göster</summary>")
    out.append("")
    out.append("| Kategori | Method | Path | Handler | Auth | W | GF | Dosya |")
    out.append("|---|---|---|---|---|---|---|---|")
    for e in sorted(all_eps, key=lambda x: (x.category or "", x.full_path, x.method)):
        auth_mark = "✓" if e.has_auth else "✗"
        write_mark = "W" if e.is_write else "R"
        gf_mark = "✓" if e.gf_covered else "—"
        out.append(
            f"| {e.category} | {e.method.upper()} | `{e.full_path}` | "
            f"`{e.handler}` | {auth_mark} | {write_mark} | {gf_mark} | "
            f"`{e.file_path}:{e.line}` |"
        )
    out.append("")
    out.append("</details>")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 5. Sonraki adım")
    out.append("")
    out.append(
        "**Aşama 1, batch 1:** En yüksek kullanıcı etkili 10 write endpoint seç,"
    )
    out.append(
        "her biri için `backend/tests/e2e/test_golden_flows.py` içine 5-10 satırlık"
    )
    out.append(
        "probe yaz, GF suite'i koş, düşenleri Session 136 stilinde kök neden tablosu"
    )
    out.append("ile raporla.")
    out.append("")
    out.append("**Seçim kriteri:**")
    out.append("1. User-facing (öğrenci/öğretmen/veli günlük kullanıyor)")
    out.append("2. State-changing (DB yazar)")
    out.append("3. Mevcut GF kapsamında yok")
    out.append(
        "4. Auth'lu (anonim endpoint'ler Session 138 linter'ı ile zaten kontrol altında)"
    )
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="Write markdown to docs/audits/"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-router chatter"
    )
    args = parser.parse_args()

    mapping = parse_loader_mapping()
    if not args.quiet:
        print(
            f"[inventory] parsed {len(mapping)} entries from ROUTER_MAPPING",
            file=sys.stderr,
        )

    routers: list[RouterFile] = []
    unresolved: list[str] = []
    for module, category in mapping:
        path = module_to_path(module)
        if path is None:
            unresolved.append(module)
            continue
        rf = RouterFile(module=module, category=category, file_path=path)
        parse_router_file(rf)
        routers.append(rf)

    if not args.quiet and unresolved:
        print(
            f"[inventory] {len(unresolved)} modules did not resolve to a file:",
            file=sys.stderr,
        )
        for m in unresolved[:10]:
            print(f"  - {m}", file=sys.stderr)

    gf_paths = extract_gf_paths()
    if not args.quiet:
        print(
            f"[inventory] extracted {len(gf_paths)} distinct paths from GF test",
            file=sys.stderr,
        )

    report = build_report(routers, gf_paths)

    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(report, encoding="utf-8")
        print(f"[inventory] wrote {OUTPUT.relative_to(REPO_ROOT)}")
    else:
        # Print first ~80 lines to stdout as a preview
        preview = "\n".join(report.splitlines()[:80])
        print(preview)

    # Exit code: 0 always (this is an inventory, not a gate)
    total_eps = sum(len(rf.endpoints) for rf in routers)
    write_eps = sum(1 for rf in routers for e in rf.endpoints if e.is_write)
    gf_covered = sum(
        1
        for rf in routers
        for e in rf.endpoints
        if e.is_write and _match_gf(e.full_path, gf_paths)
    )
    print(
        f"[inventory] total={total_eps} write={write_eps} gf_covered={gf_covered} "
        f"gap={write_eps - gf_covered}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
