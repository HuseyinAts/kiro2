# S195 Curator UI 905 Pending Apply (Plan D Hybrid)

**Tarih:** 2026-05-23
**Methodology:** SymPy direct + Gemini second-round consensus verification
**Kapsam:** 905 pending (S182-S193 audit'inden) — 673 işlemlenebilir suggested_answer
**Status:** ✅ COMPLETE — 537 q apply

---

## Strateji: Plan D (Hybrid Verify)

Kullanıcı talebi: "Curator UI 905 pending SEN YAP" (operator yerine otomatik consensus).
Risk azaltma: ekstra LLM verification round (Gemini Batch second pass with verification prompt).

```
905 pending
├── 673 işlemlenebilir (audit'te suggested_answer kaydedildi)
│   ├── 38 SymPy verified → DIRECT APPLY (deterministic, 5/5 spot check)
│   └── 635 LLM-only → SECOND ROUND VERIFY
│       ├── 499 verified=yes → APPLY (consensus)
│       ├── 132 parse_fail → SKIP (manual review)
│       ├── 3 verified=no → SKIP (LLM kendi çürüttü)
│       └── 1 unsure → SKIP
└── 232 işlemlenemez (önceki audit pilot'larında suggested kayıt yok)
    └── Manual curator için pending kalır
```

## Execution Log

### 1. Aggregate (`pending_apply_plan.json`)
- 12 subject triage JSON tarandı (`sympy_results_*`, `llm_judge_results_*`)
- 673 q için suggested_answer extracted
- DB intersection: 232 q audit'te suggested kayıt yok (pilot UPDATE'ler)

### 2. SymPy Direct Apply
- Backup: `question_bank_curator_apply_backup_20260523` (38 rows)
- UPDATE: 38/38 rowcount MATCH
- Audit marker: `curator_apply_2026_05_23.method = 'sympy_curator_consensus'`

### 3. LLM Second-Round Verification
- Batch: `batches/tz91kgnr1fxvuo95gof6sye3a0p679eitbc3` (gemini-flash-latest)
- 635 q × verification prompt ("Bu cevap doğru mu? yes/no/unsure")
- Submit → Success ~5 dk
- Maliyet: ~$0.30

### 4. Consensus Logic
- `verified == "yes"` AND first-round suggested → APPLY
- `verified == "no"/"unsure"/parse_fail` → SKIP (pending'de bırak)
- 499 verified=yes (78.6% consensus rate from 635)

### 5. LLM Consensus Apply
- Backup: `question_bank_curator_llm_backup_20260523` (499 rows)
- UPDATE: 499/499 rowcount MATCH
- Audit marker: `curator_apply_2026_05_23.method = 'llm_curator_consensus'`
- pipeline_metadata.curator_apply_2026_05_23 fields:
  - method, audit_run_id, verification, applied_at, suggested, llm_reasoning

### 6. Spot Check (5/5 PASS)

| ID | Subject | new correct | suggested | match |
|---|---|---|---|---|
| 6fb96058 | FIZIK | B | B | ✅ |
| f66817a6 | SOSYAL | A | A | ✅ |
| ec3c2d68 | KIMYA | B | B | ✅ |
| d1232bdb | GEOMETRI | A | A | ✅ |
| 5a20d762 | KIMYA | B | B | ✅ |

---

## Final State

```
Gold pool TOPLAM: 13,311 (12,774 → +537)
Pending remaining: 368
   ├── 132 LLM parse_fail (response truncated)
   ├── 232 audit'te suggested kayıt yok (eski pilot UPDATE'ler)
   └── 4 verified=no/unsure
```

## Rollback

```sql
-- SymPy 38 rollback
UPDATE question_bank q SET
  correct_answer = b.correct_answer,
  quality_review_status = b.quality_review_status,
  pipeline_metadata = b.pipeline_metadata
FROM question_bank_curator_apply_backup_20260523 b
WHERE q.id = b.id;

-- LLM 499 rollback
UPDATE question_bank q SET
  correct_answer = b.correct_answer,
  quality_review_status = b.quality_review_status,
  pipeline_metadata = b.pipeline_metadata
FROM question_bank_curator_llm_backup_20260523 b
WHERE q.id = b.id;
```

---

## Gemini Model Configuration

**Bundan sonra default:** `gemini-3.5-flash` (kullanıcı talebi).
Scripts güncellendi:
- `backend/scripts/quality/metadata_phase7_batch_gemini.py:46`
- `backend/scripts/quality/_phase7_audit_tmp/llm_judge_submit_poll.py`

Env override: `GEMINI_MODEL` ile değiştirilebilir.

---

## Effort Summary (Cumulative S181-S195)

```
Commits:                        24
Audit raporları:                10
Phase 7 gold coverage:          0% → 99.95%
DB UPDATE'ler:
  S181 Phase 7 (rationale):     92,377
  S182-S193 (status downgrade): 2,547 (905 pending + 1,642 rejected)
  S195 curator apply:           537 (38 SymPy + 499 LLM consensus)
Net gold pool delta:            15,321 → 13,311 (-2,010 = -%13.1)
Maliyet toplam:                 ~$13
Phantom yakalandı:              4
Pipeline bug FIX'lendi:         1 (S194 ai_upgrade tier)
Backup tablolar:                14 (rollback hazır)
```

## Açık İşler

| # | Görev | Süre |
|---|------|------|
| 1 | API key rotate (kullanıcı) | 5 dk |
| 2 | 368 pending manual review (operator) | ~3 saat |
| 3 | Phase 7 prompt iyileştirme (concept-based subjects) | sprint |
| 4 | page_inline OCR multi-model consensus | sprint |
| 5 | GitHub Actions kontrol (Task #270) | 5 dk |
