# Tier I Re-OCR — DRYRUN RESULT (2026-05-15)

**Model:** gemini-2.5-pro
**Threshold:** substr ≥ 0.5 (HIGH ≥ 0.7)
**Total processed:** 100
**Mode:** dryrun

## Stats

| Action | Count | % |
|---|---|---|
| would_apply_high | 54 | %54.0 |
| would_apply_mid | 24 | %24.0 |
| low_skip | 12 | %12.0 |
| gemini_error | 10 | %10.0 |
| applied_high | 0 | %0.0 |
| applied_mid | 0 | %0.0 |

**Apply rate:** 78/100 (%78.0)
**Skip rate (low/error):** 22/100

**Backup:** `C:\Users\husey\kiro2\backend\_pilots\20260516_tier_i_BACKUP_dryrun.tsv`
**Detail TSV:** `C:\Users\husey\kiro2\backend\_pilots\20260516_tier_i_dryrun_RESULT.tsv`

## Karpathy + Tier H Lesson Notes

- ✅ Çift sinyal (jsonl key + Re-OCR substring)
- ✅ Pre-apply pilot 50 sample %100 precision
- ✅ Backup TSV (pre-state, rollback için)
- ✅ pipeline_metadata.tier_i_reocr audit trail
- ✅ question_text DOKUNULMAZ (sadece image_url + image_ocr_text)
