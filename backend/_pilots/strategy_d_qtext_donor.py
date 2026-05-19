#!/usr/bin/env python3
"""
Strategy D: question_text donor lookup.

For each NULL row, find a WITH-image row with the SAME question_text
(normalized) AND same source_book. That's a deterministic "twin question"
match.

Safety:
  - Min text length 80 chars (avoid short generic stems)
  - same source_book (avoid cross-book false positives)
  - text must match after NFC + whitespace normalize
"""

import hashlib
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
    t = unicodedata.normalize("NFC", t)
    return re.sub(r"\s+", " ", t).strip().lower()


eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Build donor index: (book, hash) → URL
print("[scan] WITH-image donor pool...")
with eng.connect() as c:
    donors = c.execute(
        text("""
        SELECT id::text, source_book, question_text, question_image_url
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
          AND question_text IS NOT NULL
          AND LENGTH(question_text) >= 80
        """)
    ).fetchall()

donor_idx: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
for d in donors:
    if not d.source_book:
        continue
    normed = _norm(d.question_text)
    if len(normed) < 80:
        continue
    h = hashlib.sha256(normed.encode("utf-8")).hexdigest()[:16]
    book_key = _norm(d.source_book)
    donor_idx[(book_key, h)].append((d.id, d.question_image_url))
print(f"[index] {len(donor_idx):,} unique (book, text-hash) donor keys")

# Scan NULL rows
print("\n[scan] NULL rows...")
with eng.connect() as c:
    nulls = c.execute(
        text("""
        SELECT id::text, source_book, question_text
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND question_text IS NOT NULL
          AND LENGTH(question_text) >= 80
        """)
    ).fetchall()
print(f"[null] {len(nulls):,} candidate NULL rows")

matches = []
no_donor = 0
ambiguous_donor = 0

for r in nulls:
    if not r.source_book:
        no_donor += 1
        continue
    normed = _norm(r.question_text)
    if len(normed) < 80:
        no_donor += 1
        continue
    h = hashlib.sha256(normed.encode("utf-8")).hexdigest()[:16]
    book_key = _norm(r.source_book)
    cands = donor_idx.get((book_key, h), [])
    if not cands:
        no_donor += 1
        continue
    if len(cands) > 1:
        # Multiple donors with same text — check all point to same URL
        urls = {url for _, url in cands}
        if len(urls) == 1:
            matches.append((r.id, cands[0][1], cands[0][0]))
        else:
            ambiguous_donor += 1
            continue
    else:
        matches.append((r.id, cands[0][1], cands[0][0]))

print("[result]")
print(f"  matches:           {len(matches):,}")
print(f"  no_donor:          {no_donor:,}")
print(f"  ambiguous_donor:   {ambiguous_donor:,}")

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
                                '{image_match_strategy_d_qtext}',
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
                                "source": "strategy_d_qtext_donor_same_book",
                                "donor_id": donor,
                            }
                        ),
                    },
                )
        if (i // 500 + 1) % 10 == 0:
            print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")
    print("[done]")

with eng.connect() as c:
    null_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
            "AND (question_image_url IS NULL OR question_image_url='')"
        )
    ).scalar()
    print(f"\nFINAL NULL: {null_n:,}")
