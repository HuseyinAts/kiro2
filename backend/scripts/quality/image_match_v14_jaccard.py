#!/usr/bin/env python3
"""
v14 — Token Jaccard similarity on question_text within (book, page).

For each NULL row, compute Jaccard(token_set(db_text), token_set(jsonl_text))
for each unused JSONL crop on the same (book, page).

Accept if:
  - best_score >= 0.60
  - best_score >= 1.5 × second_best (clear winner)
  - source_book + source_page match
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


def _tokens(t: str) -> set[str]:
    if not t:
        return set()
    t = unicodedata.normalize("NFKD", t).lower()
    return {w for w in re.findall(r"[a-z0-9çğıöşüâîû]{3,}", t)}


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _book_key(book: str) -> str:
    if not book:
        return ""
    f = _fold(book)
    f = re.sub(r"[_\-]+", " ", f)
    return re.sub(r"\s+", " ", f).strip()


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


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
    ap.add_argument("--threshold", type=float, default=0.60)
    ap.add_argument("--ratio", type=float, default=1.5, help="best/second_best ratio")
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index: (book_key, page) → list[(crop, token_set)]
    page_idx: dict[tuple[str, int], list[tuple[str, set]]] = defaultdict(list)
    with GEMINI_JSONL.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = d.get("book", "")
            page = d.get("page_num")
            crop = d.get("crop_file", "")
            text = d.get("soru_metni", "")
            if not (book and page is not None and crop):
                continue
            tokens = _tokens(text)
            if len(tokens) < 5:
                continue
            page_idx[(_book_key(book), int(page))].append((crop, tokens))
    print(f"[indexed] {len(page_idx):,} (book, page) groups\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    if args.audit:
        with eng.connect() as c:
            sample = c.execute(
                sa_text("""
                SELECT id::text, source_book, source_page, question_text,
                       pipeline_metadata::jsonb->'image_match_gemini_flash_v8'->>'matched_crop' AS v8_crop
                FROM question_bank
                WHERE pipeline_metadata::jsonb ? 'image_match_gemini_flash_v8'
                  AND source_page IS NOT NULL AND question_text IS NOT NULL
                ORDER BY RANDOM() LIMIT 500
            """)
            ).fetchall()
        stats = {"same": 0, "diff": 0, "no_match": 0, "ambiguous": 0}
        for r in sample:
            bk = _book_key(r.source_book or "")
            cands = page_idx.get((bk, int(r.source_page)), [])
            if not cands:
                stats["no_match"] += 1
                continue
            db_tokens = _tokens(r.question_text)
            if len(db_tokens) < 5:
                stats["no_match"] += 1
                continue
            scored = sorted(
                ((jaccard(db_tokens, t), c) for c, t in cands), reverse=True
            )
            best_s, best_c = scored[0]
            second_s = scored[1][0] if len(scored) > 1 else 0
            if best_s < args.threshold or (second_s and best_s < args.ratio * second_s):
                stats["ambiguous"] += 1
                continue
            if best_c == r.v8_crop:
                stats["same"] += 1
            else:
                stats["diff"] += 1
        ver = stats["same"] + stats["diff"]
        print("[audit]")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        if ver:
            print(f"\n[accuracy on verifiable={ver}]")
            print(
                f"  v14 == v8: {stats['same'] / ver * 100:.1f}% (threshold={args.threshold}, ratio={args.ratio})"
            )
        return

    print("[scan] NULL rows...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book, source_page, question_text, question_image_url
            FROM question_bank
            WHERE is_active=true
              AND source_book IS NOT NULL AND source_page IS NOT NULL
              AND question_text IS NOT NULL
        """)
        ).fetchall()

    # Compute used crops per (book, page)
    by_page_used: dict[tuple[str, int], set] = defaultdict(set)
    nulls_by_page: dict[tuple[str, int], list] = defaultdict(list)
    sb_orig: dict[tuple[str, int], str] = {}
    for r in rows:
        bk = _book_key(r.source_book)
        key = (bk, int(r.source_page))
        sb_orig[key] = r.source_book
        if not r.question_image_url:
            nulls_by_page[key].append((r.id, r.question_text))
        else:
            fname = r.question_image_url.split("/")[-1]
            if fname:
                by_page_used[key].add(fname)

    matches = []
    stats = {
        "matched": 0,
        "below_threshold": 0,
        "ambiguous_ratio": 0,
        "no_unused": 0,
        "no_jsonl": 0,
    }

    for key, null_list in nulls_by_page.items():
        cands = page_idx.get(key, [])
        if not cands:
            stats["no_jsonl"] += 1
            continue
        unused = [(c, t) for c, t in cands if c not in by_page_used[key]]
        if not unused:
            stats["no_unused"] += 1
            continue

        for null_id, qtext in null_list:
            db_tokens = _tokens(qtext)
            if len(db_tokens) < 5:
                stats["below_threshold"] += 1
                continue
            scored = sorted(
                ((jaccard(db_tokens, t), c) for c, t in unused), reverse=True
            )
            best_s, best_c = scored[0]
            second_s = scored[1][0] if len(scored) > 1 else 0
            if best_s < args.threshold:
                stats["below_threshold"] += 1
                continue
            if second_s and best_s < args.ratio * second_s:
                stats["ambiguous_ratio"] += 1
                continue
            disk_dir = find_disk_dir(sb_orig[key])
            if not disk_dir:
                continue
            crop_path = CROPS_BASE / disk_dir / best_c
            if not crop_path.exists():
                continue
            url = f"/static/crops/{disk_dir}/{best_c}"
            matches.append((null_id, url, sb_orig[key], key[1], best_c, best_s))
            stats["matched"] += 1

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[matches]: {len(matches):,}")
    if matches:
        print("\n[sample first 5]")
        for m in matches[:5]:
            print(f"  {m[0][:8]} {m[2][:30]} p{m[3]} jacc={m[5]:.2f} → {m[4]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, book, page, crop, score in batch:
                    c.execute(
                        sa_text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v14_jaccard}',
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
                                    "source": "v14_token_jaccard",
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                    "jaccard_score": round(score, 3),
                                }
                            ),
                        },
                    )
        print("[done]")
        with eng.connect() as c:
            null_n = c.execute(
                sa_text(
                    "SELECT COUNT(*) FROM question_bank WHERE is_active=true AND (question_image_url IS NULL OR question_image_url='')"
                )
            ).scalar()
            print(f"\nFINAL NULL: {null_n:,}")
    else:
        print("\n[dry-run]")


if __name__ == "__main__":
    main()
