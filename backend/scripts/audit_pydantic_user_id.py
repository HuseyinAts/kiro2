"""Audit: Pydantic BaseModel classes in backend/api/ that declare `user_id: int`.

Session 148 prophylactic sweep after GF107 (rule of five).

Background
==========
KIRO2 auth returns `AuthenticatedUser.id` as a UUID **string**, not an
integer. Any Pydantic model that declares `user_id: int` will raise
`pydantic.ValidationError` when the handler assigns `current_user.id` to
that field — and most handlers wrap the crash inside a bare
`except Exception` that re-raises as `HTTPException(500)`, so the real
cause is invisible to the client.

Known crash sites
-----------------
- GF20 Session 139: `AdhdPomodoroSessionResponse`, `InactivityAlert`,
  `FocusExerciseProgress` (3 models, 1 file)
- GF71 Session 144: `TaskResponse` (1 model, 1 file)
- GF107 Session 148: `VirtualBlockProgress`, `GeoGebraActivity`,
  `GeometryToolUsage`, `TangramPuzzle` (4 models, 1 file)

Rule of five established: any `user_id: int` in a Pydantic BaseModel that
lives under `backend/api/` is a guaranteed crash site the moment a handler
does `Model(user_id=current_user.id, ...)`.

Usage
=====
    python backend/scripts/audit_pydantic_user_id.py          # report only
    python backend/scripts/audit_pydantic_user_id.py --fail   # CI gate

Exit codes
----------
0  clean
1  at least one risky model found under backend/api/

Scope
=====
This audit only flags models under `backend/api/`. Pydantic models that
live under `backend/core/` or `backend/services/` may legitimately take
an integer user_id (internal DTOs that are never touched by
`current_user.id`). Extend the scope here if a future crash proves
otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
API = BACKEND / "api"


def find_risky_models(root: Path) -> list[tuple[Path, str, int]]:
    """Return (file, class_name, lineno) for every Pydantic model with user_id: int."""
    hits: list[tuple[Path, str, int]] = []
    for p in root.rglob("*.py"):
        sp = str(p).replace("\\", "/")
        if "_deprecated" in sp or "__pycache__" in sp:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in re.finditer(r"class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)\s*:", src):
            cls_name = m.group(1)
            cls_start = m.end()
            # slice body until next class or EOF
            next_cls = re.search(r"\nclass\s+\w+", src[cls_start:])
            cls_end = cls_start + next_cls.start() if next_cls else len(src)
            body = src[cls_start:cls_end]
            field = re.search(r"^\s+user_id:\s*int\b", body, re.MULTILINE)
            if field:
                # compute line number of the `user_id: int` line
                offset = cls_start + field.start()
                lineno = src.count("\n", 0, offset) + 1
                hits.append((p, cls_name, lineno))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fail",
        action="store_true",
        help="Exit with code 1 if any risky model is found (CI gate).",
    )
    args = parser.parse_args()

    hits = find_risky_models(API)
    if not hits:
        print("[OK] No Pydantic model under backend/api/ declares `user_id: int`.")
        return 0

    print(
        f"[FAIL] Found {len(hits)} Pydantic model(s) under backend/api/ "
        f"with `user_id: int`. Each is a guaranteed crash site when "
        f"assigned `current_user.id` (UUID string). Fix: `user_id: str`."
    )
    print()
    for p, cls, lineno in hits:
        rel = p.relative_to(BACKEND.parent)
        print(f"  {rel}:{lineno}  class {cls}")
    print()
    print("See backend/scripts/audit_pydantic_user_id.py for context.")
    return 1 if args.fail else 0


if __name__ == "__main__":
    sys.exit(main())
