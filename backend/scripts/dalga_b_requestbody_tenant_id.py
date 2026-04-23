#!/usr/bin/env python3
"""
Ana plan §9 Dalga B: OpenAPI’de requestBody şemasında tenant/student alanı ipucu (TSV).

    cd backend
    python scripts/dalga_b_requestbody_tenant_id.py
    python scripts/dalga_b_requestbody_tenant_id.py http://127.0.0.1:8000/openapi.json
    python scripts/dalga_b_requestbody_tenant_id.py openapi_snapshot.json

Sütunlar: METHOD path tag operationId body_tenant_hint
body_tenant_hint: JSON gövde şemasındaki özellik *adları* (components/schemas $ref çözülerek);
  student_id|user_id|child_id|mentor|veli|ogrenci|parent_id|owner vb. ile eşleşenler.
  Not: Eski sürüm tüm requestBody JSON’unu tarayınca path parametresi adları ($ref içinde)
  yanlış pozitif üretebiliyordu; artık yalnızca property key’leri kontrol edilir.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse

MUTATING = frozenset({"post", "put", "patch", "delete"})

# RequestBody özellik adlarında geçerse IDOR yüzeyi adayı (kaba süzgeç)
PATTERN = re.compile(
    r"student_id|user_id|child_id|parent_id|mentor_id|mentee_id|"
    r"ogrenci|veli|owner_id|target_user|recipient_id|studentId|userId",
    re.IGNORECASE,
)


def load_spec(source: str) -> dict:
    if os.path.isfile(source):
        with open(source, encoding="utf-8") as f:
            return json.load(f)
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        with urllib.request.urlopen(source, timeout=120) as resp:  # noqa: S310
            return json.load(resp)
    raise SystemExit(
        f"OpenAPI kaynagi gecersiz: {source!r} "
        "(http(s) URL veya mevcut .json dosya yolu kullanin)"
    )


def _collect_property_names(
    schema: object,
    schemas: dict,
    out: set[str],
    seen_refs: set[str],
) -> None:
    if not isinstance(schema, dict):
        return
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in seen_refs:
            return
        seen_refs.add(ref)
        name = ref.rsplit("/", 1)[-1]
        sub = schemas.get(name)
        if sub is not None:
            _collect_property_names(sub, schemas, out, seen_refs)
        return
    props = schema.get("properties")
    if isinstance(props, dict):
        for key, subschema in props.items():
            out.add(key)
            _collect_property_names(subschema, schemas, out, set(seen_refs))
    for key in ("allOf", "anyOf", "oneOf"):
        for part in schema.get(key) or []:
            _collect_property_names(part, schemas, out, seen_refs)
    if schema.get("type") == "array":
        items = schema.get("items")
        if items is not None:
            _collect_property_names(items, schemas, out, seen_refs)
    adisc = schema.get("additionalProperties")
    if isinstance(adisc, dict):
        _collect_property_names(adisc, schemas, out, seen_refs)


def mutating_body_tenant_hints(spec: dict, body: dict) -> list[str]:
    schemas = (spec.get("components") or {}).get("schemas") or {}
    names: set[str] = set()
    content = body.get("content") or {}
    for ct, cobj in content.items():
        if "json" not in ct.lower():
            continue
        schema = (cobj or {}).get("schema")
        if schema:
            _collect_property_names(schema, schemas, names, set())
    return sorted(n for n in names if PATTERN.search(n))


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/openapi.json"
    spec = load_spec(src)
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
            hints = mutating_body_tenant_hints(spec, body)
            if not hints:
                continue
            tag = (op.get("tags") or ["?"])[0]
            oid = str(op.get("operationId", ""))
            print(f"{m.upper()}\t{p}\t{tag}\t{oid}\t{','.join(hints)}")


if __name__ == "__main__":
    main()
