# Design: PostgreSQL Question Import (77,336 → question_bank)

**Date:** 2026-03-04
**Status:** Approved
**Session:** 66

## Goal

Load 77,336 production questions from `d-dataset/eslesmis_sorucevap.jsonl` into the `question_bank` PostgreSQL table, with subject/exam_type classification inferred from book names.

## Architecture Decisions

### Target: `question_bank` table (QuestionBankItem model)
- Advanced model with 70+ fields, IRT 4PL, taxonomy, morphology
- Production-ready with composite indexes
- Used by all adaptive learning features

### Field Mapping

| JSONL Field | → question_bank Column | Transform |
|---|---|---|
| `text` | `question_text` | Direct |
| `options.A..E` | `option_a..option_e` | Dict destructure |
| `answer` | `correct_answer` | Direct (A-E) |
| `book_name` | `source_book` (NEW) | Direct |
| `page_number` | `source_page` (NEW) | Direct |
| `quality_score` | `quality_score` | Direct (0-100) |
| `confidence` | `calibration_quality_score` | Direct (0-1) |
| (inferred) | `exam_type` | From book_name patterns |
| (inferred) | `subject_area` | From book_name patterns |
| `question_number` | stored in pipeline_metadata | |
| remaining fields | `pipeline_metadata` (NEW JSONB) | All provenance |

### New Columns (Alembic migration)

```sql
ALTER TABLE question_bank ADD COLUMN source_book VARCHAR(300);
ALTER TABLE question_bank ADD COLUMN source_page INTEGER;
ALTER TABLE question_bank ADD COLUMN pipeline_metadata JSONB DEFAULT '{}';
```

### Subject Classification Rules

| Pattern (case-insensitive, Turkish-normalized) | Subject | Default Exam |
|---|---|---|
| matematik, problemler, sayılar | MATEMATIK | TYT |
| geometri, analitik geometri, üçgen, dörtgen | GEOMETRI | TYT |
| fizik | FIZIK | TYT |
| kimya | KIMYA | TYT |
| biyoloji | BIYOLOJI | TYT |
| edebiyat | EDEBIYAT | AYT |
| paragraf, türkçe, dil bilgisi, sözcük, anlam | TURKCE | TYT |
| tarih | TARIH | TYT |
| coğrafya | COGRAFYA | TYT |
| sosyal | SOSYAL | TYT |
| trigonometri, limit, türev, integral, logaritma, polinom, fonksiyon, diziler | MATEMATIK | AYT |
| katı cisimler | GEOMETRI | AYT |

**Exam type override:** If name contains `ayt` → AYT; `tyt` → TYT; both `tyt ayt` → TYT (default lower).

### ID Generation

Deterministic UUID from `uuid5(NAMESPACE, f"{book_name}|{page_number}|{question_number}")`.
Ensures idempotent re-imports (ON CONFLICT DO NOTHING).

### Import Strategy

1. Read JSONL line-by-line (memory efficient for 112MB)
2. Classify subject/exam_type
3. Generate deterministic UUID
4. Batch INSERT 1000 records per transaction
5. ON CONFLICT (id) DO NOTHING for idempotency
6. Progress bar + per-subject statistics

### Expected Outcome

- 77,336 rows in `question_bank`
- ~95%+ subject classification coverage
- All pipeline metadata preserved in JSONB
- Queryable via existing `/api/v1/questions` endpoints
- ~30s import time
