# Quality Audit Dashboard — 2026-05-16

**Sources:** 3 SCORING TSV
**Date span:** 2026-05-15 → 2026-05-15

## Verdict Trend (time-ordered)

| Date | Audit | Total | Scored | pass | fail | unclear | empty | pass% | fail% |
|---|---|---|---|---|---|---|---|---|---|
| 2026-05-15 | `audit_C1` | 30 | 30 | 2 | 19 | 9 | 0 | %6.7 | %63.3 |
| 2026-05-15 | `audit_C2` | 50 | 50 | 15 | 25 | 10 | 0 | %30.0 | %50.0 |
| 2026-05-15 | `audit_C3` | 30 | 30 | 6 | 16 | 8 | 0 | %20.0 | %53.3 |

## Error Type Cross-Comparison

| Audit | garbage_text | incomplete | missing_diagram | ocr | wrong_answer | wrong_topic |
|---|---|---|---|---|---|---|
| 2026-05-15 `audit_C1` | — | — | 23 | 5 | — | — |
| 2026-05-15 `audit_C2` | — | 5 | — | 12 | 18 | — |
| 2026-05-15 `audit_C3` | 9 | 4 | 5 | 2 | 2 | 2 |

## Aggregate Across All Records

**Total scored:** 110 / 110 (%100.0)

| verdict | count | %scored |
|---|---|---|
| `pass` | 23 | %20.9 |
| `fail` | 60 | %54.5 |
| `unclear` | 27 | %24.5 |

| error_type | count |
|---|---|
| `missing_diagram` | 28 |
| `wrong_answer` | 20 |
| `ocr` | 19 |
| `incomplete` | 9 |
| `garbage_text` | 9 |
| `wrong_topic` | 2 |

## Drift Signals

Tek tarih var, time-series drift hesaplanamaz. Faz 2.6 (4 hafta baseline) sonrası anlamlı.
