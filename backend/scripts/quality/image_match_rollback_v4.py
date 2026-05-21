#!/usr/bin/env python3
"""ROLLBACK image_match_book_page_v4 — sample audit showed 98% mismatch.

`find_via_page_meta` brute-force scanned page candidates including
`answer_page` (cevap anahtarı sayfası, NOT soru sayfası) — yanlış crop'lar matched.
"""

import os
import sys

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
eng = create_engine(
    os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
)

with eng.begin() as c:
    pre = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE pipeline_metadata::jsonb ? 'image_match_book_page_v4'"
        )
    ).scalar()
    print(f"PRE: {pre:,} satır v4 işaretli")

    result = c.execute(
        text("""
        UPDATE question_bank
        SET question_image_url = NULL,
            pipeline_metadata = jsonb_set(
                (pipeline_metadata::jsonb - 'image_match_book_page_v4'),
                '{image_match_book_page_v4_rolled_back}',
                CAST(:reason AS jsonb),
                TRUE
            )::json,
            updated_at = NOW()
        WHERE pipeline_metadata::jsonb ? 'image_match_book_page_v4'
    """),
        {"reason": '{"date":"2026-05-19","reason":"sample audit mismatch"}'},
    )
    print(f"ROLLED BACK: {result.rowcount:,} satır")

with eng.connect() as c:
    null_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true AND (question_image_url IS NULL OR question_image_url='')"
        )
    ).scalar()
    has_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true AND question_image_url IS NOT NULL AND question_image_url != ''"
        )
    ).scalar()
    print(f"POST: NULL={null_n:,}, HAS={has_n:,}")
