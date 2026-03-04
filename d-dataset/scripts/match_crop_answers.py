#!/usr/bin/env python3
"""
Faz E: Answer matching for crop OCR results (page_inline only).

Matches OCR-extracted questions with answer keys from answers_v8.db (fallback: v7).
Uses ONLY the page_inline answer table for high-accuracy matching:
  - answers_page_inline: 78,720 answers keyed by (book, page, qnum)

REMOVED tiers (answers table DELETED in v8 — 39% accuracy, unusable):
  - Tier 2 (testno_exact): answers table REMOVED in v8
  - Tier 3 (unique_bookqnum): answers table REMOVED in v8
  - Tier 4 (same_answer): answers table REMOVED in v8
  - Tier 5b/5c/5d: answers table REMOVED in v8
  Root cause: answers table stored one answer per (book, qnum) but qnum resets
  per-section in soru bankasi books, causing massive collision (~39% accuracy).
  Decision: table removed entirely in v8 (March 2026).

Active matching tiers (A-grade, page_inline based):
  1.   Page-inline exact:     (book, page, soru_no) → answers_page_inline
  1B.  Position page-inline:  DB qnum = N-th question on page → answers_page_inline
  1.5  Page-inline unique:    (book, soru_no) where qnum on single page → answers_page_inline
  5a.  q_index page_inline:   (book, page, q_index) → answers_page_inline
  5a2. q_index PI unique:     (book, q_index) single-page → answers_page_inline

Tier 1B addresses the numbering scheme mismatch discovered in mikroskobik analiz:
  - 40.9% of (book,page) pairs have ZERO qnum overlap between DB and OCR
  - Root cause: page_inline DB uses per-page position numbering (1,2,3...)
    while OCR reads actual printed question numbers (12,13,14...)
  - Solution: map OCR soru_no to its position on the page, then look up DB by position
  - Simulation: +28,605 matches (+78.5% improvement)

Tier 1.5 bypasses the page mismatch problem (83.8% of unmatched questions) by
matching (book, qnum) when the qnum only appears on a single page in the DB.

Deduplication: Output is deduplicated by (book, page, qnum) key before writing.
YOLO multi-crop can produce duplicate records with identical answers.

Usage:
    python match_crop_answers.py                      # Full run
    python match_crop_answers.py --dry-run             # Stats only
    python match_crop_answers.py --input custom.jsonl   # Custom input

Input:
    output/ocr_crops/results_filtered.jsonl     (from Faz D)
    output/answer_keys_v8/answers_v8.db         (answer key database, v8: no 'answers' table)

Output:
    output/matched_v3/eslesmis_sorucevap_v3.jsonl     (matched questions)
    output/matched_v3/unmatched_v3.jsonl              (questions without answers)
    output/matched_v3/match_report.json                (statistics)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# PATHS
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
OCR_DIR = DATASET_DIR / "output" / "ocr_crops"
FILTERED_FILE = OCR_DIR / "results_filtered.jsonl"
DB_PATH = DATASET_DIR / "output" / "answer_keys_v8" / "answers_v8.db"
# v8: 'answers' table REMOVED (~39% accuracy, unusable).
# Only answers_page_inline remains (~85% accuracy).
# Fallback to v7 if v8 doesn't exist:
if not DB_PATH.exists():
    DB_PATH = DATASET_DIR / "output" / "answer_keys_v7" / "answers_v7.db"
OUTPUT_DIR = DATASET_DIR / "output" / "matched_v3"
MATCHED_FILE = OUTPUT_DIR / "eslesmis_sorucevap_v3.jsonl"
UNMATCHED_FILE = OUTPUT_DIR / "unmatched_v3.jsonl"
REPORT_FILE = OUTPUT_DIR / "match_report.json"


# ============================================================================
# HELPERS
# ============================================================================
def normalize_tr(text: str) -> str:
    """NFC + Turkish casefold for book name matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u0130", "i").replace("I", "\u0131")
    return text.lower().strip()


# ============================================================================
# ANSWER DB LOADING
# ============================================================================
def load_page_inline_answers(db: sqlite3.Connection) -> dict[tuple[str, int, int], dict]:
    """Load answers_page_inline: (norm_book, page, qnum) -> answer record.

    Returns 78,720 entries keyed by normalized book name.
    """
    lookup: dict[tuple[str, int, int], dict] = {}
    cur = db.cursor()
    cur.execute("""
        SELECT book_name, page_number, question_number, answer, confidence, source
        FROM answers_page_inline
    """)
    for row in cur.fetchall():
        book_name, page, qnum, answer, conf, source = row
        key = (normalize_tr(book_name), int(page), int(qnum))
        lookup[key] = {
            "answer": answer,
            # Use DB confidence when available; default 0.0 = "unmeasured" (not "high")
            # Actual accuracy will be measured via human GT (measure_tier_accuracy.py)
            "confidence": conf if conf and conf > 0 else 0.0,
            "source": source or "page_inline",
            "db_book": book_name,
        }
    return lookup


def load_page_inline_unique(db: sqlite3.Connection) -> dict[tuple[str, int], dict]:
    """Load (book, qnum) pairs from answers_page_inline where qnum appears on exactly one page.

    Bypasses page mismatch: if a qnum is on only one page in the DB,
    we can match by (book, qnum) alone without requiring page match.

    WARNING: 17.2% pilot accuracy (below random). DISABLED by default.
    """
    lookup: dict[tuple[str, int], dict] = {}
    cur = db.cursor()
    cur.execute("""
        SELECT book_name, question_number,
               MIN(answer) AS answer, MIN(confidence) AS confidence, MIN(source) AS source
        FROM answers_page_inline
        WHERE (book_name, question_number) IN (
            SELECT book_name, question_number
            FROM answers_page_inline
            GROUP BY book_name, question_number
            HAVING COUNT(DISTINCT page_number) = 1
        )
        GROUP BY book_name, question_number
    """)
    for row in cur.fetchall():
        book_name, qnum, answer, conf, source = row
        key = (normalize_tr(book_name), int(qnum))
        lookup[key] = {
            "answer": answer,
            "confidence": conf if conf and conf > 0 else 0.0,
            "source": source or "page_inline_unique",
            "db_book": book_name,
        }
    return lookup


def load_testno_answers(db: sqlite3.Connection) -> dict[tuple[str, int, int], dict]:
    """Load answers: (norm_book, test_no, qnum) -> answer record.

    DEPRECATED in v8: 'answers' table REMOVED (~39% accuracy).
    Kept for backward compatibility with v7 databases.
    Returns empty dict if 'answers' table doesn't exist.
    """
    lookup: dict[tuple[str, int, int], dict] = {}
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT book_name, test_number, question_number, answer, confidence, source
            FROM answers
        """)
    except sqlite3.OperationalError:
        return lookup  # v8: answers table doesn't exist
    for row in cur.fetchall():
        book_name, test_no, qnum, answer, conf, source = row
        key = (normalize_tr(book_name), int(test_no or 0), int(qnum))
        lookup[key] = {
            "answer": answer,
            "confidence": conf or 0.8,
            "source": source or "answer_key",
            "db_book": book_name,
        }
    return lookup


def load_unique_bookqnum(db: sqlite3.Connection) -> dict[tuple[str, int], dict]:
    """Load (book, qnum) pairs that have exactly one answer (no collision).

    DEPRECATED in v8: 'answers' table REMOVED.
    Returns empty dict if 'answers' table doesn't exist.
    """
    lookup: dict[tuple[str, int], dict] = {}
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT book_name, question_number, answer, confidence, source
            FROM answers
            WHERE (book_name, question_number) IN (
                SELECT book_name, question_number
                FROM answers
                GROUP BY book_name, question_number
                HAVING COUNT(DISTINCT test_number) = 1
            )
        """)
    except sqlite3.OperationalError:
        return lookup  # v8: answers table doesn't exist
    for row in cur.fetchall():
        book_name, qnum, answer, conf, source = row
        key = (normalize_tr(book_name), int(qnum))
        lookup[key] = {
            "answer": answer,
            "confidence": conf or 0.8,
            "source": source or "answer_key_unique",
            "db_book": book_name,
        }
    return lookup


def load_same_answer_collisions(db: sqlite3.Connection) -> dict[tuple[str, int], dict]:
    """Load (book, qnum) pairs that collide but all have same answer.

    DEPRECATED in v8: 'answers' table REMOVED.
    Returns empty dict if 'answers' table doesn't exist.
    """
    lookup: dict[tuple[str, int], dict] = {}
    cur = db.cursor()
    try:
        cur.execute("""
        SELECT book_name, question_number, answer, MIN(confidence), MIN(source)
        FROM answers
        WHERE (book_name, question_number) IN (
            SELECT book_name, question_number
            FROM answers
            GROUP BY book_name, question_number
            HAVING COUNT(DISTINCT test_number) > 1 AND COUNT(DISTINCT answer) = 1
        )
        GROUP BY book_name, question_number
    """)
    except sqlite3.OperationalError:
        return lookup  # v8: answers table doesn't exist
    for row in cur.fetchall():
        book_name, qnum, answer, conf, source = row
        key = (normalize_tr(book_name), int(qnum))
        lookup[key] = {
            "answer": answer,
            "confidence": (conf or 0.7) * 0.9,  # Slight confidence discount
            "source": "same_answer_collision",
            "db_book": book_name,
        }
    return lookup


# ============================================================================
# PRODUCTION FORMAT
# ============================================================================
def to_production_format(rec: dict, answer_info: dict, match_tier: str) -> dict:
    """Convert OCR record + answer to production JSONL format.

    Compatible with existing eslesmis_sorucevap.jsonl schema.
    """
    return {
        "book_name": rec.get("book", ""),
        "page_number": rec.get("page_num", 0),
        "question_number": rec.get("soru_no") or rec.get("question_index", 0),
        "question_index": rec.get("question_index", 0),
        "question_text": rec.get("soru_metni", ""),
        "options": rec.get("secenekler", {}),
        "answer": answer_info.get("answer", ""),
        "answer_confidence": answer_info.get("confidence", 0),
        "answer_source": answer_info.get("source", ""),
        "match_tier": match_tier,
        "test_number": rec.get("test_no", 0),
        "crop_file": rec.get("crop_file", ""),
        "det_confidence": rec.get("det_confidence", 0),
    }


# ============================================================================
# MAIN MATCHING LOGIC
# ============================================================================
def prescan_page_soru_nos(input_file: Path) -> dict[tuple[str, int], list[int]]:
    """Pre-scan input to build sorted soru_no lists per (book, page).

    Required for Tier 1B position matching: maps OCR soru_no to its
    ordinal position on the page (1-indexed), then looks up DB by position.

    Returns: {(norm_book, page_num): [sorted unique soru_nos]}
    """
    page_snos: dict[tuple[str, int], set[int]] = defaultdict(set)
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = normalize_tr(rec.get("book", ""))
            page = rec.get("page_num", 0)
            sno_raw = rec.get("soru_no")
            sno = int(sno_raw) if sno_raw is not None and str(sno_raw).isdigit() else None
            if sno and sno > 0:
                page_snos[(book, page)].add(sno)
    # Convert to sorted lists
    return {k: sorted(v) for k, v in page_snos.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer matching (page_inline only)")
    parser.add_argument("--input", type=str, help="Custom filtered JSONL")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--include-tier1-5", action="store_true",
        help="Include tier1_5 (page_inline_unique) matching. DISABLED by default: "
             "17.2%% pilot accuracy (below 20%% random baseline). "
             "Enable only for coverage analysis, not for production GT.",
    )
    args = parser.parse_args()

    input_file = Path(args.input) if args.input else FILTERED_FILE

    print("=" * 60)
    print("Faz E: 4-Tier Answer Matching (page_inline only)")
    print("=" * 60)
    print(f"Input      : {input_file}")
    print(f"DB         : {DB_PATH}")
    print(f"Output     : {MATCHED_FILE}")
    print(f"Dry run    : {args.dry_run}")
    print(f"Tier 1.5   : {'ENABLED (--include-tier1-5)' if args.include_tier1_5 else 'DISABLED (17.2% accuracy < 20% random)'}")
    print()

    if not input_file.exists():
        print(f"ERROR: Input not found: {input_file}")
        sys.exit(1)
    if not DB_PATH.exists():
        print(f"ERROR: DB not found: {DB_PATH}")
        sys.exit(1)

    # Load answer databases
    db = sqlite3.connect(str(DB_PATH))
    print("Loading answer databases...")

    page_inline = load_page_inline_answers(db)
    print(f"  page_inline: {len(page_inline):,} entries")

    if args.include_tier1_5:
        page_inline_uniq = load_page_inline_unique(db)
        print(f"  page_inline_unique: {len(page_inline_uniq):,} entries")
    else:
        page_inline_uniq = {}
        print("  page_inline_unique: SKIPPED (--include-tier1-5 not set)")

    # F-grade DB lookups DISABLED — answers table ~22% accuracy (per-section qnum collision)
    # testno_answers = load_testno_answers(db)
    # unique_bq = load_unique_bookqnum(db)
    # same_ans = load_same_answer_collisions(db)

    db.close()
    print()

    # Pre-scan: build page-level soru_no sorted lists for Tier 1B
    print("Pre-scanning for Tier 1B position matching...")
    page_soru_sorted = prescan_page_soru_nos(input_file)
    print(f"  Pages with soru_nos: {len(page_soru_sorted):,}")
    print()

    # Process questions
    total = 0
    matched = 0
    unmatched_count = 0
    dedup_count = 0
    tier_counts: Counter = Counter()
    answer_dist: Counter = Counter()
    book_match_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"matched": 0, "unmatched": 0})
    seen_keys: set[tuple[str, int, int]] = set()

    matched_f = None
    unmatched_f = None
    if not args.dry_run:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        matched_f = open(MATCHED_FILE, "w", encoding="utf-8")
        unmatched_f = open(UNMATCHED_FILE, "w", encoding="utf-8")

    try:
        with open(input_file, encoding="utf-8") as in_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total += 1
                book = rec.get("book", "")
                norm_book = normalize_tr(book)
                page_num = rec.get("page_num", 0)
                soru_no_raw = rec.get("soru_no")  # Can be None, int, or str
                soru_no = int(soru_no_raw) if soru_no_raw is not None and str(soru_no_raw).isdigit() else None
                q_index = int(rec.get("question_index", 0) or 0)
                test_no = int(rec.get("test_no", 0) or 0)

                answer_info = None
                match_tier = None

                # Tier 1: Page-inline exact (book, page, soru_no)
                if soru_no and soru_no > 0:
                    key1 = (norm_book, page_num, soru_no)
                    if key1 in page_inline:
                        answer_info = page_inline[key1]
                        match_tier = "tier1_page_inline"

                # Tier 1B: Position-based page-inline matching
                # Root cause: ~41% of pages use per-page position numbering in DB
                # (qnum=1,2,3...) while OCR reads actual printed numbers (12,13,14...).
                # Solution: find this soru_no's ordinal position on the page, then
                # look up the DB answer by that position.
                if not answer_info and soru_no and soru_no > 0:
                    page_key = (norm_book, page_num)
                    sorted_snos = page_soru_sorted.get(page_key)
                    if sorted_snos and soru_no in sorted_snos:
                        position = sorted_snos.index(soru_no) + 1  # 1-indexed
                        if position != soru_no:  # Skip if position == soru_no (already tried in Tier 1)
                            key1b = (norm_book, page_num, position)
                            if key1b in page_inline:
                                answer_info = page_inline[key1b]
                                match_tier = "tier1b_position_page_inline"

                # Tier 1.5: Page-inline unique (book, soru_no) — bypasses page mismatch
                # DISABLED by default: 17.2% pilot accuracy (below 20% random baseline).
                # Root cause: page mismatch bypass introduces wrong-page answer contamination.
                # Enable with --include-tier1-5 only for coverage analysis.
                if args.include_tier1_5 and not answer_info and soru_no and soru_no > 0:
                    key15 = (norm_book, soru_no)
                    if key15 in page_inline_uniq:
                        answer_info = page_inline_uniq[key15]
                        match_tier = "tier1_5_page_inline_unique"

                # Tier 2: DISABLED — 19.6% accuracy (answers table per-section qnum collision)
                # if not answer_info and soru_no and soru_no > 0 and test_no and test_no > 0:
                #     key2 = (norm_book, test_no, soru_no)
                #     if key2 in testno_answers:
                #         answer_info = testno_answers[key2]
                #         match_tier = "tier2_testno_exact"

                # Tier 3: DISABLED — 23.4% accuracy (per-section qnum collision)
                # if not answer_info and soru_no and soru_no > 0:
                #     key3 = (norm_book, soru_no)
                #     if key3 in unique_bq:
                #         answer_info = unique_bq[key3]
                #         match_tier = "tier3_unique_bookqnum"

                # Tier 4: DISABLED — 21.5% accuracy (same-answer collision structurally broken)
                # if not answer_info and soru_no and soru_no > 0:
                #     key4 = (norm_book, soru_no)
                #     if key4 in same_ans:
                #         answer_info = same_ans[key4]
                #         match_tier = "tier4_same_answer"

                # Tier 5 (fallback): question_index when soru_no is null or 0
                # Handles K3 bug: soru_no=null causes all tiers to skip
                # CRITICAL: Only use q_index when soru_no is truly absent —
                # if soru_no exists but DB lookup failed, do NOT fall back to q_index
                if not answer_info and (not soru_no or soru_no <= 0) and q_index and q_index > 0:
                    # 5a: page_inline with question_index
                    key5a = (norm_book, page_num, q_index)
                    if key5a in page_inline:
                        answer_info = page_inline[key5a]
                        match_tier = "tier5_qindex_page_inline"
                    # 5a2: page_inline_unique with question_index
                    if not answer_info:
                        key5a2 = (norm_book, q_index)
                        if key5a2 in page_inline_uniq:
                            answer_info = page_inline_uniq[key5a2]
                            match_tier = "tier5_qindex_page_inline_unique"
                    # 5b: DISABLED — 21.7% accuracy (answers table)
                    # if not answer_info and test_no and test_no > 0:
                    #     key5b = (norm_book, test_no, q_index)
                    #     if key5b in testno_answers:
                    #         answer_info = testno_answers[key5b]
                    #         match_tier = "tier5_qindex_testno"
                    # 5c: DISABLED — 19.7% accuracy (answers table)
                    # if not answer_info:
                    #     key5c = (norm_book, q_index)
                    #     if key5c in unique_bq:
                    #         answer_info = unique_bq[key5c]
                    #         match_tier = "tier5_qindex_unique"
                    # 5d: DISABLED — 25.9% accuracy (answers table)
                    # if not answer_info:
                    #     key5d = (norm_book, q_index)
                    #     if key5d in same_ans:
                    #         answer_info = same_ans[key5d]
                    #         match_tier = "tier5_qindex_same_answer"

                if answer_info:
                    # Dedup by (book, page, qnum) — YOLO multi-crop produces duplicates
                    prod = to_production_format(rec, answer_info, match_tier)
                    dedup_key = (prod["book_name"], prod["page_number"], prod["question_number"])
                    if dedup_key in seen_keys:
                        dedup_count += 1
                        continue
                    seen_keys.add(dedup_key)

                    matched += 1
                    tier_counts[match_tier] += 1
                    answer_dist[answer_info["answer"]] += 1
                    book_match_stats[book]["matched"] += 1

                    if matched_f:
                        matched_f.write(json.dumps(prod, ensure_ascii=False) + "\n")
                else:
                    unmatched_count += 1
                    book_match_stats[book]["unmatched"] += 1

                    if unmatched_f:
                        rec["match_status"] = "unmatched"
                        unmatched_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

                if total % 50000 == 0:
                    print(f"  [{total:,}] matched={matched:,} unmatched={unmatched_count:,}")

    finally:
        if matched_f:
            matched_f.close()
        if unmatched_f:
            unmatched_f.close()

    # Print report
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total input     : {total:,}")
    print(f"Matched         : {matched:,} ({matched / total * 100:.1f}%)" if total > 0 else "")
    print(f"Unmatched       : {unmatched_count:,} ({unmatched_count / total * 100:.1f}%)" if total > 0 else "")
    print(f"Dedup skipped   : {dedup_count:,}")
    print()

    print("Match tier breakdown:")
    for tier, count in tier_counts.most_common():
        pct = count / matched * 100 if matched > 0 else 0
        print(f"  {tier}: {count:,} ({pct:.1f}%)")
    print()

    print("Answer distribution:")
    total_answers = sum(answer_dist.values())
    for ans in sorted(answer_dist.keys()):
        count = answer_dist[ans]
        pct = count / total_answers * 100 if total_answers > 0 else 0
        print(f"  {ans}: {count:,} ({pct:.1f}%)")
    print()

    # Chi-square test (5-option uniform)
    chi_sq = None
    if total_answers > 0:
        expected = total_answers / 5
        chi_sq = sum((answer_dist.get(a, 0) - expected) ** 2 / expected for a in "ABCDE")
        print(f"Chi-square (uniform 5): {chi_sq:.2f} (threshold: 9.49)")
        if chi_sq < 9.49:
            print("  PASS: Answer distribution is uniform")
        else:
            print("  WARNING: Non-uniform answer distribution")
    print()

    # Book-level stats
    books_with_matches = sum(1 for b in book_match_stats if book_match_stats[b]["matched"] > 0)
    books_no_matches = sum(1 for b in book_match_stats if book_match_stats[b]["matched"] == 0)
    print(f"Books with matches: {books_with_matches}")
    print(f"Books without matches: {books_no_matches}")

    # Top unmatched books
    unmatched_books = sorted(
        [(b, s["unmatched"]) for b, s in book_match_stats.items() if s["unmatched"] > 0],
        key=lambda x: -x[1],
    )
    if unmatched_books:
        print("\nTop 10 unmatched books:")
        for book, cnt in unmatched_books[:10]:
            total_book = book_match_stats[book]["matched"] + cnt
            print(f"  {book[:50]}: {cnt:,}/{total_book:,} unmatched")

    # Write report
    report = {
        "total_input": total,
        "matched": matched,
        "unmatched": unmatched_count,
        "dedup_skipped": dedup_count,
        "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        "tier_breakdown": dict(tier_counts.most_common()),
        "answer_distribution": dict(sorted(answer_dist.items())),
        "chi_square": round(chi_sq, 2) if chi_sq is not None else None,
        "books_with_matches": books_with_matches,
        "books_without_matches": books_no_matches,
    }
    if not args.dry_run:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport: {REPORT_FILE}")
        print(f"Matched: {MATCHED_FILE}")
        print(f"Unmatched: {UNMATCHED_FILE}")


if __name__ == "__main__":
    main()
