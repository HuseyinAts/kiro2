# Faz 6.6 Opsiyon B — R2 Selective Restore (DRYRUN)

**Date:** 2026-05-17
**Version:** v2_r2_selective_restore_faz_6_6
**Mode:** dryrun
**Elapsed:** 0.0s

## Criteria

Single-subject Aromat kitapları (Matematik, Fizik, Türkçe, Edebiyat,
Paragraf) doğru etiketli — wrong_topic değil. Faz 5+6 R2 mass reject
yanlıştı. Sadece multi-disiplin volumler rejected kalmalı.

**Restore filter:**
```sql
WHERE quality_review_status = 'rejected'
  AND beta_filter_v1.rule = 'R2_aromat_wrong_topic'
  AND source_book NOT ILIKE '%Fen Bilimleri%'
  AND source_book NOT ILIKE '%Sosyal Bilimler%'
```

## Pre/Post State

| Metric | Pre | Post | Δ |
|---|---|---|---|
| rejected total | 21,329 | 21,329 | +0 |
| rejected via R2 | 2,932 | (after restore) | — |
| v_safe_for_beta | 22,325 | 22,325 | +0 |
| Restored | — | — | **2,463** |

## Source Book Breakdown (restored)

| Source Book | Count |
|---|---|
| Aromat Ayt 2023 2024 Fizik Soru Bankası | 755 |
| Aromat Tyt 2023 2024 Fizik Soru Bankası | 584 |
| Aromat -2023-2024-Matematik Soru Bankası | 388 |
| Aromat-2023-Ayt-Matematik Soru Bankası | 270 |
| Aromat Paragraf Soru Bankası | 207 |
| Aromat-2023-Tyt-Matematik Net 30 | 92 |
| Aromat Tyt Türkce Model Sorular | 67 |
| Aromat Ayt Edebiyat | 60 |
| Aromat-2024-Matematik Net 30 | 40 |

## Audit Trail

Restored satırlarda `pipeline_metadata.beta_filter_v2_r2_restore`:
```json
{
  "date": "2026-05-17",
  "restore_version": "v2_r2_selective_restore_faz_6_6",
  "previous_status": "rejected",
  "previous_rule": "R2_aromat_wrong_topic",
  "reason": "single_subject_aromat_correct_label"
}
```

Önceki `beta_filter_v1` audit korunur (rollback için).

