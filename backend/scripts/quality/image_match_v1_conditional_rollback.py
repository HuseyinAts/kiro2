#!/usr/bin/env python3
"""Conditional rollback v1: keep only rows where URL q_no == DB ai_extras.q_no.

Sample audit revealed v1 has ~48% structural mismatch (URL q_no != DB q_no).
Tier 2+3 fallbacks (meta.json index, q_index_in_page) produced wrong matches.
"""

import json
import os
import re
import sys

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)


def parse_url_qno(url: str) -> int | None:
    m = re.search(r"_p\d+_q(\d+)\.", url or "")
    return int(m.group(1)) if m else None


with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT id::text, question_image_url, pipeline_metadata::text AS pm
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? 'image_match_metadata_v1'
          AND question_image_url IS NOT NULL
    """)
    ).fetchall()

print(f"[scan] {len(rows):,} v1 rows")

keep_ids, rollback_ids = [], []
for r in rows:
    try:
        pm = json.loads(r.pm) if r.pm else {}
    except json.JSONDecodeError:
        rollback_ids.append(r.id)
        continue

    ai = pm.get("ai_extras", {}) or {}
    db_qno = ai.get("q_no")
    url_qno = parse_url_qno(r.question_image_url)

    if db_qno is None or url_qno is None:
        rollback_ids.append(r.id)
        continue
    try:
        if int(str(db_qno).strip()) == url_qno:
            keep_ids.append(r.id)
        else:
            rollback_ids.append(r.id)
    except (ValueError, TypeError):
        rollback_ids.append(r.id)

print(f"[plan] keep={len(keep_ids):,}, rollback={len(rollback_ids):,}")

# Rollback
print("\n[rollback] NULL'a düşürülüyor...")
for i in range(0, len(rollback_ids), 1000):
    batch = rollback_ids[i : i + 1000]
    with eng.begin() as c:
        c.execute(
            text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        (pipeline_metadata::jsonb - 'image_match_metadata_v1'),
                        '{image_match_metadata_v1_rolled_back}',
                        CAST(:reason AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE id::text = ANY(:ids)
            """),
            {
                "reason": '{"date":"2026-05-19","reason":"URL q_no != DB ai_extras.q_no"}',
                "ids": batch,
            },
        )
    if (i // 1000 + 1) % 10 == 0:
        print(f"  batch {i // 1000 + 1}/{(len(rollback_ids) + 999) // 1000}")
print(f"[done] {len(rollback_ids):,} satır NULL'a döndü")

# Final state
with eng.connect() as c:
    null_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
            "AND (question_image_url IS NULL OR question_image_url='')"
        )
    ).scalar()
    has_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
            "AND question_image_url IS NOT NULL AND question_image_url != ''"
        )
    ).scalar()
    v1_kept = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank "
            "WHERE pipeline_metadata::jsonb ? 'image_match_metadata_v1'"
        )
    ).scalar()

print(f"\nFINAL: NULL={null_n:,}, HAS={has_n:,}, v1_kept={v1_kept:,}")
