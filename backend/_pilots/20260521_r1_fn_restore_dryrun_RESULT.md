# R1 legacy_v3 False-Negative Restore — DRYRUN RESULT

**Date:** 2026-05-21
**Version:** r1_restore_v1
**Mode:** dryrun
**Elapsed:** 0.0s
**Pilot:** %87.0 restorable (100 sample, 2026-05-21)

## Context

Faz 6.6 reject audit'i R1_legacy_v3 filtresinin %24 false-negative
rate gösterdiğini tespit etti. R1 kural: `legacy_v3_unaudited` durumundaki
tüm satırları toptan reject — audit edilmemiş ≠ kötü olduğu için fazla agresif.

Bu restore conservative auto-rule ile (image + 5 opt + valid CA + len + no garbage)
false-positive YOK hedefli kurtarma yapar.

## Restore Filter

```sql
WHERE quality_review_status = 'rejected'
  AND beta_filter_v1.rule = 'R1_legacy_v3'
  AND question_image_url IS NOT NULL AND <> ''
  AND option_a..option_e all NOT NULL AND <> ''
  AND correct_answer IN ('A','B','C','D','E')
  AND LENGTH(question_text) >= 50
  AND question_text !~ '(.)\1{4,}'  -- no 5+ repeat char
  AND question_text !~ '\.{4,}'      -- no 4+ ellipsis
```

## Pre/Post State

| Metric | Pre | Post | Δ |
|---|---|---|---|
| rejected total | 69,447 | 69,447 | +0 |
| rejected via R1 | 18,397 | (after restore) | — |
| auto_judged_high | 0 | 0 | +0 |
| v_safe_for_beta | 0 | 0 | +0 |
| **Restored** | — | — | **15,321** |

## Subject Breakdown (restored)

| Subject | Count |
|---|---|
| MATEMATIK | 4,899 |
| TURKCE | 2,415 |
| GEOMETRI | 2,306 |
| FIZIK | 1,601 |
| KIMYA | 1,133 |
| EDEBIYAT | 773 |
| TARIH | 659 |
| GENEL | 521 |
| BIYOLOJI | 469 |
| SOSYAL | 427 |
| COGRAFYA | 95 |
| FEN | 23 |

## NOT-Restorable Causes (R1 pool, can overlap)

| Cause | Count |
|---|---|
| no_image | 1,411 |
| partial_options | 252 |
| invalid_correct_answer | 0 |
| too_short (<50 char) | 1,553 |
| repeat_char (5+) | 56 |
| ellipsis_garbage (4+ dots) | 4 |

## Audit Trail

Restored satırlarda `pipeline_metadata.r1_restore_v1`:
```json
{
  "date": "2026-05-21",
  "restore_version": "r1_restore_v1",
  "reason": "false_negative_recovery",
  "pilot_restorable_pct": 87.0,
  "previous_status": "rejected",
  "previous_rule": "R1_legacy_v3",
  "criteria_summary": "image+5opt+valid_ca+len>=50+no_repeat_char+no_ellipsis"
}
```

Önceki `beta_filter_v1` audit korunur (rollback için).

## Rollback SQL

```sql
UPDATE question_bank
SET quality_review_status = 'rejected',
    pipeline_metadata = (pipeline_metadata::jsonb - 'r1_restore_v1')::json,
    updated_at = NOW()
WHERE pipeline_metadata::jsonb ? 'r1_restore_v1'
  AND pipeline_metadata::jsonb -> 'r1_restore_v1' ->> 'restore_version' = 'r1_restore_v1';
```

