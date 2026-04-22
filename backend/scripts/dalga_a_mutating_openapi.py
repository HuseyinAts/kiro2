#!/usr/bin/env python3
"""
Ana plan §9 Dalga A: OpenAPI üzerinden mutating operasyon envanteri (TSV).

    cd backend
    python scripts/dalga_a_mutating_openapi.py
    python scripts/dalga_a_mutating_openapi.py https://example.com/openapi.json

Sütunlar: METHOD path tag operationId student_hint
"""
from __future__ import annotations

import json
import sys
import urllib.request

MUTATING = frozenset({"post", "put", "patch", "delete"})
HINT_KEYWORDS = (
    "student",
    "ogrenci",
    "user_id",
    "child",
    "cocuk",
    "fsrs",
    "sync",
    "veli",
    "parent",
)


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/openapi.json"
    with urllib.request.urlopen(url, timeout=30) as resp:
        spec = json.load(resp)
    paths: dict = spec.get("paths") or {}
    print("method\tpath\ttag\toperationId\tstudent_surface_hint")
    for p in sorted(paths):
        for method, op in paths[p].items():
            m = method.lower()
            if m not in MUTATING:
                continue
            if not isinstance(op, dict):
                continue
            tag = (op.get("tags") or ["?"])[0]
            oid = str(op.get("operationId", ""))
            low = f"{p} {oid}".lower()
            hint = "yes" if any(k in low for k in HINT_KEYWORDS) else ""
            print(f"{m.upper()}\t{p}\t{tag}\t{oid}\t{hint}")


if __name__ == "__main__":
    main()
