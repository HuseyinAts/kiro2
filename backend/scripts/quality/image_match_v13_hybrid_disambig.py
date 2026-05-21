#!/usr/bin/env python3
"""
v13 — Hybrid disambiguation for residual cases.

After v12 (page residual unique), remaining cases on (book, page):
  - single_null_multi_unused (3,641): 1 NULL DB row, >1 unused JSONL crops
    → disambiguate by option match count (highest count wins, must be unique)
  - multi_null_single_unused (779): >1 NULL DB rows, 1 unused JSONL crop
    → assign to the NULL row whose options best match (if unique winner)

Safety:
  - Require ≥3/5 option matches AND winner option count > 2nd place
  - Same source_book + source_page (already enforced by being in same group)
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


def _opt_match(db_opts, jsonl_opts) -> int:
    matches = 0
    for db, js in zip(db_opts, jsonl_opts):
        n_db = _norm(db or "")
        n_js = _norm(js or "")
        if len(n_db) >= 2 and n_db == n_js:
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
    ap.add_argument("--min-match", type=int, default=3, help="Min option matches")
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index: (book_key, page) → list[(crop, opts_list)]
    page_idx: dict[tuple[str, int], list[tuple[str, list[str]]]] = defaultdict(list)
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
            page_idx[(_book_key(book), int(page))].append((crop, opts))
    print(f"[indexed] {len(page_idx):,} (book, page) groups\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    print("[scan] active rows by (book, page)...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book, source_page, question_image_url,
                   option_a, option_b, option_c, option_d, option_e
            FROM question_bank
            WHERE is_active=true
              AND source_book IS NOT NULL AND source_page IS NOT NULL
        """)
        ).fetchall()

    by_page: dict[tuple[str, int], dict] = defaultdict(
        lambda: {"nulls": [], "used_crops": set(), "source_book_orig": ""}
    )
    for r in rows:
        bk = _book_key(r.source_book)
        key = (bk, int(r.source_page))
        by_page[key]["source_book_orig"] = r.source_book
        opts = [
            r.option_a or "",
            r.option_b or "",
            r.option_c or "",
            r.option_d or "",
            r.option_e or "",
        ]
        if not r.question_image_url:
            by_page[key]["nulls"].append((r.id, opts))
        else:
            fname = r.question_image_url.split("/")[-1] if r.question_image_url else ""
            if fname:
                by_page[key]["used_crops"].add(fname)

    matches = []
    stats = {
        "single_null_disambig": 0,
        "multi_null_assigned": 0,
        "ambiguous_tied": 0,
        "below_threshold": 0,
        "no_jsonl_page": 0,
    }

    for (bk, page), g in by_page.items():
        if not g["nulls"]:
            continue

        jsonl = page_idx.get((bk, page), [])
        if not jsonl:
            stats["no_jsonl_page"] += 1
            continue

        # Unused crops on this page
        unused = [(crop, opts) for crop, opts in jsonl if crop not in g["used_crops"]]
        if not unused:
            continue

        n_null = len(g["nulls"])
        n_unused = len(unused)

        # Case A: 1 NULL, >1 unused — pick unused with best option match
        if n_null == 1 and n_unused > 1:
            null_id, null_opts = g["nulls"][0]
            scored = sorted(
                ((_opt_match(null_opts, opts), crop) for crop, opts in unused),
                reverse=True,
            )
            best_score, best_crop = scored[0]
            second_score = scored[1][0] if len(scored) > 1 else -1
            if best_score < args.min_match:
                stats["below_threshold"] += 1
                continue
            if best_score == second_score:
                stats["ambiguous_tied"] += 1
                continue
            disk_dir = find_disk_dir(g["source_book_orig"])
            if not disk_dir:
                continue
            crop_path = CROPS_BASE / disk_dir / best_crop
            if not crop_path.exists():
                continue
            url = f"/static/crops/{disk_dir}/{best_crop}"
            matches.append(
                (
                    null_id,
                    url,
                    g["source_book_orig"],
                    page,
                    best_crop,
                    f"1null_{n_unused}unused_{best_score}match",
                )
            )
            stats["single_null_disambig"] += 1

        # Case B: >1 NULL, 1 unused — assign unused to NULL with best match
        elif n_null > 1 and n_unused == 1:
            crop, crop_opts = unused[0]
            scored = sorted(
                (
                    (_opt_match(null_opts, crop_opts), null_id)
                    for null_id, null_opts in g["nulls"]
                ),
                reverse=True,
            )
            best_score, best_id = scored[0]
            second_score = scored[1][0] if len(scored) > 1 else -1
            if best_score < args.min_match:
                stats["below_threshold"] += 1
                continue
            if best_score == second_score:
                stats["ambiguous_tied"] += 1
                continue
            disk_dir = find_disk_dir(g["source_book_orig"])
            if not disk_dir:
                continue
            crop_path = CROPS_BASE / disk_dir / crop
            if not crop_path.exists():
                continue
            url = f"/static/crops/{disk_dir}/{crop}"
            matches.append(
                (
                    best_id,
                    url,
                    g["source_book_orig"],
                    page,
                    crop,
                    f"{n_null}null_1unused_{best_score}match",
                )
            )
            stats["multi_null_assigned"] += 1

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[matches]: {len(matches):,}")

    if matches:
        print("\n[sample first 5]")
        for m in matches[:5]:
            print(f"  {m[0][:8]} {m[2][:30]} p{m[3]} [{m[5]}] → {m[4]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, book, page, crop, reason in batch:
                    c.execute(
                        sa_text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v13_hybrid_disambig}',
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
                                    "source": "v13_hybrid_options_disambig",
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                    "reason": reason,
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
        print("\n[dry-run]")


if __name__ == "__main__":
    main()
