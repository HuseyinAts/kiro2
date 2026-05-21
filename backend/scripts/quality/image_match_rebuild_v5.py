#!/usr/bin/env python3
"""
Image match v5 (REBUILD) — JSONL-authoritative match for ALL NULL rows.

Root cause of v1/v4 mismatches:
  - ai_extras.q_no is Gemini's free-text label ("Soru: 2", "BIRLIKTE ÇÖZELIM")
  - q_index_in_page semantics vary per page_type
  - Both unreliable as page-index proxy

Reliable signal: JSONL eslesmis_sorucevap.jsonl
  - text (question content) is GROUND TRUTH
  - question_number = page index (matches disk qNN)
  - book_name + page_number + question_number → deterministic disk filename

Strategy:
  1. Build JSONL index by NORMALIZED text → (book, page, qno)
  2. For each NULL question, lookup by exact-norm hash
  3. If hash miss, try LOOSE prefix (first 80 normalized chars)
  4. If both miss, skip (cannot verify)
  5. Apply only with verified disk file existence

NO ai_extras dependency. JSONL is the single source of truth.
"""

from __future__ import annotations

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
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"

PREFIX_LEN = 80


def _norm_exact(text: str) -> str:
    """Exact normalize: NFC + whitespace collapse + lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _norm_loose(text: str) -> str:
    """Loose normalize: NFKD + strip non-alphanumeric."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9çğıöşüâîû]", "", text)
    return text


def _fold(s: str) -> str:
    tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return s.translate(tr_map).lower()


_DISK_DIRS: list[str] | None = None
_BOOK_CACHE: dict[str, str] = {}


def find_disk_dir(book: str) -> str | None:
    global _DISK_DIRS
    if not book:
        return None
    if book in _BOOK_CACHE:
        return _BOOK_CACHE[book] or None
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    for variant in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if variant in _DISK_DIRS:
            _BOOK_CACHE[book] = variant
            return variant
    folded = _fold(book.replace(" ", "_"))
    for d in _DISK_DIRS:
        if _fold(d) == folded:
            _BOOK_CACHE[book] = d
            return d
    db_tokens = set(_fold(book).split()) - {"soru", "bankası", "bankasi"}
    if len(db_tokens) >= 3:
        best, best_score = None, 0
        for d in _DISK_DIRS:
            d_tokens = set(_fold(d.replace("_", " ")).split()) - {
                "soru",
                "bankası",
                "bankasi",
            }
            common = db_tokens & d_tokens
            if len(common) > best_score:
                best, best_score = d, len(common)
        if best_score >= max(3, len(db_tokens) - 1):
            _BOOK_CACHE[book] = best
            return best
    _BOOK_CACHE[book] = ""
    return None


def find_crop_disk(book: str, page: int, qno: int) -> str | None:
    book_dir = find_disk_dir(book)
    if not book_dir:
        return None
    dir_path = CROPS_BASE / book_dir
    if not dir_path.exists():
        return None
    page_str = f"{page:04d}"
    for q_str in (f"q{qno:02d}", f"q{qno}"):
        for ext in (".png", ".jpg"):
            fname = f"{book_dir}_p{page_str}_{q_str}{ext}"
            if (dir_path / fname).exists():
                return f"/static/crops/{book_dir}/{fname}"
    return None


def build_jsonl_indices():
    """Build TWO indices: exact hash + loose prefix."""
    exact_idx: dict[str, tuple[str, int, int]] = {}
    prefix_idx: defaultdict[str, list[tuple[str, int, int]]] = defaultdict(list)

    print("[load] JSONL...")
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = d.get("text") or ""
            book = d.get("book_name", "")
            page = d.get("page_number")
            qno = d.get("question_number")
            if not (text and book and page and qno):
                continue

            # Exact hash
            normed_exact = _norm_exact(text)
            h = hashlib.sha256(normed_exact.encode("utf-8")).hexdigest()[:16]
            if h not in exact_idx:
                exact_idx[h] = (book, int(page), int(qno))

            # Loose prefix
            normed_loose = _norm_loose(text)
            if len(normed_loose) >= PREFIX_LEN:
                prefix_idx[normed_loose[:PREFIX_LEN]].append(
                    (book, int(page), int(qno))
                )

    print(f"[done] exact={len(exact_idx):,}, prefix={len(prefix_idx):,}")
    return exact_idx, prefix_idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    exact_idx, prefix_idx = build_jsonl_indices()

    limit = f"LIMIT {args.pilot}" if args.pilot else ""
    with eng.connect() as c:
        rows = c.execute(
            text(
                f"SELECT id::text, source_book, question_text FROM question_bank "
                f"WHERE is_active=true "
                f"AND (question_image_url IS NULL OR question_image_url='') "
                f"AND question_text IS NOT NULL "
                f"{limit}"
            )
        ).fetchall()

    print(f"\n[scan] {len(rows):,} NULL rows")

    matches = []
    via_exact, via_prefix, no_jsonl, no_disk = 0, 0, 0, 0

    for r in rows:
        normed_exact = _norm_exact(r.question_text)
        h = hashlib.sha256(normed_exact.encode("utf-8")).hexdigest()[:16]
        truth = exact_idx.get(h)

        if not truth:
            normed_loose = _norm_loose(r.question_text)
            if len(normed_loose) >= PREFIX_LEN:
                cands = prefix_idx.get(normed_loose[:PREFIX_LEN], [])
                if cands:
                    if r.source_book:
                        sb_folded = _fold(r.source_book)
                        for tb, tp, tq in cands:
                            if _fold(tb) == sb_folded:
                                truth = (tb, tp, tq)
                                break
                    if not truth:
                        truth = cands[0]
                    if truth:
                        via_prefix += 1
            if not truth:
                no_jsonl += 1
                continue
        else:
            via_exact += 1

        url = find_crop_disk(*truth)
        if url:
            matches.append((r.id, url, truth))
        else:
            no_disk += 1

    print("\n[result]")
    print(f"  via_exact_hash:  {via_exact:,}")
    print(f"  via_loose_prefix: {via_prefix:,}")
    print(f"  no_jsonl:        {no_jsonl:,}")
    print(f"  no_disk:         {no_disk:,}")
    print(f"  total_to_apply:  {len(matches):,}")

    if args.apply and matches:
        print(f"\n[apply] {len(matches):,} satır UPDATE...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, truth in batch:
                    c.execute(
                        text(
                            "UPDATE question_bank SET question_image_url=:url, "
                            "pipeline_metadata = jsonb_set("
                            "  COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb), "
                            "  '{image_match_rebuild_v5}', "
                            "  CAST(:audit AS jsonb), "
                            "  TRUE"
                            ")::json, "
                            "updated_at=NOW() "
                            "WHERE id::text=:qid"
                        ),
                        {
                            "url": url,
                            "qid": qid,
                            "audit": json.dumps(
                                {
                                    "date": "2026-05-19",
                                    "source": "v5_jsonl_authoritative",
                                    "truth_book": truth[0],
                                    "truth_page": truth[1],
                                    "truth_qno": truth[2],
                                }
                            ),
                        },
                    )
            if (i // 500 + 1) % 10 == 0:
                print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
