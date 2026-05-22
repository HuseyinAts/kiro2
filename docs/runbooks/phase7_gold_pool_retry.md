# Phase 7 Gold Pool Rationale Generation Runbook

**Status**: ✅ EXECUTED 2026-05-22 (S181) — see [Execution History](#execution-history)
**Audit reference**: `docs/audits/2026-05-22_product_ready_audit/05_data_quality.md` §Phase 7
**Actual cost**: ~$5-8 (15,518 q × Gemini 2.5 Flash Batch — _initial $300 estimate was stale Faz 5.6 80K Bronze projection_)
**Actual wall time**: 30 dakika (S181 ana batch, 23.4MB JSONL — Gemini SLA 24h ama queue boş olunca hızlı)

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

## Cost monitoring (gerçek S181 ölçümü)

Per-question token analysis (`metadata_phase7_llm_generation.py:111`):
- **Input**: ~600 tok/q (system prompt + question + 5 options + instructions)
- **Output**: ~225 tok/q (5 rationale × 25 kelime + tags + steps + formula JSON)
- **15,518 q total**: 9.3M input + 3.5M output tokens

Gemini 2.5 Flash Batch pricing (May 2026, %50 batch discount):
- Input: 9.3M × $0.15/M = **$1.40**
- Output: 3.5M × $1.25/M = **$4.38**
- **Total ~$5-8** (Türkçe tokenization +%30 buffer ile)

Önceki "$300" projeksiyonu yanlıştı — token sayısı 7K input/q sanılmıştı, gerçek ~600.

Hard ceiling: pilot için `--limit 200` yeter (135 fail soru recovery için).

## Execution History

### S181 Ana Batch — 2026-05-22 15:57→16:27 (30dk runtime) ✅
- Batch ID: `batches/y291wn12e8zugymclye8w40p6p0nalpbe8hp`
- Build: 15,518 q (auto_judged_high 15,321 + bronze_clean 197) → 23.4MB JSONL
- Submit: gemini-flash-latest, resumable upload
- Apply: success 15,377 / 15,518 (**%99.1**), fail 141 (%0.9 — önceki R4 batch %5.7'den dramatik iyileşme)
- DB: 76,885 rationale rows + 15,377 question_bank UPDATE
- Coverage: auto_judged_high **0% → 99.1%**, bronze_clean **0% → 97.0%**
- Commits: `6bcd4e626..3693f2f09`
- S180 audit P0 #2 ÇÖZÜLDÜ

### S181 Bonus Apply — stale R4 batch (1,898 q, S180 öncesi build)
- Apply: success 1,790 / 1,898 (%94.3)
- Net value: 485 pending LIVE (%27) + 1,413 rejected DEAD (%73)
- Idempotent ON CONFLICT — zarar yok, sunk cost

### S181 Mini Retry — 2026-05-22 ~22:00 (141 fail questions) 🟡 IN PROGRESS
- Batch ID: `batches/7cknizzmrgl3m5j47be46z6w1clypkyks6u6`
- Target: auto_judged_high'da kalan 135 + bronze_clean kalan 6
- Beklenen: gold %99.1 → %99.8

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
