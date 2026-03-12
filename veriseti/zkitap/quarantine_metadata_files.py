#!/usr/bin/env python3
"""
Quarantine metadata files from screenshots tree without filename collisions.

Moves files by preserving relative directory structure under quarantine root and
writes a JSONL manifest for traceability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def iter_metadata_files(root: Path):
    for pattern in ("**/desktop.ini", "**/*.lnk"):
        for p in root.glob(pattern):
            if p.is_file():
                yield p


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine desktop.ini and .lnk files safely")
    parser.add_argument(
        "--screenshots-root",
        default="veriseti/zkitap/screenshots",
        help="Screenshots directory",
    )
    parser.add_argument(
        "--quarantine-root",
        default="veriseti/zkitap/_quarantine_metadata_tree",
        help="Quarantine base directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned moves only",
    )
    args = parser.parse_args()

    screenshots_root = Path(args.screenshots_root).resolve()
    quarantine_root = Path(args.quarantine_root).resolve()
    manifest_path = quarantine_root / "manifest.jsonl"

    files = sorted(set(iter_metadata_files(screenshots_root)))
    if not files:
        print("No metadata files found.")
        return 0

    if not args.dry_run:
        quarantine_root.mkdir(parents=True, exist_ok=True)
        manifest_file = manifest_path.open("a", encoding="utf-8")
    else:
        manifest_file = None

    moved = 0
    try:
        for src in files:
            rel = src.relative_to(screenshots_root)
            dst = quarantine_root / rel
            if args.dry_run:
                print(f"DRY-RUN {src} -> {dst}")
                moved += 1
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dst)
            manifest_file.write(
                json.dumps({"src": str(src), "dst": str(dst)}, ensure_ascii=False) + "\n"
            )
            moved += 1
    finally:
        if manifest_file is not None:
            manifest_file.close()

    print(f"Moved: {moved}")
    print(f"Manifest: {manifest_path}" if not args.dry_run else "Dry-run completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
