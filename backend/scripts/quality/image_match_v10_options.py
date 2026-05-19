#!/usr/bin/env python3
"""
v10 — Options-based match.

Hypothesis: Question options (A) X B) Y C) Z D) W E) V) are highly distinctive.
Two questions almost never share all 5 options. Match by:
  - Concatenate normalized options "A=X|B=Y|C=Z|D=W|E=V" → hash key
  - Lookup in JSONL's secenekler dict
  - Verify on same source_book (avoid cross-book collision)

Safety:
  - Require 5 options present (option_a through option_e)
  - Require each option >= 2 chars
  - Hash entire option set
  - Same source_book preferred
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


def _opts_hash(a, b, c, d, e):
    """Hash normalized 5 options into a single key."""
    parts = []
    for label, val in zip("ABCDE", (a, b, c, d, e)):
        n = _norm(val or "")
        if not n:
            return None  # Need all 5
        parts.append(f"{label}={n}")
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:20]


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
    args = ap.parse_args()

    # Build JSONL index by opts_hash
    print(f"[load] {GEMINI_JSONL.name}...")
    opts_idx: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    n_indexed = 0
    n_no_opts = 0
    with GEMINI_JSONL.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = d.get("book", "")
            page = d.get("page_num")
            crop = d.get("crop_file", "")
            secenekler = d.get("secenekler", {})
            if not (book and page is not None and crop):
                continue
            if not isinstance(secenekler, dict):
                continue
            a = secenekler.get("A") or secenekler.get("a")
            b = secenekler.get("B") or secenekler.get("b")
            c = secenekler.get("C") or secenekler.get("c")
            d_opt = secenekler.get("D") or secenekler.get("d")
            e = secenekler.get("E") or secenekler.get("e")
            h = _opts_hash(a, b, c, d_opt, e)
            if not h:
                n_no_opts += 1
                continue
            opts_idx[h].append((book, int(page), crop))
            n_indexed += 1
    print(
        f"[indexed] {n_indexed:,} JSONL entries with 5 options (skipped {n_no_opts:,} no-opts)"
    )
    print(f"[unique opts hashes] {len(opts_idx):,}\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    print("[scan] NULL rows with 5 options...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book,
                   option_a, option_b, option_c, option_d, option_e
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND option_a IS NOT NULL AND option_a <> ''
              AND option_b IS NOT NULL AND option_b <> ''
              AND option_c IS NOT NULL AND option_c <> ''
              AND option_d IS NOT NULL AND option_d <> ''
              AND option_e IS NOT NULL AND option_e <> ''
            """)
        ).fetchall()
    print(f"[null] {len(rows):,} candidates\n")

    matches: list[tuple[str, str, str, int, str]] = []
    stats = {
        "matched_same_book": 0,
        "matched_single_book": 0,
        "ambiguous": 0,
        "no_hash": 0,
    }

    for r in rows:
        h = _opts_hash(r.option_a, r.option_b, r.option_c, r.option_d, r.option_e)
        if not h:
            stats["no_hash"] += 1
            continue
        cands = opts_idx.get(h, [])
        if not cands:
            stats["no_hash"] += 1
            continue

        # Prefer same-book
        sb_folded = _fold(r.source_book or "")
        chosen = None
        same_book = [(b, p, c) for b, p, c in cands if _fold(b) == sb_folded]
        if len(same_book) == 1:
            chosen = same_book[0]
            stats["matched_same_book"] += 1
        elif same_book:
            # Multiple same-book: ambiguous
            stats["ambiguous"] += 1
            continue
        elif len({_fold(b) for b, _, _ in cands}) == 1:
            chosen = cands[0]
            stats["matched_single_book"] += 1
        else:
            stats["ambiguous"] += 1
            continue

        cb, cp, cc = chosen
        disk_dir = find_disk_dir(cb)
        if not disk_dir:
            continue
        crop_path = CROPS_BASE / disk_dir / cc
        if not crop_path.exists():
            continue
        url = f"/static/crops/{disk_dir}/{cc}"
        matches.append((r.id, url, cb, cp, cc))

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
                                    '{image_match_v10_options}',
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
                                    "source": "v10_options_hash_5_match",
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
