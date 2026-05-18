# Beta Eligible Filter v2 — DRYRUN RESULT

**Date:** 2026-05-18
**Filter version:** v2_nonsense_truncation
**Mode:** dryrun
**Elapsed:** 813.4s

## Rule Counts

| Rule | Count |
|---|---|
| R5a_repeated_char_7plus | 59 |
| R5b_ends_with_ellipsis | 12 |
| R6_truncation_no_terminal | 318 |
| **TOTAL (overlap dahil)** | **389** |

## Pre/Post State

| Status | Pre | Post |
|---|---|---|
| auto_judged_high | 84,239 | 84,239 |
| bronze_clean | 197 | 197 |
| pending | 2,775 | 2,775 |
| rejected | 18,866 | 18,866 |
| unverified | 61,482 | 61,482 |

**v_safe_for_beta:** 23,497

## Bug coverage

| Bug | Status |
|---|---|
| Bug #5 AI nonsense filter | R5a + R5b ✅ |
| Bug #9 OCR truncation residual | R6 ✅ |
| Bug #7 question-image MISMATCH | NEUTRALIZED via Bug #11 (image suppress) |
| Bug #10 image yok/yanlış | NEUTRALIZED via Bug #11 (image suppress) |
| Bug #11 vision audit classification | DEFER — post-beta vision re-crop |

## Audit trail format

```json
{"beta_filter_v2": {"date": "...", "filter_version": "v2_nonsense_truncation", "rule": "R5a / R5b / R6"}}
```
