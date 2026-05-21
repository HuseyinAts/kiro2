# Data Quality Audit — Product Readiness (2026-05-22)

Live PostgreSQL 18 @ `localhost:5434/kiro2`. READ-ONLY queries only.

## 🚨 CRITICAL: MEMORY.md vs Live Database

| Claim | MEMORY.md | Live DB | Drift | Status |
|-------|-----------|---------|-------|--------|
| Total active questions | 77,336 | **167,559** | **+116.5%** | ⚠️ SEVERELY STALE |
| Image coverage | 87,177 (52%) | **165,885 (98.99%)** | +90% | ⚠️ STALE (improved) |
| Phase 7 gold rationale | 76,733/81,776 (93.8%) | **0 / 15,321** | -100% | 🔴 WRONG CLAIM |
| question_option_rationales rows | 383,660 | 408,720 | +6.5% | 🟡 minor drift |
| v_safe_for_beta | 12,362 | 12,362 | 0% | ✅ MATCH |
| quality_review_status dist | (see MEMORY) | identical | 0% | ✅ MATCH |

**Verified independently** by claude with direct psql queries on 2026-05-22.

## Quality Review Status Distribution (live)

| Status | Active questions | w/ rationales | rationale coverage |
|---|---|---|---|
| auto_judged_high (gold) | 15,321 | **0** | **0% 🔴** |
| bronze_clean (curator queue) | 197 | 0 | 0% |
| pending | 36,433 | 32,726 | 89.8% |
| rejected | 54,126 | 48,942 | 90.4% |
| unverified | 61,482 | 77 | 0.1% |
| **TOTAL** | **167,559** | 81,745 | 48.8% |

## Critical Column Nullability (P0 — ALL PASS)

| Column | NULL count / Total | Status |
|---|---|---|
| correct_answer | 0 / 167,559 | ✅ PASS |
| subject_area | 0 / 167,559 | ✅ PASS |
| primary_topic_id | 0 / 167,559 | ✅ PASS |
| option_a/b/c/d | 0 / 167,559 | ✅ PASS |
| xp_transactions.user_id / amount | 0 / total | ✅ PASS |

## IRT Parameter Coverage (✅ PERFECT)

| Parameter | Coverage |
|---|---|
| irt_difficulty NOT NULL | 167,559 / 167,559 (100%) |
| irt_discrimination NOT NULL | 167,559 / 167,559 (100%) |
| irt_guessing NOT NULL | 167,559 / 167,559 (100%) |

## Topic Hierarchy Completeness

Distribution (14 distinct UPPERCASE values, total active topics):
- MATEMATIK: 40
- TDE: 12
- FIZIK / BIYOLOJI / TURKCE / KIMYA: 8 each
- TARIH / COGRAFYA: 7 each
- EDEBIYAT / SOSYAL / FEN / GENEL / GEOMETRI: 5 each
- (14 topics have NULL subject_area — uncategorized)

**Orphan questions** (primary_topic_id NOT IN topic_hierarchy): **0 / 167,559** ✅

## Phase 7 LLM Rationale — KRITIK BULGU

**MEMORY.md WRONG**: Claims 76,733 / 81,776 gold (93.8%) via Gemini Flash Batch API. Reality:

- auto_judged_high (gold) pool: **15,321 questions, 0 rationale** (0%)
- bronze_clean (curator queue): **197 questions, 0 rationale** (0%)
- pending: 32,726 / 36,433 (89.8%)
- rejected: 48,942 / 54,126 (90.4%)
- unverified: 77 / 61,482 (0.1%)

**Toplam rationale-eksik**: 85,814 / 167,559 = **51.2% missing**

**Root cause hipotezi**: Phase 7 batch görünüşe göre `pending` + `rejected` pool'lar üzerinde çalışmış — `auto_judged_high` (beta-ready gold) hedef ALINMAMIS. Audit `EVIDENCE_BASED III.N` aynı şeyi gösteriyordu: "100% NULL for Gold pool". MEMORY.md yanıltıcı bir başarı sayısı yazıyor.

## Beta-Ready Pool

`v_safe_for_beta` view: **12,362** ✅ (matches MEMORY)

## Migration Chain Integrity

- Current applied: `curator_audit_20260521` ✅
- Latest file: `20260521_s179_hot_path_indexes.py` (dry-run banner — NOT applied)
- Chain: consistent

## Index Health (S179 Hot-Path)

| Expected Index | Status |
|---|---|
| idx_qbank_status_active | ❌ NOT APPLIED |
| idx_qbank_active_created | ❌ NOT APPLIED |
| idx_qbank_beta_filter_rule | ❌ NOT APPLIED |
| idx_qbank_quality_subject_exam | ❌ NOT APPLIED |
| idx_qbank_created_by | ❌ NOT APPLIED |

**Bu DOĞRU davranış** — migration dry-run banner ile bekletiliyor (audit'in talimatı: EXPLAIN ANALYZE on staging first). Ama bu süre boyunca hot-path query'ler optimize değil.

## Re-OCR Debt

- `is_active=FALSE` questions: **20,275** (silinmiş/devre dışı)
- `pipeline_metadata.deletion_reason='low_confidence'` flag: 0 (track-edilmemiş)

**Hipotez**: 20,275 inactive'in bir kısmı re-OCR ile kurtarılabilir ama recovery markers yok. MEMORY'nin "1,521-2,511 potansiyel kurtarma" iddiası unsourced.

## XP Transaction Integrity (✅ CLEAN)

| Check | Result |
|---|---|
| student_id IS NULL | 0 |
| amount IS NULL | 0 |

## Top 10 P0 Data Risks

| # | Risk | Severity | Aksiyon |
|---|---|---|---|
| 1 | auto_judged_high gold pool 0 rationale (15,321 q) | 🔴 P0 | Phase 7 batch tekrar — beta launch için zorunlu |
| 2 | 85,814 question rationale-eksik (51.2%) | 🔴 P0 | Phase 7 kapsamı genişlet |
| 3 | MEMORY.md severely stale (+116% question count) | 🔴 P0 | MEMORY.md güncelle, single source of truth restore |
| 4 | S179 hot-path indexes NOT applied | 🟡 P1 | EXPLAIN ANALYZE staging → `alembic upgrade head` |
| 5 | 20,275 inactive question lacking recovery markers | 🟡 P1 | pipeline_metadata.deletion_reason backfill |
| 6 | 14 topic_hierarchy entries NULL subject_area | 🟢 P3 | Categorize uncategorized topics |
| 7 | unverified pool 99.9% rationale-eksik (61,405) | 🟡 P2 | Curator workflow scale-up |
| 8 | bronze_clean queue stuck at 197 (Curator backlog) | 🟢 P3 | Curator UI velocity verify |
| 9 | question_option_rationales drift +6.5% | 🟢 P3 | Identify source of new rationales |
| 10 | Question population doubled in 1 month — capacity? | 🟡 P2 | Verify query perf scales |

## Methodology

12 live DB queries run independently. Sample:
- `SELECT quality_review_status, COUNT(*) FROM question_bank WHERE is_active=TRUE GROUP BY 1`
- `LEFT JOIN question_option_rationales` for coverage breakdown
- `SELECT COUNT(*) FROM pg_indexes WHERE tablename='question_bank' AND indexname LIKE 'idx_qbank_%'`

All results re-verified by claude main thread via independent psql calls.
