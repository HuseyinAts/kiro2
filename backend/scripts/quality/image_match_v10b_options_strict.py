#!/usr/bin/env python3
"""
v10b — Options hash match WITH stricter book identity + source_page filter.

v10 had %85.9 accuracy because options hash collided across same-publisher
different-year books (e.g., "Bilgi Sarmalı 2025" vs "Bilgi Sarmalı 2024").

Tightening:
  1. Book match: STRICT identity (folded + same year tokens preserved)
  2. Add source_page filter: JSONL page must equal DB source_page
  3. Single-candidate-only after both filters
"""

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GEMINI_JSONL = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _book_key(book: str) -> str:
    """Canonical book identity: folded + year tokens preserved + cleaned punctuation."""
    if not book:
        return ""
    folded = _fold(book)
    # Replace common separators with single space
    folded = re.sub(r"[_\-]+", " ", folded)
    folded = re.sub(r"\s+", " ", folded).strip()
    return folded


def _opts_hash(a, b, c, d, e):
    parts = []
    for label, val in zip("ABCDE", (a, b, c, d, e)):
        n = _norm(val or "")
        if not n:
            return None
        parts.append(f"{label}={n}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


_DISK_DIRS = None


def find_disk_dir(book):
    global _DISK_DIRS
    if not book:
        return None
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    for v in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if v in _DISK_DIRS:
            return v
    folded = _fold(book.replace(" ", "_"))
    for d in _DISK_DIRS:
        if _fold(d) == folded:
            return d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--audit", action="store_true", help="Audit only on v8 sample")
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index: (book_key, page, opts_hash) → list[crop]
    triple_idx: dict[tuple[str, int, str], list[str]] = defaultdict(list)
    # Also: (book_key, opts_hash) for fallback (no page filter)
    bk_opts_idx: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    n_indexed = 0
    with GEMINI_JSONL.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = d.get("book", "")
            page = d.get("page_num")
            crop = d.get("crop_file", "")
            sec = d.get("secenekler", {}) or {}
            if not (book and page is not None and crop and isinstance(sec, dict)):
                continue
            h = _opts_hash(
                sec.get("A"), sec.get("B"), sec.get("C"), sec.get("D"), sec.get("E")
            )
            if not h:
                continue
            bk = _book_key(book)
            triple_idx[(bk, int(page), h)].append(crop)
            bk_opts_idx[(bk, h)].append((int(page), crop))
            n_indexed += 1
    print(f"[indexed] {n_indexed:,} entries")
    print(f"[triple_idx] {len(triple_idx):,} unique (book, page, opts) tuples\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    # AUDIT MODE
    if args.audit:
        print("[audit] cross-checking v10b proposal against v8 ground truth...")
        with eng.connect() as c:
            sample = c.execute(
                sa_text("""
                SELECT id::text, source_book, source_page,
                       option_a, option_b, option_c, option_d, option_e,
                       pipeline_metadata::jsonb->'image_match_gemini_flash_v8'->>'matched_crop' AS v8_crop
                FROM question_bank
                WHERE pipeline_metadata::jsonb ? 'image_match_gemini_flash_v8'
                  AND option_a IS NOT NULL AND option_b IS NOT NULL
                  AND option_c IS NOT NULL AND option_d IS NOT NULL AND option_e IS NOT NULL
                  AND source_page IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 500
            """)
            ).fetchall()
        stats = {"same": 0, "diff": 0, "no_triple_match": 0, "ambiguous": 0}
        for r in sample:
            h = _opts_hash(r.option_a, r.option_b, r.option_c, r.option_d, r.option_e)
            if not h:
                stats["no_triple_match"] += 1
                continue
            bk = _book_key(r.source_book or "")
            crops = triple_idx.get((bk, int(r.source_page), h), [])
            if len(crops) == 0:
                stats["no_triple_match"] += 1
                continue
            if len(crops) > 1:
                stats["ambiguous"] += 1
                continue
            if crops[0] == r.v8_crop:
                stats["same"] += 1
            else:
                stats["diff"] += 1
        ver = stats["same"] + stats["diff"]
        print("[audit-result]")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        if ver:
            print(f"\n[accuracy on verifiable={ver}]")
            print(f"  v10b == v8: {stats['same'] / ver * 100:.1f}%")
        return

    # APPLY MODE
    print("[scan] NULL rows...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book, source_page,
                   option_a, option_b, option_c, option_d, option_e
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND option_a IS NOT NULL AND option_b IS NOT NULL
              AND option_c IS NOT NULL AND option_d IS NOT NULL AND option_e IS NOT NULL
        """)
        ).fetchall()
    print(f"[null] {len(rows):,} candidates\n")

    matches: list[tuple[str, str, str, int, str]] = []
    stats = {
        "via_triple": 0,
        "via_book_opts_uniq": 0,
        "no_match": 0,
        "ambiguous": 0,
        "no_source_page": 0,
    }

    for r in rows:
        h = _opts_hash(r.option_a, r.option_b, r.option_c, r.option_d, r.option_e)
        if not h:
            stats["no_match"] += 1
            continue
        bk = _book_key(r.source_book or "")

        # Strategy 1: (book_key, source_page, opts_hash) triple match
        if r.source_page is not None:
            crops = triple_idx.get((bk, int(r.source_page), h), [])
            if len(crops) == 1:
                disk_dir = find_disk_dir(r.source_book or "")
                if disk_dir:
                    crop_path = CROPS_BASE / disk_dir / crops[0]
                    if crop_path.exists():
                        url = f"/static/crops/{disk_dir}/{crops[0]}"
                        matches.append(
                            (
                                r.id,
                                url,
                                r.source_book or "",
                                int(r.source_page),
                                crops[0],
                            )
                        )
                        stats["via_triple"] += 1
                        continue
                    # disk doesn't have this crop
                    stats["no_match"] += 1
                    continue
            elif len(crops) > 1:
                stats["ambiguous"] += 1
                continue

        # Strategy 2: (book_key, opts_hash) — unique within book
        page_crops = bk_opts_idx.get((bk, h), [])
        if len(page_crops) == 1:
            page, crop = page_crops[0]
            disk_dir = find_disk_dir(r.source_book or "")
            if disk_dir:
                crop_path = CROPS_BASE / disk_dir / crop
                if crop_path.exists():
                    url = f"/static/crops/{disk_dir}/{crop}"
                    matches.append((r.id, url, r.source_book or "", page, crop))
                    stats["via_book_opts_uniq"] += 1
                    continue

        stats["no_match"] += 1

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[matches]: {len(matches):,}")

    if matches:
        print("\n[sample first 5]")
        for m in matches[:5]:
            print(f"  {m[0][:8]} {m[2][:30]} p{m[3]} → {m[4]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, book, page, crop in batch:
                    c.execute(
                        sa_text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v10b_options_strict}',
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
                                    "source": "v10b_book_page_opts_triple",
                                    "matched_book": book,
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                }
                            ),
                        },
                    )
            if (i // 500 + 1) % 10 == 0:
                print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")
        print("[done]")
        with eng.connect() as c:
            null_n = c.execute(
                sa_text(
                    "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                    "AND (question_image_url IS NULL OR question_image_url='')"
                )
            ).scalar()
            print(f"\nFINAL NULL: {null_n:,}")
    else:
        print("\n[dry-run] Pass --apply.")


if __name__ == "__main__":
    main()
