# Tier I Re-OCR — APPLY RESULT (2026-05-15)

**Model:** gemini-2.5-pro
**Threshold:** substr ≥ 0.5 (HIGH ≥ 0.7)
**Total processed:** 10
**Mode:** apply

## Stats

| Action | Count | % |
|---|---|---|
| applied_high | 8 | %80.0 |
| mid_skip | 2 | %20.0 |
| would_apply_high | 0 | %0.0 |

**Apply rate:** 8/10 (%80.0)
**Skip rate (low/error):** 0/10

**Backup:** `C:\Users\husey\kiro2\backend\_pilots\20260516_tier_i_BACKUP_apply.tsv`
**Detail TSV:** `C:\Users\husey\kiro2\backend\_pilots\20260516_tier_i_apply_RESULT.tsv`

## Karpathy + Tier H Lesson Notes

- ✅ Çift sinyal (jsonl key + Re-OCR substring)
- ✅ Pre-apply pilot 50 sample %100 precision
- ✅ Backup TSV (pre-state, rollback için)
- ✅ pipeline_metadata.tier_i_reocr audit trail
- ✅ question_text DOKUNULMAZ (sadece image_url + image_ocr_text)
