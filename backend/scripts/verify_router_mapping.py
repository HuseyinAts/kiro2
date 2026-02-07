#!/usr/bin/env python3
"""
Verify router mapping modules can be imported and expose a FastAPI router.

Usage:
  python backend/scripts/verify_router_mapping.py
  python backend/scripts/verify_router_mapping.py --json backend/router_mapping_report.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def _load_mapping() -> dict[str, tuple[str, str]]:
    from routers.loader import ROUTER_MAPPING  # local import after path setup

    return ROUTER_MAPPING


def _check_module(module_path: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # noqa: BLE001 - we need the full failure reason
        return False, f"import failed: {exc!r}"

    if not hasattr(module, "router"):
        return False, "imported, but missing 'router' attribute"

    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify router mapping modules.")
    parser.add_argument("--json", dest="json_path", help="Write JSON report to file")
    args = parser.parse_args()

    _ensure_backend_on_path()
    mapping = _load_mapping()

    results: dict[str, dict[str, str | bool]] = {}
    ok_count = 0
    fail_count = 0

    for _old_module, (_category, module_path) in mapping.items():
        ok, detail = _check_module(module_path)
        results[module_path] = {"ok": ok, "detail": detail}
        if ok:
            ok_count += 1
        else:
            fail_count += 1

    summary = {"ok": ok_count, "failed": fail_count, "total": len(mapping)}

    if args.json_path:
        report = {"summary": summary, "modules": results}
        Path(args.json_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Router Mapping Verification")
    print(f"Total: {summary['total']}  OK: {summary['ok']}  Failed: {summary['failed']}")
    print("")

    for module_path, info in sorted(results.items()):
        status = "OK" if info["ok"] else "FAIL"
        print(f"{status} {module_path} - {info['detail']}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
