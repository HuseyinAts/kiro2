#!/usr/bin/env python
"""
Cursor afterFileEdit hook — pilot sapma pattern'lerini warn-only yakalar.

D-9:  Plan-dışı test dosyası düzenleme
D-11: Migration dosyası düzenleme (alembic heads teyit hatırlatması)
D-12: Service dosyası düzenleme (container deploy hatırlatması)

Cursor input formatı (hooks.md docs):
  {
    "file_path": "<absolute path>",
    ...
  }

Bu hook BLOCK ETMEZ — sadece stderr'e uyarı yazar.
"""
import json
import os
import sys

# Windows cp1254 encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower().startswith("cp"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def extract_file_path(hook_input: dict) -> str:
    if fp := hook_input.get("file_path"):
        return fp
    if fp := hook_input.get("tool_input", {}).get("file_path"):
        return fp
    return ""


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return 0

    file_path = extract_file_path(hook_input)
    if not file_path:
        return 0

    normalized = file_path.replace("\\", "/")

    # D-11: Migration dosyası düzenlendi
    if "alembic/versions/" in normalized:
        print(
            f"[pilot-guard WARNING] Migration düzenlendi: {os.path.basename(file_path)}\n"
            f"  → down_revision doğrulaması gerekli:\n"
            f"    docker exec kiro2-backend alembic heads",
            file=sys.stderr,
        )

    # D-12: Service dosyası düzenlendi
    if "/backend/services/" in normalized:
        print(
            f"[pilot-guard WARNING] Service düzenlendi: {os.path.basename(file_path)}\n"
            f"  → Container deploy doğrulaması gerekli:\n"
            f"    docker cp + docker restart kiro2-backend + grep",
            file=sys.stderr,
        )

    # D-9: Test dosyası düzenlendi
    if "/backend/tests/" in normalized:
        print(
            f"[pilot-guard WARNING] Test dosyası düzenlendi: {os.path.basename(file_path)}\n"
            f"  → Plan-dışı test ekleme D-9 sapması olabilir.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[WARN] pilot-guard: {e}", file=sys.stderr)
        sys.exit(0)
