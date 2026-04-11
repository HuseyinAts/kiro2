"""Smoke test: import every backend/api/*.py module and report failures."""

from __future__ import annotations

import importlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

failed: list[tuple[str, str]] = []
count = 0
for p in (ROOT / "api").rglob("*.py"):
    if "_deprecated" in p.parts:
        continue
    if p.name == "__init__.py":
        continue
    rel = p.relative_to(ROOT).with_suffix("")
    mod = ".".join(rel.parts)
    try:
        importlib.import_module(mod)
        count += 1
    except Exception as e:
        failed.append((mod, f"{type(e).__name__}: {e}"))

print(f"Imported {count} modules, {len(failed)} failed")
for m, e in failed[:30]:
    print(f"  FAIL {m}: {e[:200]}")
