# Beta Eligible Filter v2 — APPLY RESULT

**Date:** 2026-05-19
**Filter version:** v2_truncation_only
**Mode:** apply
**Elapsed:** 7.4s

## Rule Counts

| Rule | Count |
|---|---|
| R6_truncation_no_terminal | 318 |
| **TOTAL (overlap dahil)** | **318** |

## Pre/Post State

| Status | Pre | Post |
|---|---|---|
| auto_judged_high | 84,239 | 83,921 |
| bronze_clean | 197 | 197 |
| pending | 2,775 | 2,775 |
| rejected | 18,866 | 19,184 |
| unverified | 61,482 | 61,482 |

**v_safe_for_beta:** 23,417

## Bug coverage

| Bug | Status |
|---|---|
| Bug #5 AI nonsense filter | DEFER → Faz 6.1 LLM judge (rule-based yanlış pozitif riski yüksek) |
| Bug #9 OCR truncation residual | R6 ✅ |
| Bug #7 question-image MISMATCH | NEUTRALIZED via Bug #11 (image suppress) |
| Bug #10 image yok/yanlış | NEUTRALIZED via Bug #11 (image suppress) |
| Bug #11 vision audit classification | DEFER — post-beta vision re-crop |

## Audit trail format

```json
{"beta_filter_v2": {"date": "...", "filter_version": "v2_nonsense_truncation", "rule": "R5a / R5b / R6"}}
```
