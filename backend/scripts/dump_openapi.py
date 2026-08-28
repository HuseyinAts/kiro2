#!/usr/bin/env python3
"""Dump FastAPI OpenAPI schema to JSON (offline Dalga B input; no HTTP server)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    default = Path(__file__).resolve().parent.parent / "openapi_snapshot.json"
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    backend_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_root))
    from main import app

    out.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(out)


if __name__ == "__main__":
    main()
