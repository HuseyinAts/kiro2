#!/usr/bin/env python3
"""
Ana plan §9 Dalga B: OpenAPI’de requestBody şemasında tenant/student alanı ipucu (TSV).

    cd backend
    python scripts/dalga_b_requestbody_tenant_id.py
    python scripts/dalga_b_requestbody_tenant_id.py http://127.0.0.1:8000/openapi.json

Sütunlar: METHOD path tag operationId body_field_hint
body_field_hint: requestBody (veya türetilmiş schema) string içinde
  student_id|user_id|child_id|mentor|veli|ogrenci|parent_id|owner alan adları
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from urllib.parse import urlparse

MUTATING = frozenset({"post", "put", "patch", "delete"})

# RequestBody’de geçerse IDOR yüzeyi adayı (kaba süzgeç)
PATTERN = re.compile(
    r"student_id|user_id|child_id|parent_id|mentor_id|mentee_id|"
    r"ogrenci|veli|owner_id|target_user|recipient_id|studentId|userId",
    re.IGNORECASE,
)


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/openapi.json"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SystemExit("Only http(s) OpenAPI URL allowed")
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
        spec = json.load(resp)
    paths: dict = spec.get("paths") or {}
    print("method\tpath\ttag\toperationId\tbody_tenant_hint")
    for p in sorted(paths):
        for method, op in paths[p].items():
            m = method.lower()
            if m not in MUTATING or not isinstance(op, dict):
                continue
            body = op.get("requestBody")
            if not body:
                continue
            blob = json.dumps(body, ensure_ascii=False)
            if not PATTERN.search(blob):
                continue
            tag = (op.get("tags") or ["?"])[0]
            oid = str(op.get("operationId", ""))
            m_obj = PATTERN.search(blob)
            hint = m_obj.group(0) if m_obj else "yes"
            print(f"{m.upper()}\t{p}\t{tag}\t{oid}\t{hint}")


if __name__ == "__main__":
    main()
