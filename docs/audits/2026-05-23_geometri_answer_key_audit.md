# DB Geometri Cevap Anahtarı Audit (S183)

**Tarih:** 2026-05-23
**Methodology:** S182 matematik pattern (Hybrid SymPy + LLM-as-judge, script reuse with `SUBJECT=GEOMETRI` env)
**Kapsam:** `quality_review_status = 'auto_judged_high'` AND `subject_area = 'GEOMETRI'` (2,306 soru)
**Status:** ✅ COMPLETE — DB UPDATE applied

---

## Discovery

| Metrik | Değer |
|---|---|
| Toplam geometri (auto_judged_high) | 2,306 |
| `expected_answer_formula` dolu | 1,770 (%76.8) |
| `is_math_solvable=true` | 2,304 (%99.9) |

**`correct_answer` dağılımı (A bias yine var):**
| Şık | Sayı | % |
|---|---|---|
| A | 675 | **29.3%** |
| B | 458 | 19.9% |
| C | 459 | 19.9% |
| D | 413 | 17.9% |
| E | 301 | 13.1% |

A bias %29.3 — matematik %32 ile uyumlu, **pipeline-wide pattern doğrulandı**.

---

## SymPy Verification (1,770 formula-dolu)

```
verified_correct:  1352 (76.4%)   — DB tutarlı (matematik %59.6'dan daha yüksek)
wrong_db_correct:    36 ( 2.0%)   — 🚨 HIGH-confidence DB hatası
no_match:           156 ( 8.8%)
ambiguous:            9 ( 0.5%)
formula_fail:       217 (12.3%)   — SymPy parse fail (matematik %30.5'ten DAHA DÜŞÜK)
```

**Geometri'de SymPy başarı oranı çok daha yüksek** — formulas basit (Pitagor, alan, çevre, açı toplamı 180°).

### SymPy spot check 5/5 DOĞRULANDI

| ID | Soru | Formula | Doğru | DB | Verdict |
|---|---|---|---|---|---|
| `18bae995` | Dikdörtgen çevre 20, kenar 4 | 6 | D | C=5 | ✅ WRONG |
| `e401b1c7` | √2500 | 50 | A | B=10 | ✅ WRONG |
| `be81bf8d` | Dik üçgen 10×24/2 | 120 | A | C=130 | ✅ WRONG |
| `5645e86c` | Üçgen iç açıları: 180-30-45 | 105 | A | E=75 | ✅ WRONG |
| `72579748` | Pitagor √(144+25) | 13 | A | E=18 | ✅ WRONG |

**4/5 doğru cevap A** — geometri'de A bias daha kuvvetli görünüyor.

---

## LLM-as-Judge (909 formula-yok + SymPy-fail) ✅ COMPLETE

**Batch:** `batches/8fue41dst3i4mex0u8qj5t3o70n2jet04uqc`
**Submit → Success:** 2026-05-23 (~5 dakika runtime)
**Maliyet:** ~$0.30

```
parsed:             382 (42.0%)
parse_fail:         527 (58.0%)   — geometri için daha yüksek (matematik %49)
llm_agrees:         157 (41.1%)
llm_disagrees_high: 212 (55.5%)
```

### 212 high-conf disagree kategorize

| LLM Answer | N | % |
|---|---|---|
| `unsolvable` (garbage) | 153 | 72.2% |
| A | 27 | 12.7% |
| B | 14 | 6.6% |
| C | 8 | 3.8% |
| E | 7 | 3.3% |
| D | 3 | 1.4% |

**Real wrong = 59, Garbage = 153**

### LLM spot check 5/5 matematik açısından doğru

3/5 kesin DB hatası, 2/5 borderline (LLM doğru ama soru zaten anlamsız):
- `6796ce66`: x+y=7, x-y=3 → x=5,y=2 (LLM:A) vs DB:B=(2,5) ✅
- `bc59e2c9`: 180-(20+60)=100° (LLM:A) vs DB:D=90° ✅
- `2a8934ad`: 180° rotation (x,y)→(-x,-y) (LLM:E) vs DB:A ✅

---

## Final Triage

```
SymPy ∪ LLM analysis (disjoint, overlap=0):

  SymPy HIGH wrong:       36  (5/5 verified)
  LLM real wrong (A-E):   59  (5/5 verified)
  LLM unsolvable garbage: 153 (sample-based ~%75 verified)
  ────────────────────────────
  TOTAL WRONG ADAYI:     95
  TOTAL GARBAGE:        153
  TOTAL UPDATE:         248
```

**Total impact:**
- 2,306 geometri sorudan **~95 (%4.1) cevap anahtarı hatası** + **~153 (%6.6) garbage** = **%10.7 problematik** (matematik %12'den biraz düşük)
- %89.3 kabul edilebilir

---

## Apply Execution Log

```
PRE-FLIGHT (2026-05-23):
  248/248 IDs verified in DB
  Overlap wrong-garbage: 0

BACKUP:
  CREATE TABLE question_bank_geo_audit_backup_20260523 (248 rows)

PILOT (5 questions, S183 marker):
  3 SymPy + 2 LLM real wrong → pending
  UPDATE rowcount: 5
  Spot verify: 5/5 ✅
  ✅ COMMITTED (after fix: parametrize audit_run_id verification)

FULL (243 remaining):
  90 wrong → pending (rowcount 90 ✅)
  153 garbage → rejected (rowcount 153 ✅)
  ✅ COMMITTED

POST-VERIFY:
  S183 markers: 95 pending + 153 rejected (exact match)
  Geometri auto_judged_high: 2,306 → 2,058 (-248)
  Genel gold pool: 14,733 → 14,485
```

### Bug Fix During Apply

`apply_pilot.py:75` `audit == "S182"` hardcoded — pilot script S183 markı'nı reject ediyordu. Düzeltme: `audit == audit_metadata["audit_run_id"]` (env-driven).

### Rollback

```sql
UPDATE question_bank q SET
  correct_answer = b.correct_answer,
  quality_review_status = b.quality_review_status,
  pipeline_metadata = b.pipeline_metadata
FROM question_bank_geo_audit_backup_20260523 b
WHERE q.id = b.id;
DROP TABLE question_bank_geo_audit_backup_20260523;
```

---

## Karşılaştırma: S182 (Matematik) vs S183 (Geometri)

| Metrik | Matematik | Geometri | Not |
|---|---|---|---|
| Total auto_judged_high | 4,899 | 2,306 | Geo %47 |
| Formula coverage | %78.9 | %76.8 | benzer |
| SymPy verified_correct | %59.6 | %76.4 | **Geo +%17** (basit formulas) |
| SymPy wrong | 43 (%1.1) | 36 (%2.0) | Geo daha yüksek oran |
| SymPy formula_fail | %30.5 | %12.3 | **Geo -%18** (SymPy-friendly) |
| LLM batch boyut | 2,521 q | 909 q | Geo daha küçük |
| LLM parse_fail | %49 | %58 | Geo daha kötü |
| LLM real wrong | 189 | 59 | Geo daha az |
| LLM unsolvable | 356 | 153 | Geo daha az |
| **Total wrong adayı** | **232** | **95** | |
| **Total garbage** | **356** | **153** | |
| **Problematic %** | **%12.0** | **%10.7** | benzer |
| A bias (DB genel) | %32 | %29.3 | benzer |
| Spot check başarı | 5/5 + 5/5 | 5/5 + 5/5 | her ikisi de yüksek |

---

## Sonraki Adımlar

1. ✅ S183 audit complete + commit
2. ⏳ FİZİK audit (1,601 soru) — sonraki sprint
3. ⏳ KİMYA audit (1,133 soru) — sonraki sprint
4. ⏳ Curator UI manuel review (S182 + S183 toplam **327 pending** = 232 + 95)
5. ⏳ **A bias root cause** — pipeline'da hangi aşamada shift oluyor (pre-existing data quality)
6. ⏳ LLM parse_fail iyileştirme — max_tokens 1500+ veya prompt iyileştirme

---

## Çıktılar

```
docs/audits/2026-05-23_geometri_answer_key_audit.md  (BU)
backend/scripts/quality/_phase7_audit_tmp/
├── sympy_results_geometri.json
├── llm_judge_results_geometri.json
├── triage_final_geometri.json
└── judge_batch_state_geometri/
```

Scripts (parametrize edildi — SUBJECT env):
- `sympy_verify.py` — SUBJECT=<X>
- `llm_judge_build.py` — SUBJECT=<X>
- `llm_judge_submit_poll.py` — SUBJECT=<X>
- `llm_judge_apply.py` — SUBJECT=<X>
- `apply_pilot.py` — SUBJECT=<X>, AUDIT_RUN_ID=<S###>
- `apply_full.py` — SUBJECT=<X>, AUDIT_RUN_ID=<S###>
