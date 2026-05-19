#!/usr/bin/env python3
"""
Image match v7 — N-to-N text-based match.

For (book, page) groups where DB row count == disk crop count AND N>=2,
look up each DB question_text in JSONL → get truth qno → verify disk has that q
crop. This bypasses ordering ambiguity by using JSONL as ground truth.

Output of pilot_n_to_n_v2_text_match.py: 16 verified matches.
"""

import csv
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TSV_PATH = PROJECT_ROOT / "backend" / "_pilots" / "n_to_n_text_matches.tsv"

from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

matches = []
with TSV_PATH.open(encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        matches.append((row["id"], row["url"], row["book"], row["page"], row["qno"]))

print(f"[load] {len(matches):,} matches from {TSV_PATH.name}")

if not matches:
    sys.exit(0)

print(f"[apply] UPDATE {len(matches):,} satır...")
for i in range(0, len(matches), 100):
    batch = matches[i : i + 100]
    with eng.begin() as c:
        for qid, url, book, page, qno in batch:
            c.execute(
                text("""
                    UPDATE question_bank
                    SET question_image_url=:url,
                        pipeline_metadata = jsonb_set(
                            COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                            '{image_match_n_to_n_text_v7}',
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
                            "source": "v7_n_to_n_text_jsonl_verified",
                            "truth_page": int(page),
                            "truth_qno": int(qno),
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
