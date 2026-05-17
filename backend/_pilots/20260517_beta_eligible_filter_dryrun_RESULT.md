# Beta Eligible Filter — DRYRUN RESULT

**Date:** 2026-05-17
**Filter version:** v1_faz_4_1_patterns
**Mode:** dryrun
**Elapsed:** 1.3s

## Rule Counts

| Rule | Count |
|---|---|
| R1_legacy_v3_reject | 18,397 |
| R2_aromat_reject | 2,932 |
| R3_edebiyat_sokagi_manual | 197 |
| R4_kalan_auto_judged_high | 81,776 |

## Pre/Post State

| Status | Pre | Post |
|---|---|---|
| bronze_clean | 84,905 | 84,905 |
| legacy_v3_unaudited | 18,397 | 18,397 |
| pending | 2,775 | 2,775 |
| unverified | 61,482 | 61,482 |

**v_safe_for_beta:** 0

## Audit trail format

```json
{"beta_filter_v1": {"date": "...", "filter_version": "v1_faz_4_1_patterns", "rule": "R1_legacy_v3 / R2_aromat / R3_edebiyat / R4_gold"}}
```
