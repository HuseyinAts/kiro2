#!/usr/bin/env python3
"""Test 3 currently-pending Phase 7 questions via OpenAI to see fail reason."""

import os
import sys
import time
from pathlib import Path

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "quality"))
os.environ["LLM_PROVIDER"] = "openai"
from metadata_phase7_llm_generation import openai_generate, PROMPT_TEMPLATE  # noqa

conn = psycopg2.connect("postgresql://postgres:1470@localhost:5434/kiro2")
cur = conn.cursor()
cur.execute(
    """
SELECT q.id::text, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
       q.correct_answer, q.subject_area, q.exam_type, q.difficulty_level::text, q.bloom_category
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
  AND r.question_id IS NULL LIMIT 3
"""
)
rows = cur.fetchall()
conn.close()

for i, row in enumerate(rows):
    qid, qt, oa, ob, oc, od, oe, ca, subj, exam, diff, bloom = row
    prompt = PROMPT_TEMPLATE.format(
        subject_area=subj,
        exam_type=exam,
        difficulty_level=diff,
        bloom_category=bloom,
        question_text=qt[:1000],
        option_a=oa[:300],
        option_b=ob[:300],
        option_c=oc[:300],
        option_d=(od or "")[:300],
        option_e=(oe or "")[:300],
        correct_answer=ca,
    )
    try:
        t0 = time.time()
        raw = openai_generate(prompt, timeout=30)
        dt = (time.time() - t0) * 1000
        print(f"[{i + 1}/3] {qid[:8]} {subj:10s} dt={dt:.0f}ms ok=YES len={len(raw)}")
        print(f"       first 200: {raw[:200]}")
    except Exception as e:
        print(
            f"[{i + 1}/3] {qid[:8]} {subj:10s} ERROR: {type(e).__name__}: {str(e)[:300]}"
        )
