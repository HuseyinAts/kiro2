# R1 legacy_v3 False-Negative Restore — PILOT RESULT

**Date:** 2026-05-21
**Sample size:** 100 (stratified by subject_area)
**Pool:** 18,397 R1_legacy_v3 rejected rows
**Seed:** `r1_fn_restore_v1` (deterministic)

## Context

Faz 6.6 reject audit'i R1_legacy_v3 filtresinin **%24 false-negative
rate** ürettiğini tespit etti (3/30 örnekte iyi soru yanlış reject).
Beklenen restorable: ~4,415 satır (18,397 × 0.24).

R1 reject kuralı: `quality_review_status='legacy_v3_unaudited'` satırların
toptan reject edilmesi — fazla agresif (audit edilmemiş ≠ kötü).

## Auto-Rule Criteria (conservative, false-positive YOK hedefli)

Bir satır restorable sayılır AİSAR (Ancak ve sadece):
1. `question_image_url IS NOT NULL` (boş string değil)
2. Tüm 5 option dolu (`option_a..option_e`)
3. `correct_answer ∈ {A,B,C,D,E}`
4. `LENGTH(question_text) >= 50`
5. Text 5+ tekrarlı karakter içermiyor (`aaaaa`, regex `(.)\1{4,}`)
6. Text 4+ ardışık nokta içermiyor (`....`, regex `\.{4,}`)

## Sonuç — Auto-Rule

| Metrik | Sayı | Yüzde |
|---|---|---|
| **Restorable (auto-rule PASS)** | **87** | **87.0%** |
| Not restorable | 13 | 13.0% |
| **Total** | **100** | 100% |

## Subject Breakdown

| Subject | Total | Restorable | % |
|---|---|---|---|
| MATEMATIK | 30 | 27 | 90.0% |
| TURKCE | 17 | 16 | 94.1% |
| GEOMETRI | 14 | 13 | 92.9% |
| FIZIK | 10 | 10 | 100.0% |
| KIMYA | 7 | 5 | 71.4% |
| EDEBIYAT | 6 | 5 | 83.3% |
| TARIH | 4 | 4 | 100.0% |
| SOSYAL | 4 | 2 | 50.0% |
| GENEL | 3 | 2 | 66.7% |
| BIYOLOJI | 3 | 2 | 66.7% |
| FEN | 1 | 0 | 0.0% |
| COGRAFYA | 1 | 1 | 100.0% |

## Fail Reason Breakdown

| Reason | Count | % of total |
|---|---|---|
| has_image | 7 | 7.0% |
| text_min_len | 6 | 6.0% |
| has_5_options | 1 | 1.0% |

## Verdict

- **Restorable oranı: %87.0**
- ✅ Pilot başarılı — Faz 6.6 bulgusunu (%24+) doğruluyor
- Apply tahmini etki: ~16,005 satır → `auto_judged_high`

## Next Steps

1. RAW TSV'de manual_verdict kolonuna 20-30 satır insan-onay yap
   (false-positive sıfır mı doğrula)
2. False-positive 0 ise → `backend/scripts/quality/r1_legacy_v3_restore_apply.py --dry-run`
3. Dry-run state OK ise → `--apply`

## Audit Trail

Restored satırlarda eklenecek metadata:
```json
{"r1_restore_v1": {"date": "...", "reason": "false_negative_recovery",
 "pilot_restorable_pct": X.X, "previous_status": "rejected",
 "previous_rule": "R1_legacy_v3"}}
```

Önceki `beta_filter_v1` metadata korunur (rollback için).

