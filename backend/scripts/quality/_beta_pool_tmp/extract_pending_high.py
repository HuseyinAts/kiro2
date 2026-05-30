"""Beta pool — 'high'-confidence pending segmentinden stratified pilot sample.

Bu sorular beta_pool_nuke_v1 ile toplu demote edilmiş ama pipeline confidence
'high' + DB cevap == best_answer. A-bias buggy pipeline'dan geldikleri için
bağımsız judge ile doğrulanmalı. SALT OKUNUR.
"""

from __future__ import annotations

import json
import os

import psycopg2

DSN = os.environ.get("KIRO2_DSN", "host=localhost port=5434 dbname=kiro2 user=postgres")
PER_SUBJECT = int(os.environ.get("PER_SUBJECT", "20"))
OUT = os.path.join(os.path.dirname(__file__), "pending_high_sample.jsonl")

QUERY = """
WITH ranked AS (
  SELECT id::text, subject_area, exam_type, difficulty_level::text AS difficulty_level,
         question_text, option_a, option_b, option_c, option_d, option_e,
         correct_answer, explanation,
         ROW_NUMBER() OVER (PARTITION BY subject_area ORDER BY md5(id::text)) AS rn
  FROM question_bank
  WHERE is_active = TRUE AND quality_review_status = 'pending'
    AND pipeline_metadata::jsonb->>'confidence_level' = 'high'
    AND question_text IS NOT NULL AND correct_answer IS NOT NULL
)
SELECT id, subject_area, exam_type, difficulty_level, question_text,
       option_a, option_b, option_c, option_d, option_e, correct_answer, explanation
FROM ranked WHERE rn <= %s
ORDER BY subject_area, id;
"""


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(QUERY, (PER_SUBJECT,))
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    by_subject: dict[str, int] = {}
    with open(OUT, "w", encoding="utf-8") as f:
        for row in rows:
            rec = dict(zip(cols, row))
            by_subject[rec["subject_area"]] = by_subject.get(rec["subject_area"], 0) + 1
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    cur.close()
    conn.close()
    print(f"Yazildi: {OUT}  ({len(rows)} soru)")
    for s, n in sorted(by_subject.items(), key=lambda x: -x[1]):
        print(f"  {s:14s} {n}")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
