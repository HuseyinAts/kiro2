#!/usr/bin/env python3
"""
v11a — Partial options match (≥4/5 + book + page).

Hypothesis: DB question_text may differ from JSONL soru_metni (LaTeX render,
encoding fixes) but options are usually preserved. If 4 of 5 options match
EXACTLY (normalized) within the same (book, page), this is a deterministic
match (probability of 4/5 collision on same page is very low).

Safety:
  - Same source_book key (year-preserved)
  - Same source_page
  - Each option ≥2 chars after normalize
  - Exactly 1 candidate on the page passes 4/5 threshold

Audit first against v8 ground truth.
"""

import argparse
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
    if not book:
        return ""
    folded = _fold(book)
    folded = re.sub(r"[_\-]+", " ", folded)
    folded = re.sub(r"\s+", " ", folded).strip()
    return folded


def _option_match_count(db_opts: list[str], jsonl_opts: list[str]) -> int:
    """Count matching options (normalized, position-aware)."""
    matches = 0
    for db, js in zip(db_opts, jsonl_opts):
        n_db = _norm(db or "")
        n_js = _norm(js or "")
        if len(n_db) < 2 or len(n_js) < 2:
            continue
        if n_db == n_js:
            matches += 1
    return matches


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
    ap.add_argument("--audit", action="store_true")
    ap.add_argument(
        "--threshold", type=int, default=4, help="Min option matches (default 4)"
    )
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index: (book_key, page) → list[(opts_list, crop)]
    page_idx: dict[tuple[str, int], list[tuple[list[str], str]]] = defaultdict(list)
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
            opts = [
                sec.get("A") or sec.get("a") or "",
                sec.get("B") or sec.get("b") or "",
                sec.get("C") or sec.get("c") or "",
                sec.get("D") or sec.get("d") or "",
                sec.get("E") or sec.get("e") or "",
            ]
            page_idx[(_book_key(book), int(page))].append((opts, crop))
            n_indexed += 1
    print(f"[indexed] {n_indexed:,} entries, {len(page_idx):,} (book, page) groups\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    if args.audit:
        print("[audit] cross-checking partial-match against v8...")
        with eng.connect() as c:
            sample = c.execute(
                sa_text("""
                SELECT id::text, source_book, source_page,
                       option_a, option_b, option_c, option_d, option_e,
                       pipeline_metadata::jsonb->'image_match_gemini_flash_v8'->>'matched_crop' AS v8_crop
                FROM question_bank
                WHERE pipeline_metadata::jsonb ? 'image_match_gemini_flash_v8'
                  AND source_page IS NOT NULL
                ORDER BY RANDOM() LIMIT 500
            """)
            ).fetchall()
        stats = {
            "same": 0,
            "diff": 0,
            "no_match": 0,
            "ambiguous": 0,
            "below_threshold": 0,
        }
        for r in sample:
            bk = _book_key(r.source_book or "")
            db_opts = [
                r.option_a or "",
                r.option_b or "",
                r.option_c or "",
                r.option_d or "",
                r.option_e or "",
            ]
            cands_with_match = []
            for jsonl_opts, crop in page_idx.get((bk, int(r.source_page)), []):
                mc = _option_match_count(db_opts, jsonl_opts)
                if mc >= args.threshold:
                    cands_with_match.append((mc, crop))
            if not cands_with_match:
                stats["no_match"] += 1
                continue
            # Pick highest match count
            cands_with_match.sort(reverse=True)
            best_count = cands_with_match[0][0]
            top = [c for cnt, c in cands_with_match if cnt == best_count]
            if len(top) > 1:
                stats["ambiguous"] += 1
                continue
            if top[0] == r.v8_crop:
                stats["same"] += 1
            else:
                stats["diff"] += 1
        ver = stats["same"] + stats["diff"]
        print("[audit-result]")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        if ver:
            print(f"\n[accuracy on verifiable={ver}]")
            print(
                f"  v11a == v8: {stats['same'] / ver * 100:.1f}% (threshold={args.threshold})"
            )
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
              AND source_page IS NOT NULL
              AND option_a IS NOT NULL
        """)
        ).fetchall()
    print(f"[null] {len(rows):,} candidates\n")

    matches: list[tuple[str, str, str, int, str]] = []
    stats = {"matched": 0, "no_match": 0, "ambiguous": 0}

    for r in rows:
        bk = _book_key(r.source_book or "")
        db_opts = [
            r.option_a or "",
            r.option_b or "",
            r.option_c or "",
            r.option_d or "",
            r.option_e or "",
        ]
        cands_with_match = []
        for jsonl_opts, crop in page_idx.get((bk, int(r.source_page)), []):
            mc = _option_match_count(db_opts, jsonl_opts)
            if mc >= args.threshold:
                cands_with_match.append((mc, crop))

        if not cands_with_match:
            stats["no_match"] += 1
            continue

        cands_with_match.sort(reverse=True, key=lambda x: x[0])
        best_count = cands_with_match[0][0]
        top = [c for cnt, c in cands_with_match if cnt == best_count]
        if len(top) > 1:
            stats["ambiguous"] += 1
            continue

        crop = top[0]
        disk_dir = find_disk_dir(r.source_book or "")
        if not disk_dir:
            stats["no_match"] += 1
            continue
        crop_path = CROPS_BASE / disk_dir / crop
        if not crop_path.exists():
            stats["no_match"] += 1
            continue
        url = f"/static/crops/{disk_dir}/{crop}"
        matches.append((r.id, url, r.source_book or "", int(r.source_page), crop))
        stats["matched"] += 1

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
                                    '{image_match_v11a_partial_options}',
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
                                    "source": "v11a_partial_options_4of5",
                                    "matched_book": book,
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                }
                            ),
                        },
                    )
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
