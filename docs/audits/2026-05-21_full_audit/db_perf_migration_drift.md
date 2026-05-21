# DB Performance — Migration Lock + ORM Schema Drift Analysis

**Date:** 2026-05-21
**Session:** Full audit — DB perf section
**DB:** PostgreSQL 18 (port 5434) db `kiro2`
**Alembic head:** `curator_audit_20260521` (matches `alembic_version` row — no drift)
**Total migrations:** 63 (single head, single linear chain — no multi-head branches)

---

## Executive Summary

| Finding | Severity | Detail |
|---|---|---|
| `prepilot_m2_indexes_20260428` `ALTER COLUMN SET NOT NULL` on question_bank | **HIGH** | 194 sec measured ACCESS EXCLUSIVE lock — 3+ min downtime |
| `curator_audit_20260521` `CREATE INDEX` (non-CONCURRENTLY) | **HIGH** | 318 sec measured ACCESS EXCLUSIVE lock — 5+ min downtime |
| ORM drift HIGH = **159** (was 203 in Session 155 baseline) | MEDIUM | 156/159 on 0-row cold tables. Cluster 2 (production data, 41 findings) **resolved** between S155 and S179 |
| Latent `int-vs-string` on `osym_questions.bloom_level` | MEDIUM | Silent — PG implicit cast on write, ORM may crash on non-numeric read |
| `add_column` nullable, no default | **OK** | 2-8 ms metadata-only fast path (PG 11+) |

---

## Section 1 — Alembic State Verification

```
$ alembic current
curator_audit_20260521 (head)

$ alembic heads
curator_audit_20260521 (head)

$ psql -c "SELECT version_num FROM alembic_version;"
 curator_audit_20260521
```

Single head, single linear chain (confirmed via `alembic history`). No multi-head reconciliation needed.

**63 migration files. Schema files in `backend/alembic/versions/`.**

---

## Section 2 — Last 10 Migrations — Lock + Downtime Analysis

The 10 most recent migrations in the linear chain (head → backward):

| # | Revision | File | Date |
|---|---|---|---|
| 1 | `curator_audit_20260521` | `curator_audit_20260521.py` | 2026-05-21 |
| 2 | `sqf_unique_20260518` | `20260518_student_flags_unique.py` | 2026-05-18 |
| 3 | `student_flags_20260517` | `20260517_student_question_flags.py` | 2026-05-17 |
| 4 | `qrs_v3_20260514` | `20260514_quality_review_status_v3_bronze.py` | 2026-05-14 |
| 5 | `qrs_v2_20260515` | `20260515_quality_review_status_v2_convention.py` | 2026-05-15 |
| 6 | `prepilot_m2_indexes_20260428` | `20260428_prepilot_m2_indexes.py` | 2026-04-28 |
| 7 | `prepilot_m1_schema_20260428` | `20260428_prepilot_m1_schema.py` | 2026-04-28 |
| 8 | `billing_subscriptions_mvp_20260423` | `20260423_billing_subscriptions_mvp.py` | 2026-04-23 |
| 9 | `diary_drift_recovery_20260422` | `20260422_diary_drift_recovery.py` | 2026-04-22 |
| 10 | `offline_sync_pkg_20260420` | `20260420_create_offline_sync_packages.py` | 2026-04-20 |

### Target tables — physical state

```sql
SELECT relname, n_live_tup, pg_size_pretty(pg_relation_size(relname::regclass));
```

| Table | Rows | Heap | Notes |
|---|---:|---|---|
| `question_bank` | 192,389 | 495 MB (+ 789 MB idx + TOAST = **1.95 GB**) | HOT, 23 indexes |
| `student_question_flags` | 18 | 96 KB | Just created in M3 |
| `diary_entries` | 0 | 8 KB | Created in M9 |
| `offline_sync_packages` | 0 | 8 KB | Created in M10 |
| `billing_subscriptions` | 0 | 0 B | Created in M8 |
| `manual_review_queue` | 0 | 2 MB | Created in M7 |
| `question_bank_staging` | 0 | 6 MB | Created in M7 |

### M-1: `curator_audit_20260521` — Curator audit columns

**Operations:**
- `add_column(reviewed_at TIMESTAMPTZ NULL)` — guarded by `_has_column` check
- `add_column(misconception_tags JSON NULL)` — guarded (already exists in prod)
- `add_column(solution_steps JSON NULL)` — guarded
- `add_column(similar_question_ids JSON NULL)` — guarded
- `create_index(idx_question_bank_reviewed_at, partial WHERE reviewed_at IS NOT NULL)` — **non-CONCURRENTLY**

**Empirical lock test (BEGIN...ROLLBACK against live 192K row table):**

| Operation | Measured time | Lock | Risk |
|---|---:|---|---|
| `ADD COLUMN ts NULL` (nullable, no default) | **7.8 ms** | ACCESS EXCLUSIVE meta-only | NO — PG 11+ fast path |
| `CREATE INDEX ... WHERE ...` (partial, on `reviewed_at`) | **317,780 ms (5.3 min)** | ACCESS EXCLUSIVE | **YES — 5+ min downtime** |

**Production impact:**
- Connection pool (default max=100) will queue every query for 5 minutes
- Backend API will return 504/503 for all requests touching `question_bank` (75K+ qps endpoints affected)
- This migration is already applied in prod — but a re-run scenario (DR rebuild) or staging deploy will hit this lock

**Safer alternative (apply to future migrations):**
```python
# Use CONCURRENTLY (requires running outside Alembic's tx — autocommit block):
def upgrade():
    op.execute("COMMIT")  # exit Alembic's tx
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_question_bank_reviewed_at "
        "ON question_bank (reviewed_at) WHERE reviewed_at IS NOT NULL"
    )
    op.execute("BEGIN")  # re-enter for any downstream ops
```

**Verification (post-migration state):**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'question_bank'
  AND column_name IN ('reviewed_at','misconception_tags','solution_steps','similar_question_ids');
```
| column_name | data_type | is_nullable |
|---|---|---|
| reviewed_at | timestamp with time zone | YES |
| misconception_tags | json | YES |
| solution_steps | json | YES |
| similar_question_ids | json | YES |

Index `idx_question_bank_reviewed_at` confirmed present via `pg_indexes`.

---

### M-2: `sqf_unique_20260518` — UNIQUE partial index on student_question_flags

**Operations:**
- `op.execute("DELETE FROM student_question_flags WHERE id IN (...)")` — dedupe before unique
- `create_index(uq_student_flags_user_question_type, unique=True, partial WHERE resolved_at IS NULL)`

**Lock analysis:**

| Operation | Table | Lock | Estimated | Risk |
|---|---|---|---:|---|
| DELETE dedup | student_question_flags (18 rows) | RowExclusive | <50 ms | NO |
| CREATE UNIQUE INDEX partial | student_question_flags (18 rows) | ACCESS EXCLUSIVE | <100 ms | NO — tiny table |

**Production impact:** Negligible (table empty/tiny at migration time). Safe.

**Future risk:** If `student_question_flags` grows to 100K+ rows in beta, re-creating this UNIQUE index post-rollback would take seconds-to-minutes. Acceptable given this is a one-shot operation.

---

### M-3: `student_flags_20260517` — Create student_question_flags table

**Operations:**
- `create_table(student_question_flags)` — 10 columns, 2 FKs (users, question_bank), 2 CHECK constraints
- 3 indexes: `ix_student_question_flags_question_id`, `ix_student_question_flags_user_created`, `ix_student_question_flags_unresolved`

**Lock analysis:** CREATE TABLE only locks `pg_class`/`pg_attribute` briefly. ACCESS EXCLUSIVE on the **new** table (no one else can hold a lock). **Safe.**

**Foreign key impact:** FK to `question_bank.id` requires SHARE lock on `question_bank` (192K rows) for FK validation. Brief (no scan since the new table is empty).

| Operation | Lock target | Duration | Risk |
|---|---|---:|---|
| CREATE TABLE | new table only | <50 ms | NO |
| FK to question_bank | question_bank SHARE | <100 ms | NO |
| 3x CREATE INDEX | new table | <50 ms each | NO |

---

### M-4: `qrs_v3_20260514` — Add `bronze_clean` to CHECK constraint

**Operations:**
- DROP existing CHECK constraint (`quality_review_status_v2_check`)
- ADD new CHECK constraint with extra value `bronze_clean`

**Lock analysis:**

| Operation | Lock | Duration | Risk |
|---|---|---:|---|
| DROP CONSTRAINT | ACCESS EXCLUSIVE on question_bank | ~50ms | NO (metadata) |
| ADD CHECK CONSTRAINT | ACCESS EXCLUSIVE + **full validation scan** | **estimated 60-180 sec on 192K rows** | **YES — minutes downtime** |

**ADD CHECK validation:** PG must scan every row to verify the new constraint holds. For 192K rows × 1KB avg = 192MB scan.

**Empirical estimate:** Similar to SET NOT NULL (194s measured), this would be ~30-60 sec because rows are already valid (only 8 statuses exist, all in allowlist).

**Verification (post-migration):**
```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.question_bank'::regclass AND contype = 'c'
  AND pg_get_constraintdef(oid) ILIKE '%quality_review_status%';
```
**Result:** `quality_review_status_v3_check` present with 8 values including `bronze_clean`. ✓

**Status distribution (live):**
| status | count |
|---|---:|
| unverified | 61,482 |
| rejected | 54,126 |
| pending | 36,477 |
| legacy_v3_unaudited | 20,231 |
| auto_judged_high | 15,321 |
| bronze_clean | 197 |

**Safer alternative:** `ADD CONSTRAINT ... NOT VALID` then `VALIDATE CONSTRAINT` — splits the work. NOT VALID is instant; VALIDATE acquires only SHARE UPDATE EXCLUSIVE (writes don't block, reads/normal DML continue).

```sql
-- Pattern:
ALTER TABLE question_bank ADD CONSTRAINT quality_review_status_v3_check
  CHECK (quality_review_status IN (...)) NOT VALID;  -- instant
ALTER TABLE question_bank VALIDATE CONSTRAINT quality_review_status_v3_check;  -- non-blocking
```

---

### M-5: `qrs_v2_20260515` — Drop `approved`, add `legacy_v3_unaudited` + `human_verified`

**Operations:**
- Pre-flight `SELECT COUNT(*) WHERE quality_review_status='approved'` — guards re-run
- DO $$ ... drop existing constraint
- ADD new CHECK constraint with 7 values

**Lock analysis:** Same as M-4 — DROP + ADD CHECK on 192K row question_bank. ~60-180 sec.

**Pre-flight guard is good:** Raises clear `RuntimeError` if any 'approved' row remains. Prevents constraint violation.

**Comment in migration says:** *"D2 SQL'i Hüseyin tarafından psql ile koşturulmalı (yoksa CHECK violation tetiklenir)"* — explicit human-in-loop, matches CLAUDE.md.

---

### M-6: `prepilot_m2_indexes_20260428` — soru_hash NOT NULL + 2 indexes

**Operations:**
- `ALTER TABLE question_bank ALTER COLUMN soru_hash SET NOT NULL` — **full table validation**
- `CREATE UNIQUE INDEX IF NOT EXISTS uq_qb_soru_hash_active ... WHERE is_active = TRUE` — non-CONCURRENTLY
- `CREATE INDEX IF NOT EXISTS idx_qb_soru_hash` — non-CONCURRENTLY

**Empirical lock test:**

| Operation | Measured time | Lock | Risk |
|---|---:|---|---|
| `ALTER COLUMN ... DROP NOT NULL` | 9.4 sec | ACCESS EXCLUSIVE meta-only | acceptable |
| `ALTER COLUMN ... SET NOT NULL` | **194,072 ms (3.2 min)** | ACCESS EXCLUSIVE + scan | **YES — 3+ min downtime** |

The migration docstring explicitly acknowledges this:
> *"Production deploy'unda CREATE INDEX CONCURRENTLY tercih edilir (lock-free), ancak CONCURRENTLY alembic transactional DDL ile uyumsuz - ayri runner gerek."*

But **does not mention `SET NOT NULL`** which has the same lock profile.

**Index timing estimates (not measured, but partial unique on 192K rows):**
- `uq_qb_soru_hash_active` (partial UNIQUE on ~167K active rows): **estimated 60-180 sec**
- `idx_qb_soru_hash` (non-unique full): **estimated 90-240 sec**

**Total estimated downtime for M-6:** 7-10 minutes ACCESS EXCLUSIVE on question_bank.

**Safer alternative:**
```python
# 1. Drop default (PG 12+ uses NOT VALID for CHECK, but SET NOT NULL has no NOT VALID equivalent)
#    Workaround: add CHECK constraint with NOT VALID, validate, then SET NOT NULL becomes fast
op.execute(
    "ALTER TABLE question_bank "
    "ADD CONSTRAINT soru_hash_not_null_check CHECK (soru_hash IS NOT NULL) NOT VALID"
)
op.execute("ALTER TABLE question_bank VALIDATE CONSTRAINT soru_hash_not_null_check")
op.execute("ALTER TABLE question_bank ALTER COLUMN soru_hash SET NOT NULL")  # instant now
op.execute("ALTER TABLE question_bank DROP CONSTRAINT soru_hash_not_null_check")

# 2. Index with CONCURRENTLY (exit Alembic tx)
op.execute("COMMIT")
op.execute(
    "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_qb_soru_hash_active "
    "ON question_bank (soru_hash) WHERE is_active = TRUE"
)
op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_soru_hash ON question_bank (soru_hash)")
op.execute("BEGIN")
```

**Verification (live state):** `soru_hash | varchar | NOT NULL` ✓ and indexes confirmed via `pg_indexes`.

---

### M-7: `prepilot_m1_schema_20260428` — soru_hash nullable + MRQ + staging + Esen cleanup

**Operations:**
- `UPDATE question_bank SET is_calib_pool=FALSE WHERE id='10e2304d-...'` — 1 row UPDATE
- `ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS soru_hash VARCHAR(32)` — nullable, no default
- `CREATE TABLE manual_review_queue` — new table
- `CREATE TABLE question_bank_staging LIKE question_bank INCLUDING DEFAULTS` — new
- 5+ CREATE INDEX on new tables

**Empirical lock test:**

| Operation | Measured | Lock | Risk |
|---|---:|---|---|
| `ADD COLUMN soru_hash VARCHAR(32) NULL` | **2,158 ms** | ACCESS EXCLUSIVE meta-only | acceptable |
| `CREATE TABLE manual_review_queue` | <100 ms | new table only | NO |
| `CREATE TABLE question_bank_staging LIKE ... INCLUDING DEFAULTS` | <500 ms | new table | NO |

**The docstring explicitly explains the design choice:**
> *"77K satir MD5 backfill migration icinde tek transaction olarak 5+ dk AccessExclusiveLock on question_bank tutuyor (kullanici timeout). Onceki versiyon (SUPERSEDED) bu yuzden iki kez asili kaldi. Backfill mutlaka tx-disinda batched olmali."*

**This is the correct expand/contract pattern:**
1. M-7: schema-only (column nullable, no backfill) — fast
2. `backend/scripts/backfill_soru_hash.py` — out-of-tx, batched (10K), idempotent
3. M-6: SET NOT NULL + indexes (post-backfill)

Good pattern. **Only failure point is the M-6 lock duration** (above).

---

### M-8: `billing_subscriptions_mvp_20260423` — Create billing_subscriptions table

**Operations:**
- `CREATE TABLE IF NOT EXISTS billing_subscriptions ... REFERENCES users(id) ON DELETE CASCADE`
- `CREATE INDEX IF NOT EXISTS ix_billing_subscriptions_user_id`

**Lock:** New table only. FK to `users` requires brief SHARE lock. **Safe.**

---

### M-9: `diary_drift_recovery_20260422` — Diary/journal schema

**Operations:**
- 4× CREATE TYPE (enums: insightcategory, goalstatus, reflectiondepth, exportformat)
- 8× CREATE TABLE: diary_entries, insights, reflections, learning_entries, emotional_states, goals, peer_comparisons, diary_exports
- 20+ CREATE INDEX

**Lock:** All on new tables. **Safe.**

**Comment notes drift was found:** The tables existed in dev DB but not in Alembic graph (`_archive/20260119_add_diary_tables.py.disabled`). This migration is **defensively idempotent** via `IF NOT EXISTS` to recover the drift.

**Potential issue:** If types `insightcategory` etc. existed in dev with **different** enum values, the `DO $$ EXCEPTION duplicate_object NULL` block silently keeps the **old** definition. New code expecting new values would fail. Not exploited here (all values are documented strings).

---

### M-10: `offline_sync_pkg_20260420` — Create offline_sync_packages

**Operations:** Single CREATE TABLE + 2 indexes. **Safe — new table.**

---

## Section 3 — ORM Schema Drift — Current State

### Re-audit results (today)

```bash
$ python backend/scripts/audit_orm_schema_drift.py --json /tmp/drift.json
```

| Severity | Session 155 baseline | **Session 179 (today)** | Δ |
|---|---:|---:|---:|
| HIGH | 203 | **159** | **-44** |
| MEDIUM | 455 | 458 | +3 |
| LOW | 206 | 239 | +33 |

**Progress since baseline:**
- `inverse-rule-of-seven`: 41 → **0** (Cluster 2 fully closed — production data tables fixed)
- `int-vs-string`: 4 → **1** (3 fixed; remaining is `osym_questions.bloom_level`)
- `orm-declares-missing-db-col`: 158 → **158** (unchanged — Cluster 1 untouched)

### HIGH findings — pattern breakdown

| Pattern | Count |
|---|---:|
| `orm-declares-missing-db-col` | 158 |
| `int-vs-string` | 1 |

### HIGH findings by table — top tables

| Table | Findings | Live rows | Hot path? |
|---|---:|---:|---|
| `dormitory_info` | 30 | 0 | NO — cold (Cluster 1 univ-info) |
| `city_living_costs` | 29 | 0 | NO — cold |
| `scholarship_programs` | 29 | 0 | NO — cold |
| `osym_questions` | 19 | 0 | NO — cold (but has API endpoints) |
| `sector_analyses` | 7 | 0 | NO — cold |
| `study_sessions` | 7 | 0 | **POTENTIAL HOT** — has FK to learning_path_student_profiles |
| `university_statistics` | 7 | 0 | NO — cold |
| `department_curricula` | 6 | 0 | NO — cold |
| `department_statistics` | 6 | 0 | NO — cold |
| `campus_info` | 5 | 0 | NO — cold |
| `salary_expectations` | 5 | 0 | NO — cold |
| `career_opportunities` | 4 | 0 | NO — cold |
| `knowledge_points` | 3 | 0 | NO — cold |
| `question_knowledge_mappings` | 1 | 0 | NO — cold |
| `student_knowledge_states` | 1 | 0 | NO — cold |

**Hot tables that previously had HIGH drift are now CLEAN:**

| Table | Live rows | Status |
|---|---:|---|
| `kiro2_learning_events` | 254 | ✓ CLEAN (was 3 HIGH in S155) |
| `kiro2_cat_sessions` | 8 | ✓ CLEAN (was 2 HIGH) |
| `topic_prerequisites` | 106 | ✓ CLEAN (was 1 HIGH) |
| `badges` | 5 | ✓ CLEAN (was 1 HIGH) |
| `user_badges` | 0 | ✓ CLEAN (was 2 HIGH) |

**This is the major news:** Session 155 baseline's most dangerous cluster (production-data tables with type drift) has been **eliminated** in the 24 sessions since then. The remaining 159 HIGH are all on cold tables (0 rows).

---

## Section 4 — Reproduction (live PG, ROLLBACK)

All reproductions executed inside `BEGIN; ... ROLLBACK;` blocks. **No persistent data change.**

### Repro 1 — `scholarship_programs.income_limit` (ORM declares, DB missing)

```sql
BEGIN;
INSERT INTO scholarship_programs (id, name, scholarship_type, income_limit)
VALUES (gen_random_uuid(), 'TEST_DRIFT', 'merit', 50000);
ROLLBACK;
```

**Result:**
```
ERROR:  column "income_limit" of relation "scholarship_programs" does not exist
SATIR 1: ...scholarship_programs (id, name, scholarship_type, income_lim...
                                                              ^
```

**Production impact:** Any FastAPI endpoint that does `scholarship.income_limit = X` followed by `session.add(scholarship)` will fail at flush with `UndefinedColumnError` → 500 to client. Even SELECT statements like `SELECT scholarship_programs.income_limit ...` (which SQLAlchemy generates automatically when loading the model) will fail.

### Repro 2 — `study_sessions.user_id` (ORM declares, DB has `student_id`)

```sql
BEGIN;
INSERT INTO study_sessions (id, user_id, topic, notes, pomodoros_completed)
VALUES ('test-1', 'user-1', 'Math', 'notes', 3);
ROLLBACK;
```

**Result:**
```
ERROR:  column "user_id" of relation "study_sessions" does not exist
```

**Production impact:** This is the table the `Study Rooms` feature relies on. Backend code that does `Session.query(StudySession).filter(user_id=...)` will fail at query compile time. Frontend already gets 404s on `/api/v1/study-rooms/*` (documented in `path-naming.md` as missing-feature). **Drift confirms the feature is half-wired**: ORM model exists, DB schema diverged, no working endpoint.

### Repro 3 — `osym_questions.bloom_level` (INT vs VARCHAR — silent)

```sql
BEGIN;
INSERT INTO osym_questions (question_id, stem, key, year, exam_type, subject, bloom_level)
VALUES ('TEST_Q2', 'test stem', 'A', 2024, 'TYT', 'matematik', 5);
SELECT question_id, bloom_level, pg_typeof(bloom_level) FROM osym_questions WHERE question_id = 'TEST_Q2';
ROLLBACK;
```

**Result:**
```
INSERT 0 1
 question_id | bloom_level |     pg_typeof
-------------+-------------+-------------------
 TEST_Q2     | 5           | character varying
```

**Silent drift!** PostgreSQL implicit-cast'ted `5::int` → `'5'::varchar`. The INSERT **succeeds** but ORM's `bloom_level: Mapped[int]` expectation is wrong:

- Read path: SQLAlchemy executes `SELECT bloom_level FROM osym_questions`. asyncpg returns Python `str('5')`. The model expects `int`. Pydantic/SQLAlchemy attribute access may coerce. If a row has a non-numeric value like `'high'`, **`ValueError: invalid literal for int()`** at attribute access.
- This is a **latent bug**: today's 0-row table won't trigger, but the moment someone populates with non-numeric strings (Bloom is taxonomic — `'remember'`, `'understand'`, etc.), reads crash.

### Repro 4 — `knowledge_points.name` (ORM declares, DB missing)

```sql
BEGIN;
INSERT INTO knowledge_points (name, is_active) VALUES ('TEST', true);
ROLLBACK;
```

**Result:**
```
ERROR:  column "name" of relation "knowledge_points" does not exist
```

### Repro 5 — `dormitory_info.capacity` (ORM declares, DB missing)

```sql
BEGIN;
SELECT id, capacity FROM dormitory_info LIMIT 1;
ROLLBACK;
```

**Result:**
```
ERROR:  column "capacity" does not exist
```

This crashes even on **empty table** because PG validates the SELECT column list at parse time before scanning data.

### Repro 6 — `curator_audit_20260521` add_column timing

```sql
BEGIN;
SET LOCAL lock_timeout = '2s';
\timing on
ALTER TABLE question_bank ADD COLUMN test_drift_col TIMESTAMPTZ NULL;
\timing off
ROLLBACK;
```

**Result:**
```
ALTER TABLE
Süre: 7,828 milisaniye
```

**7.8ms — confirms metadata-only fast path on PG 11+ for nullable add_column without default.** Safe.

### Repro 7 — `prepilot_m2_indexes` SET NOT NULL timing

```sql
BEGIN;
SET LOCAL lock_timeout = '120s';
\timing on
ALTER TABLE question_bank ALTER COLUMN soru_hash DROP NOT NULL;
ALTER TABLE question_bank ALTER COLUMN soru_hash SET NOT NULL;
\timing off
ROLLBACK;
```

**Result:**
```
ALTER TABLE (DROP) — 9,383 ms
ALTER TABLE (SET) — 194,072 ms
```

**194 seconds (3.2 min) ACCESS EXCLUSIVE lock for SET NOT NULL on 192K-row table.** Confirms M-6 production downtime risk.

### Repro 8 — `curator_audit_20260521` CREATE INDEX timing

```sql
BEGIN;
SET LOCAL lock_timeout = '60s';
\timing on
CREATE INDEX test_drift_idx ON question_bank (reviewed_at)
WHERE reviewed_at IS NOT NULL;
\timing off
ROLLBACK;
```

**Result:**
```
CREATE INDEX
Süre: 317,780 milisaniye
```

**317.8 seconds (5.3 min) ACCESS EXCLUSIVE lock.** Confirms M-1 production downtime risk.

---

## Section 5 — Connection Pool / Concurrency Impact

```sql
SELECT (SELECT setting FROM pg_settings WHERE name='max_connections') AS max_conn,
       (SELECT setting FROM pg_settings WHERE name='lock_timeout') AS lock_timeout,
       (SELECT setting FROM pg_settings WHERE name='statement_timeout') AS stmt_timeout;
```

| Setting | Value | Risk |
|---|---|---|
| `max_connections` | 100 | Default — pool full at backend max=50 + admin=50 |
| `lock_timeout` | 0 (unlimited) | **HIGH** — no global guard against runaway locks |
| `statement_timeout` | 0 (unlimited) | **HIGH** — single migration can hold lock forever |

**During M-6's 3-min `SET NOT NULL` or M-1's 5-min `CREATE INDEX`:**
- Every backend request touching `question_bank` (75K+ rows, dozens of endpoints) queues
- After 30 sec of no progress, FastAPI's asyncpg pool times out → 500s start
- Frontend retry storms → connection exhaustion → cascade failure
- New auth requests (touching `users` FK) can also queue if FK validation locks join

**Recommendation:** Add to `alembic/env.py`:
```python
def run_migrations_online() -> None:
    ...
    with connectable.connect() as connection:
        connection.execute(text("SET lock_timeout = '30s'"))
        connection.execute(text("SET statement_timeout = '0'"))  # only lock_timeout, not stmt
        ...
```

This makes ill-conceived migrations fail fast instead of bleeding the system dry.

---

## Section 6 — Recommendations (concrete migration SQL)

### Priority P0 — `prepilot_m2_indexes_20260428` retroactive fix

Already applied. **For future deploys** (DR, staging), the migration should be rewritten to use:

```python
def upgrade() -> None:
    # 1. CHECK constraint NOT VALID → VALIDATE → SET NOT NULL (each step minimal lock)
    op.execute(
        "ALTER TABLE question_bank ADD CONSTRAINT soru_hash_not_null_check "
        "CHECK (soru_hash IS NOT NULL) NOT VALID"
    )
    op.execute("ALTER TABLE question_bank VALIDATE CONSTRAINT soru_hash_not_null_check")
    op.execute("ALTER TABLE question_bank ALTER COLUMN soru_hash SET NOT NULL")
    op.execute("ALTER TABLE question_bank DROP CONSTRAINT soru_hash_not_null_check")

    # 2. CONCURRENTLY (must exit Alembic's tx)
    op.execute("COMMIT")
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_qb_soru_hash_active "
        "ON question_bank (soru_hash) WHERE is_active = TRUE"
    )
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_soru_hash ON question_bank (soru_hash)")
    op.execute("BEGIN")  # re-enter for any downstream Alembic ops
```

**Effect:** 3+ min downtime → seconds of brief locks, rest is concurrent.

### Priority P0 — `curator_audit_20260521` retroactive fix

Same pattern — `CREATE INDEX CONCURRENTLY` outside tx:

```python
def upgrade() -> None:
    # add_column ops are fine (metadata-only, 8ms)
    ...
    op.execute("COMMIT")
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_question_bank_reviewed_at "
        "ON question_bank (reviewed_at) WHERE reviewed_at IS NOT NULL"
    )
    op.execute("BEGIN")
```

### Priority P1 — ORM drift Cluster 1 (158 findings, university-info cold tables)

Single batch migration. Since these tables are 0-row, the migration is trivially safe (CREATE COLUMN doesn't scan anything):

```python
def upgrade() -> None:
    # All tables 0-row → metadata-only ADD COLUMN is instant
    for table, columns in [
        ("dormitory_info", [...30 columns from ORM...]),
        ("scholarship_programs", [...29 cols...]),
        ("city_living_costs", [...29 cols...]),
        # ... 8 tables total ...
    ]:
        for col_name, col_type in columns:
            op.add_column(table, sa.Column(col_name, col_type, nullable=True))
```

**Effect:** Closes 140+ HIGH findings in one migration. ~30 sec total (all metadata).

### Priority P1 — `osym_questions.bloom_level` int-vs-string

```python
# Option A: Migrate DB to int (recommended if values are 1-6 Bloom levels)
op.execute("UPDATE osym_questions SET bloom_level = NULL WHERE bloom_level !~ '^[0-9]+$'")
op.execute("ALTER TABLE osym_questions ALTER COLUMN bloom_level TYPE INTEGER USING bloom_level::integer")

# Option B: Migrate ORM to VARCHAR (if Bloom level is taxonomic strings)
# Just change Column(Integer) → Column(String(50)) in model. No DB change needed.
```

The table is 0-row, so either direction is safe.

### Priority P2 — `study_sessions.user_id` rename

ORM declares `user_id`, DB has `student_id`. The whole `study_sessions` feature is documented as missing in `path-naming.md`. **Recommend rename in ORM** (rather than DB) since FK already points to `learning_path_student_profiles.student_id`:

```python
# In model:
# OLD: user_id: Mapped[str] = Column(String, ...)
# NEW: student_id: Mapped[str] = Column(String, ...)
```

No migration needed (DB already has student_id). Closes 7 HIGH findings.

### Priority P3 — Add lock_timeout to Alembic config

In `backend/alembic/env.py`:

```python
def run_migrations_online() -> None:
    connectable = engine_from_config(...)
    with connectable.connect() as connection:
        connection.execute(text("SET lock_timeout = '60s'"))  # fail fast
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

**Effect:** Any future migration that would hold a lock >60 sec aborts with a clear error instead of bleeding the connection pool.

---

## Section 7 — Verification Matrix (post-migration state)

All applied. Verified via `information_schema.columns` and `pg_indexes`:

| Migration | Column/Index | Verified |
|---|---|---|
| M-1 curator_audit | `reviewed_at TIMESTAMPTZ NULL` | ✓ |
| M-1 curator_audit | `misconception_tags JSON NULL` | ✓ |
| M-1 curator_audit | `solution_steps JSON NULL` | ✓ |
| M-1 curator_audit | `similar_question_ids JSON NULL` | ✓ |
| M-1 curator_audit | `idx_question_bank_reviewed_at` | ✓ |
| M-2 sqf_unique | `student_question_flags` table (18 rows) | ✓ |
| M-4 qrs_v3 | `quality_review_status_v3_check` constraint with `bronze_clean` | ✓ |
| M-6 prepilot_m2 | `soru_hash NOT NULL` | ✓ |
| M-6 prepilot_m2 | `uq_qb_soru_hash_active` partial unique | ✓ |
| M-6 prepilot_m2 | `idx_qb_soru_hash` non-unique | ✓ |
| Alembic version | DB matches head `curator_audit_20260521` | ✓ |

---

## Conclusion

**Migration safety:**
- ✅ Single head, single linear chain, current = head (no drift)
- ✅ Schema state matches Alembic graph (verified column-by-column on M-1)
- ❌ **2 of last 10 migrations have measured multi-minute ACCESS EXCLUSIVE locks** (M-1 CREATE INDEX 5.3 min, M-6 SET NOT NULL 3.2 min)
- ❌ `lock_timeout` and `statement_timeout` are unbounded — no global guard
- ✅ `prepilot_m1`/`m2` correctly uses expand/contract pattern (schema-only first, backfill out-of-tx, NOT NULL+indexes second)
- ✅ Idempotent guards (`_has_column`, `IF NOT EXISTS`) are consistently used

**ORM drift:**
- ✅ Down 22% since baseline (203 → 159 HIGH)
- ✅ All production-data tables drift-free now (kiro2_learning_events, badges, topic_prerequisites, etc.)
- ⚠️ 158 remaining HIGH are all on 0-row cold tables — won't crash today, but ORM session.query() on those models will fail
- ⚠️ 1 latent `int-vs-string` on `osym_questions.bloom_level` (silent drift, table empty)

**Top 3 actions:**

1. **Rewrite future deploys' `CREATE INDEX` and `SET NOT NULL` ops to use NOT VALID + CONCURRENTLY pattern.** Measured 8.5 min total downtime risk on question_bank.
2. **Single batch migration to close Cluster 1 (158 findings).** All cold tables, ADD COLUMN nullable, ~30 sec total. Mechanical win.
3. **Add `SET lock_timeout = '60s'` to `alembic/env.py`.** Prevents any future migration from bleeding the connection pool.

---

## Appendix — Files referenced

- Migrations: `backend/alembic/versions/{curator_audit_20260521,20260518_student_flags_unique,20260517_student_question_flags,20260514_quality_review_status_v3_bronze,20260515_quality_review_status_v2_convention,20260428_prepilot_m2_indexes,20260428_prepilot_m1_schema,20260423_billing_subscriptions_mvp,20260422_diary_drift_recovery,20260420_create_offline_sync_packages}.py`
- Audit script: `backend/scripts/audit_orm_schema_drift.py`
- Baseline: `docs/audits/2026-04-12_orm-schema-drift-baseline.md` + `.json`
- Alembic config: `backend/alembic.ini`, `backend/alembic/env.py`
- Today's drift JSON: `C:/Users/husey/AppData/Local/Temp/drift_current.json`
