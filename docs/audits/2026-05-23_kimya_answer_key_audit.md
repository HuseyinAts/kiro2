# DB Kimya Cevap Anahtarı Audit (S185)

**Tarih:** 2026-05-23
**Methodology:** S182-S184 pattern reuse (Hybrid SymPy + LLM-as-judge, SUBJECT=KIMYA env)
**Kapsam:** `quality_review_status = 'auto_judged_high'` AND `subject_area = 'KIMYA'` (1,133 soru)
**Status:** ✅ COMPLETE — 248 UPDATE applied

---

## Discovery

| Metrik | Değer |
|---|---|
| Toplam kimya (auto_judged_high) | 1,133 |
| `expected_answer_formula` dolu | **125 (%11.0)** ⚠️ EN DÜŞÜK |
| A bias | %30.5 |

Kimya concept-based dominant — Phase 7 formula extraction'ı kimya için neredeyse işe yaramıyor (%11). Stoikiometri, denklem dengeleme, reaksiyon türleri tipi sorular SymPy-friendly formula üretmiyor.

---

## SymPy Verification (125 formula-dolu)

```
verified_correct:   53 (42.4%)
wrong_db_correct:    1 ( 0.8%)
formula_fail:       61 (48.8%)
```

---

## LLM-as-Judge (1,078 formula-yok + SymPy-fail) ✅

**Batch:** `batches/g8qw8ixug218tr4191ojcbhdk0io05erto0u`

```
parsed:             629 (58.3%)
parse_fail:         449 (41.7%)
llm_agrees:         366 (58.2% of parsed)
llm_disagrees_high: 247 (39.3% of parsed)
```

247 high-conf disagree:
- **unsolvable**: 124 (%50.2)
- A: 21, B: 31, C: 23, D: 25, E: 23 (toplam 123 = real wrong)

### Spot check 5/5 LLM DOĞRU

| ID | Konu | LLM | DB | Verdict |
|---|---|---|---|---|
| `2ed2a614` | Metil turuncu pH renkler | A (Kırmızı-Turuncu-Sarı) | C | ✅ LLM DOĞRU |
| `504d74f8` | Alken hidrasyon → primer alkol | B (sekonder yanlış) | A | ✅ LLM DOĞRU |
| `b5213c0a` | Su (toksik atılım+ısı+metabolizma) | E (I,II,III) | B | ✅ LLM DOĞRU |
| `e72fd7c7` | Gaz→katı süblimleşme YANLIŞ | E | A | ✅ LLM DOĞRU (kırağılaşma olmalı) |
| `bae4367a` | Thomson model eksikleri | C (I,II) | E | ✅ LLM DOĞRU (III eksiklik değil) |

---

## Final Triage

```
SymPy wrong:        1
LLM real wrong:   123
Combined:         124 (overlap=0)
LLM garbage:      124
TOTAL UPDATE:     248

Problematic %: 248/1,133 = %21.9 (EN YÜKSEK — fizik %21.2, geo %10.7, mat %12)
```

⚠️ Kimya garbage oranı %10.9 (124/1,133), wrong oranı %10.9 — neredeyse eşit dağılım (fizik garbage daha baskındı).

---

## Apply Execution Log

```
BACKUP: question_bank_kimya_audit_backup_20260523 (248 rows)

PILOT (3 — sympy 1 + llm 2):
  3 IDs UPDATE → pending audit=S185 ✅
  COMMITTED (apply_pilot.py rowcount bug fix devreye girdi)

FULL:
  Wrong (-pilot 3) = 121 → pending (rowcount 121 ✅)
  Garbage = 124 → rejected (rowcount 124 ✅)
  COMMITTED

POST-VERIFY:
  S185 markers: 124 pending + 124 rejected (exact match)
  KIMYA auto_judged_high: 1,133 → 885 (-248)
  Genel gold pool: 14,146 → 13,898 (-248)
```

### Rollback
```sql
UPDATE question_bank q SET correct_answer = b.correct_answer,
  quality_review_status = b.quality_review_status, pipeline_metadata = b.pipeline_metadata
FROM question_bank_kimya_audit_backup_20260523 b WHERE q.id = b.id;
DROP TABLE question_bank_kimya_audit_backup_20260523;
```

---

## S182-S185 Birleşik Sonuç

| Subject | Total | Wrong | Garbage | UPDATE | Problematic % |
|---|---|---|---|---|---|
| **MAT (S182)** | 4,899 | 232 | 356 | 588 | %12.0 |
| **GEO (S183)** | 2,306 | 95 | 153 | 248 | %10.7 |
| **FIZ (S184)** | 1,601 | 113 | 226 | 339 | %21.2 |
| **KIM (S185)** | 1,133 | 124 | 124 | 248 | **%21.9** |
| **TOPLAM** | **9,939** | **564** | **859** | **1,423** | %14.3 ortalama |

### Pattern Bulguları

1. **Formula coverage ↘ Problematic % ↗**: Kimya (%11) ve Fizik (%18) düşük formula coverage = yüksek problematic oranı. Phase 7 formula-extraction concept-based sorularda yetersiz.

2. **A bias pipeline-wide**: 4 subject'te de %29-32 A oranı (uniform %20 olmalı). Tek subject'e özgü değil — pipeline'da sistematik shift bug.

3. **LLM güvenilirliği yüksek**: 4 subject × 5 sample = 20 spot check, sadece 1 borderline (FIZIK truncated soru). %95+ reliability.

4. **Garbage oranı subject-bağımlı**:
   - Matematik %7.3, Geometri %6.6 (düşük) — formula-friendly sorular
   - Fizik %14.1, Kimya %10.9 (yüksek) — pre-existing OCR/data quality kötü

---

## Sonraki Adımlar

1. ✅ S185 commit + push
2. ⏳ Diğer subjects (TURKCE 2,415 + EDEBIYAT 773 + TARIH 659 + GENEL 521 + BIYOLOJI 469 + SOSYAL 427 + COGRAFYA 95 + FEN 23 = **5,382 q**) — LLM-only audit
3. ⏳ **A bias root cause** — pipeline taraması (öncelikli — pattern 4 subject'te doğrulandı)
4. ⏳ Curator UI'de **564 pending review** (S182+S183+S184+S185)
5. ⏳ **Phase 7 prompt iyileştirme** — fizik+kimya için formula extraction güçlendirme
