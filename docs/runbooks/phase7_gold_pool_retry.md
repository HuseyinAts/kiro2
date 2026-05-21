# Phase 7 Gold Pool Rationale Generation Runbook

**Status**: Script ready, NOT executed. Operator must run.
**Audit reference**: `docs/audits/2026-05-22_product_ready_audit/05_data_quality.md` §Phase 7
**Estimated cost**: ~$300 (15,321 questions × ~$0.0023 Gemini Flash Batch API)
**Estimated wall time**: 24h (Gemini batch async)

## Problem statement

Live PostgreSQL 5434/kiro2 shows:
- `auto_judged_high` (Gold pool, beta-ready): **15,321 questions / 0 rationales (0%)**
- `bronze_clean` (Curator queue): **197 questions / 0 rationales (0%)**
- Total beta-eligible questions lacking rationale: **15,518**

Pre-fix `metadata_phase7_batch_gemini.py` filter was `beta_filter_v1.rule = 'R4_rule_based_gold'`, which excluded R1-restored gold questions added in session 178. Filter now targets `quality_review_status IN ('auto_judged_high', 'bronze_clean')` directly.

## Pre-flight checks

```bash
# 1. Confirm GEMINI_API_KEY is set
echo "GEMINI_API_KEY length: ${#GEMINI_API_KEY}"  # Should be >40 chars

# 2. Verify DATABASE_URL points to live PG 5434
echo "$DATABASE_URL"  # Should contain :5434/kiro2

# 3. Dry-run count what would be queued
PGPASSWORD=postgres psql -p 5434 -U postgres -d kiro2 -c "
SELECT COUNT(*) FROM question_bank q
LEFT JOIN question_option_rationales r
  ON r.question_id = q.id::text AND r.option_letter = 'A'
WHERE q.is_active AND q.question_text IS NOT NULL
  AND q.option_a IS NOT NULL
  AND q.correct_answer IN ('A','B','C','D','E')
  AND r.question_id IS NULL
  AND q.quality_review_status IN ('auto_judged_high', 'bronze_clean');"
# Expected: 15,518 (or close)
```

## Execution (operator-run)

```bash
cd C:/Users/husey/kiro2/backend

# Sub-command flow:
# build → submit → poll (loop) → apply

# 1. Build JSONL files (auto-split if > 30K rows)
python scripts/quality/metadata_phase7_batch_gemini.py build --limit 20000
# Output: scripts/quality/phase7_batch_*.jsonl

# 2. Submit to Gemini Batch API (returns job IDs)
python scripts/quality/metadata_phase7_batch_gemini.py submit
# Saves: scripts/quality/phase7_batch_jobs.json

# 3. Poll for completion (every ~30min, may take 24h)
while ! python scripts/quality/metadata_phase7_batch_gemini.py poll; do
  sleep 1800
done

# 4. Apply results — downloads outputs, INSERTs into question_option_rationales
python scripts/quality/metadata_phase7_batch_gemini.py apply
```

## Validation after apply

```bash
PGPASSWORD=postgres psql -p 5434 -U postgres -d kiro2 -c "
SELECT q.quality_review_status,
       COUNT(DISTINCT q.id) AS questions,
       COUNT(DISTINCT r.question_id) AS w_rationale,
       ROUND(100.0 * COUNT(DISTINCT r.question_id) / COUNT(DISTINCT q.id), 1) AS coverage_pct
FROM question_bank q
LEFT JOIN question_option_rationales r ON r.question_id = q.id::text
WHERE q.is_active
GROUP BY 1 ORDER BY 1;"
# Expected after apply:
#   auto_judged_high: ~100% rationale coverage
#   bronze_clean: ~100% rationale coverage
```

## Rollback

```sql
-- If quality issues found post-apply, delete the new rationales:
DELETE FROM question_option_rationales
WHERE created_at >= '2026-05-22'::date
  AND question_id IN (
    SELECT id::text FROM question_bank
    WHERE quality_review_status IN ('auto_judged_high', 'bronze_clean')
  );
```

## Cost monitoring

- Gemini Flash Batch API: ~$0.0023 per rationale × 5 options × ~15,500 questions = **~$178** worst case
- Free tier may absorb partial volume (check Gemini dashboard before running)
- Hard ceiling: set `--limit 1000` for a pilot run first, validate quality, then scale up

## Quality gate (post-apply)

After 100-1000 sample apply, manually verify 10 questions:
1. Open question + correct answer + 4 rationales
2. Each rationale should explain WHY that option is wrong (or correct for the right answer)
3. Look for factual errors (e.g., the Hemingway→Stendhal hallucination from gpt-4o-mini's run)
4. If <90% correct, halt and re-prompt-tune; if ≥90%, scale to full 15K

## Legacy mode (R4-rule-based-gold scope only)

```bash
PHASE7_TARGET_RULE=R4_rule_based_gold python scripts/quality/metadata_phase7_batch_gemini.py build
```

Use only if you specifically want to re-target the legacy R4-tagged pool. Default mode is now status-based and covers all beta-eligible questions including R1 restores.
