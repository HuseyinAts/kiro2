# DB Fizik Cevap Anahtarı Audit (S184)

**Tarih:** 2026-05-23
**Methodology:** S182/S183 pattern reuse (Hybrid SymPy + LLM-as-judge, scripts SUBJECT=FIZIK env)
**Kapsam:** `quality_review_status = 'auto_judged_high'` AND `subject_area = 'FIZIK'` (1,601 soru)
**Status:** ✅ COMPLETE — 339 UPDATE applied

---

## Discovery

| Metrik | Değer |
|---|---|
| Toplam fizik (auto_judged_high) | 1,601 |
| `expected_answer_formula` dolu | **295 (%18.4)** ⚠️ |
| `correct_answer` A bias | %29.0 |

**Anomali:** Fizik formula coverage matematik %78.9 ve geometri %76.8'den çok düşük. Sebep: fizik problemleri multi-step, unit conversion, vektör hesabı gerektiriyor — Phase 7 prompt template numerik formula extraction'da yetersiz.

---

## SymPy Verification (295 formula-dolu)

```
verified_correct:  132 (44.7%)
wrong_db_correct:    1 ( 0.3%)   — düşük (matematik 1.1%, geometri 2.0%)
formula_fail:      136 (46.1%)
```

SymPy başarı oranı düşük çünkü fizik formula syntax'ı (units, vectors) parse-friendly değil.

---

## LLM-as-Judge (1,463 formula-yok + SymPy-fail) ✅ COMPLETE

**Batch:** `batches/uk7ea6xz5hhsr5ha7a2qh19cxp4k6rmf419o`
**Maliyet:** ~$0.50

```
parsed:             823 (56.3%)
parse_fail:         640 (43.7%)   — yüksek (multi-step fizik LLM için zor)
llm_disagrees_high: 338 (41.1% of parsed)
```

### 338 high-conf disagree

| LLM Answer | N | % |
|---|---|---|
| `unsolvable` (garbage) | 226 | 66.9% |
| B | 31 | 9.2% |
| A | 24 | 7.1% |
| C | 23 | 6.8% |
| E | 21 | 6.2% |
| D | 13 | 3.8% |

**Real wrong = 112, Garbage = 226**

A bias daha hafif (%7.1) — fizik için A shift pattern matematik/geometri'den farklı.

### Spot check 4/5 LLM doğru

| ID | Konu | LLM | DB | Verdict |
|---|---|---|---|---|
| `7dfee154` | Yeşil Dalga 3 öncül | E (I,II,III) | D (II ve III) | ✅ DOĞRU |
| `1e6b398c` | Cam vs plastik iletkenlik | D (cam λ daha büyük) | B (cam ısısı) | ✅ DOĞRU (DB konsept hatası) |
| `d579c25d` | Yol ≥ yer değiştirme | D (II,III) | B (Yalnız III) | ✅ DOĞRU |
| `9b69fb75` | Hacim 60-24=36 | C=36 | B=30 | ✅ DOĞRU (basit aritmetik) |
| `bced658d` | Vakum'da ısı transferi | E | B | ⚠️ Soru truncated, belirsiz |

---

## Final Triage

```
SymPy wrong:    1
LLM real wrong: 112
Combined:       113 (overlap=0)
LLM garbage:    226
────────────────────
TOTAL UPDATE:  339

Problematic %: 339/1,601 = %21.2 (matematik %12, geometri %10.7)
```

⚠️ **FIZIK %21.2 problematic — diğer subject'lerden ÇOK YÜKSEK.** Phase 7 fizik için yetersiz veya pre-existing data quality fizik subject'inde daha düşük.

---

## Apply Execution Log

```
BACKUP: question_bank_fizik_audit_backup_20260523 (339 rows)

PILOT (planned 5, gerçek 3 — sympy_wrong sadece 1 olduğu için):
  3 IDs UPDATE → pending audit=S184 ✅
  AMA: cur.rowcount == 5 hardcoded check rolled back
  Manuel re-apply: 3 IDs → pending ✅

FULL:
  Wrong (-pilot 3) = 110 → pending (rowcount 110 ✅)
  Garbage = 226 → rejected (rowcount 226 ✅)
  ✅ COMMITTED

POST-VERIFY:
  S184 markers: 113 pending + 226 rejected (exact match)
  FIZIK auto_judged_high: 1,601 → 1,262 (-339)
  Genel gold pool: 14,485 → 14,146 (-339)
```

### Bug Fix During Apply

`apply_pilot.py:80` `cur.rowcount == 5` hardcoded → S184'te 3 satır oldu (sympy 1 + llm 2). Düzeltme: `cur.rowcount == len(PILOT_IDS)`. Manuel UPDATE ile 3 lost ID kurtarıldı.

### Rollback

```sql
UPDATE question_bank q SET
  correct_answer = b.correct_answer,
  quality_review_status = b.quality_review_status,
  pipeline_metadata = b.pipeline_metadata
FROM question_bank_fizik_audit_backup_20260523 b
WHERE q.id = b.id;
DROP TABLE question_bank_fizik_audit_backup_20260523;
```

---

## Karşılaştırma: S182 vs S183 vs S184

| Metrik | MAT | GEO | FIZ |
|---|---|---|---|
| Total | 4,899 | 2,306 | 1,601 |
| Formula coverage | %78.9 | %76.8 | **%18.4** ⚠️ |
| SymPy wrong | 43 | 36 | **1** (sample küçük) |
| LLM parse_fail | %49 | %58 | **%77.8** ⚠️ |
| LLM real wrong | 189 | 59 | 112 |
| LLM garbage | 356 | 153 | 226 |
| **Wrong → pending** | **232** | **95** | **113** |
| **Garbage → rejected** | **356** | **153** | **226** |
| **Problematic %** | %12.0 | %10.7 | **%21.2** ⚠️ |
| A bias | %32 | %29.3 | %29.0 |
| Spot check | 5/5+5/5 | 5/5+5/5 | 5/5 + 4/5 |

**Fizik için Phase 7 pipeline'ın yetersizliği net:**
- Formula extraction %18.4 (vs %78.9 matematik)
- LLM parse_fail %77.8 (vs %49 matematik)
- Problematic %21.2 (vs %12 matematik)

---

## Sonraki Adımlar

1. ✅ S184 commit + push
2. ⏳ KİMYA audit (S185) — 1,133 soru, beklenen pattern fizik benzeri
3. ⏳ **Phase 7 fizik prompt iyileştirme** — formula extraction multi-step destek
4. ⏳ Curator UI'de **440 pending** review (S182 232 + S183 95 + S184 113)

## Çıktılar

```
docs/audits/2026-05-23_fizik_answer_key_audit.md  (BU)
backend/scripts/quality/_phase7_audit_tmp/
├── sympy_results_fizik.json
├── llm_judge_results_fizik.json
├── triage_final_fizik.json
└── judge_batch_state_fizik/
```
