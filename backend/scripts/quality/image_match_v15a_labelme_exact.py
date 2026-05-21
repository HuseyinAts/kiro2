#!/usr/bin/env python3
"""
v15a — Labelme manual annotation exact-count crop pairing.

For (book, page) pages where:
  - Labelme JSON has N "soru" bboxes (manually verified)
  - DB has exactly N NULL rows
  - Same source_book exists in both veriseti/zkitap and d-dataset
→ Crop the page screenshot using labelme bbox, save into d-dataset/output/crops/,
  assign image_url.

NULL rows paired to bboxes by Y-coordinate ordering (reading order).
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ZKITAP = PROJECT_ROOT / "veriseti" / "zkitap" / "screenshots"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s)).strip("_")


_DD_DIRS = None


def find_dd_dir(book):
    """Find matching d-dataset crop dir for given source_book."""
    global _DD_DIRS
    if _DD_DIRS is None:
        _DD_DIRS = {_canon(d.name): d.name for d in CROPS_BASE.iterdir() if d.is_dir()}
    return _DD_DIRS.get(_canon(book))


_ZK_DIRS = None


def find_zk_dir(book):
    """Find matching zkitap screenshot dir."""
    global _ZK_DIRS
    if _ZK_DIRS is None:
        _ZK_DIRS = {_canon(d.name): d.name for d in ZKITAP.iterdir() if d.is_dir()}
    return _ZK_DIRS.get(_canon(book))


def bbox_from_shape(shape):
    """Extract (x1, y1, x2, y2) from labelme rectangle shape."""
    pts = shape.get("points", [])
    if not pts:
        return None
    xs = [p[0] for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2]
    ys = [p[1] for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # Build labelme index: (book_canon, page) → list[(bbox, soru_index)]
    print("[load] labelme JSONs with soru bboxes...")
    labelme_pages: dict[tuple[str, int], dict] = {}
    for d in ZKITAP.iterdir():
        if not d.is_dir():
            continue
        bk = _canon(d.name)
        for j in d.glob("sayfa_*.json"):
            try:
                data = json.loads(j.read_text(encoding="utf-8"))
            except Exception:
                continue
            shapes = data.get("shapes", [])
            soru = [s for s in shapes if s.get("label") == "soru"]
            if not soru:
                continue
            m = re.search(r"sayfa_(\d+)", j.name)
            if not m:
                continue
            page = int(m.group(1))
            # Sort by Y (top), then X (left) for reading order
            bboxes = []
            for s in soru:
                b = bbox_from_shape(s)
                if b:
                    bboxes.append(b)
            bboxes.sort(key=lambda x: (x[1], x[0]))
            labelme_pages[(bk, page)] = {
                "dir_name": d.name,
                "bboxes": bboxes,
                "img_w": data.get("imageWidth", 1920),
                "img_h": data.get("imageHeight", 1080),
            }
    print(f"[loaded] {len(labelme_pages):,} labelme pages\n")

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    print("[scan] NULL DB rows...")
    with eng.connect() as c:
        rows = c.execute(
            text("""
            SELECT id::text, source_book, source_page, created_at
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND source_book IS NOT NULL AND source_page IS NOT NULL
            ORDER BY source_book, source_page, created_at
        """)
        ).fetchall()

    null_by_page: dict[tuple[str, int], list] = defaultdict(list)
    book_orig: dict[tuple[str, int], str] = {}
    for r in rows:
        bk = _canon(r.source_book)
        key = (bk, int(r.source_page))
        null_by_page[key].append(r.id)
        book_orig[key] = r.source_book

    # Find exact count match
    matches: list[tuple[str, str, tuple]] = []  # (db_id, url, bbox)
    stats = {"exact_count": 0, "count_mismatch": 0, "no_dd_dir": 0, "no_zk_dir": 0}

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow required. pip install Pillow")
        return 1

    for key, null_ids in null_by_page.items():
        if key not in labelme_pages:
            continue
        lm = labelme_pages[key]
        if len(null_ids) != len(lm["bboxes"]):
            stats["count_mismatch"] += 1
            continue
        stats["exact_count"] += 1

        dd_dir = find_dd_dir(book_orig[key])
        if not dd_dir:
            stats["no_dd_dir"] += 1
            continue
        zk_dir = find_zk_dir(book_orig[key])
        if not zk_dir:
            stats["no_zk_dir"] += 1
            continue

        # Open source screenshot
        page = key[1]
        src_png = ZKITAP / zk_dir / f"sayfa_{page:04d}.png"
        if not src_png.exists():
            continue
        try:
            img = Image.open(src_png)
        except Exception:
            continue

        for null_id, bbox in zip(null_ids, lm["bboxes"]):
            x1, y1, x2, y2 = map(int, bbox)
            crop = img.crop((x1, y1, x2, y2))
            crop_name = f"{dd_dir}_p{page:04d}_LM{null_ids.index(null_id) + 1:02d}.png"
            crop_path = CROPS_BASE / dd_dir / crop_name
            crop_path.parent.mkdir(parents=True, exist_ok=True)
            crop.save(crop_path, "PNG", optimize=True)
            url = f"/static/crops/{dd_dir}/{crop_name}"
            matches.append((null_id, url, (x1, y1, x2, y2)))

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\n[matches]: {len(matches)}")

    if matches:
        print("\n[sample first 3]")
        for m in matches[:3]:
            print(f"  {m[0][:8]} → {m[1]}  bbox={m[2]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches)} satır...")
        for i in range(0, len(matches), 100):
            batch = matches[i : i + 100]
            with eng.begin() as c:
                for qid, url, bbox in batch:
                    c.execute(
                        text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v15a_labelme_exact}',
                                    CAST(:audit AS jsonb),
                                    TRUE
                                )::json,
                                updated_at=NOW()
                            WHERE id::text=:qid
                        """),
                        {
                            "url": url,
                            "qid": qid,
                            "audit": json.dumps(
                                {
                                    "date": "2026-05-19",
                                    "source": "v15a_labelme_manual_exact_count",
                                    "bbox": list(bbox),
                                }
                            ),
                        },
                    )
        print("[done]")
        with eng.connect() as c:
            null_n = c.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                    "AND (question_image_url IS NULL OR question_image_url='')"
                )
            ).scalar()
            print(f"\nFINAL NULL: {null_n:,}")
    else:
        print("\n[dry-run]")


if __name__ == "__main__":
    sys.exit(main() or 0)
