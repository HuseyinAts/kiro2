#!/usr/bin/env python3
"""
Strategy B: image_ocr_text-based donor lookup.

For NULL rows with image_ocr_text populated, find WITH-image rows that share
the same OCR text. Copy donor URL.

Safety: text normalize + length minimum + same source_book.
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"\s+", " ", t).strip()


eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

print("[scan] NULL rows with image_ocr_text...")
with eng.connect() as c:
    null_rows = c.execute(
        text("""
        SELECT id::text, source_book, image_ocr_text, question_text
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND image_ocr_text IS NOT NULL
          AND LENGTH(image_ocr_text) >= 50
        """)
    ).fetchall()
print(f"[null] {len(null_rows):,} rows with image_ocr_text >=50 chars")

print("[scan] WITH-image rows with image_ocr_text or question_text donor pool...")
with eng.connect() as c:
    donors = c.execute(
        text("""
        SELECT id::text, source_book, image_ocr_text, question_text, question_image_url
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
          AND (image_ocr_text IS NOT NULL OR question_text IS NOT NULL)
        """)
    ).fetchall()
print(f"[donors] {len(donors):,} candidate donors")

# Build donor index by normalized text key (image_ocr_text first, fallback question_text)
donor_idx: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
for d in donors:
    keys = []
    if d.image_ocr_text:
        keys.append(_norm(d.image_ocr_text))
    if d.question_text:
        keys.append(_norm(d.question_text))
    for k in keys:
        if len(k) >= 50:
            donor_idx[k].append((d.id, d.question_image_url, d.source_book or ""))

print(f"[index] {len(donor_idx):,} unique donor text keys\n")

matches = []
no_donor = 0
book_mismatch = 0

for r in null_rows:
    null_key = _norm(r.image_ocr_text)
    if len(null_key) < 50:
        no_donor += 1
        continue
    donor_list = donor_idx.get(null_key, [])
    if not donor_list:
        # Try with question_text
        if r.question_text:
            null_key2 = _norm(r.question_text)
            if len(null_key2) >= 50:
                donor_list = donor_idx.get(null_key2, [])
    if not donor_list:
        no_donor += 1
        continue

    # Prefer same source_book
    chosen = None
    nb = (r.source_book or "").strip().lower()
    for did, url, dbook in donor_list:
        if dbook.strip().lower() == nb:
            chosen = (did, url)
            break
    if not chosen and donor_list:
        # cross-book accept if only one candidate
        if len({(d, u, b) for d, u, b in donor_list}) == 1:
            chosen = (donor_list[0][0], donor_list[0][1])
        else:
            book_mismatch += 1
            continue

    if chosen:
        matches.append((r.id, chosen[1], chosen[0]))

print("[result]")
print(f"  matches:        {len(matches):,}")
print(f"  no_donor_text:  {no_donor:,}")
print(f"  book_mismatch:  {book_mismatch:,}")

if matches:
    print("\n[sample first 3]")
    for qid, url, donor in matches[:3]:
        print(f"  null={qid[:8]} ← donor={donor[:8]} url={url[-50:]}")

    print(f"\n[apply] UPDATE {len(matches):,} satır...")
    for i in range(0, len(matches), 500):
        batch = matches[i : i + 500]
        with eng.begin() as c:
            for qid, url, donor in batch:
                c.execute(
                    text("""
                        UPDATE question_bank
                        SET question_image_url=:url,
                            pipeline_metadata = jsonb_set(
                                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                '{image_match_strategy_b_image_ocr}',
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
                                "source": "strategy_b_image_ocr_text",
                                "donor_id": donor,
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
