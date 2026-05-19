#!/usr/bin/env python3
"""
Strategy A: soru_hash collision recovery.

For each NULL row, check if another DB row with same soru_hash has image_url.
If yes, copy URL. Safety check: question_text must also match (defend against
hash collisions).
"""

import json
import os
import sys

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Step 1: For each NULL row, look up DONOR row with same soru_hash AND image
print("[scan] looking for NULL ↔ HAS-image collisions on soru_hash...")

with eng.connect() as c:
    rows = c.execute(
        text("""
        WITH nulls AS (
            SELECT id::text AS id, soru_hash, question_text
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND soru_hash IS NOT NULL
        ),
        donors AS (
            SELECT soru_hash, question_image_url, question_text, id::text AS donor_id
            FROM question_bank
            WHERE is_active=true
              AND question_image_url IS NOT NULL AND question_image_url <> ''
              AND soru_hash IS NOT NULL
        )
        SELECT n.id, n.soru_hash, n.question_text AS null_text,
               d.donor_id, d.question_image_url, d.question_text AS donor_text
        FROM nulls n
        JOIN donors d USING (soru_hash)
        """)
    ).fetchall()

print(f"[found] {len(rows):,} NULL↔donor pairs via soru_hash")

# Safety: question_text must match (whitespace normalize)
matches: list[tuple[str, str, str, str]] = []
hash_collision_skipped = 0
for r in rows:
    nt = " ".join((r.null_text or "").split())
    dt = " ".join((r.donor_text or "").split())
    if nt and dt and nt == dt:
        matches.append((r.id, r.question_image_url, r.donor_id, r.soru_hash))
    else:
        hash_collision_skipped += 1

print(f"[safe] {len(matches):,} text-verified matches")
print(f"[skip] {hash_collision_skipped:,} hash collisions (text differs)")

if matches:
    print("\n[sample first 3]")
    for qid, url, donor, h in matches[:3]:
        print(f"  null={qid[:8]} ← donor={donor[:8]} hash={h[:12]}... url={url[-50:]}")

    # Apply
    print(f"\n[apply] UPDATE {len(matches):,} satır...")
    for i in range(0, len(matches), 500):
        batch = matches[i : i + 500]
        with eng.begin() as c:
            for qid, url, donor, h in batch:
                c.execute(
                    text("""
                        UPDATE question_bank
                        SET question_image_url=:url,
                            pipeline_metadata = jsonb_set(
                                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                '{image_match_hash_collision_strategy_a}',
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
                                "source": "strategy_a_soru_hash_collision",
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
