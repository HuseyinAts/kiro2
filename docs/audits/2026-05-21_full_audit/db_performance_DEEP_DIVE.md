# KIRO2 DB Performance Deep Dive — 2026-05-21

**Yaklaşım:** Gerçek `EXPLAIN ANALYZE` + `pg_stat_*` runtime data + concrete fix diffs.
**Audit yöntemi:** Read-only `psql` queries on production DB (kiro2, port 5434, native Windows PostgreSQL 18, but reports as PG15 catalog).

---

## 1. PostgreSQL Configuration — KRİTİK CONFIG GAP'LERI

| Parameter | Mevcut | Production Target | Etki | Fix |
|---|---|---|---|---|
| `shared_buffers` | **128MB** (16384 × 8KB) | 2-4GB (RAM %25) | 🔴 **Cache hit %56** (target %95) | `shared_buffers = 2GB` |
| `effective_cache_size` | 4GB (524288 × 8KB) | RAM × 0.75 | OK ama orantısız | `effective_cache_size = 6GB` |
| `work_mem` | **4MB** | 16-64MB | 🔴 **1.7GB temp files**, sort disk'e döküyor | `work_mem = 32MB` |
| `maintenance_work_mem` | 64MB | 256-512MB | VACUUM/CREATE INDEX yavaş | `maintenance_work_mem = 512MB` |
| `max_connections` | **100** | 200 | 🔴 **Backend pool 150 max → exhaustion** | `max_connections = 200` veya PgBouncer |
| `random_page_cost` | **4.0** (HDD) | 1.1-2.0 (SSD) | 🔴 Planner SSD'yi HDD sanıyor → bad plan | `random_page_cost = 1.1` |
| `default_statistics_target` | 100 | 1000 (büyük tablolar için) | Cardinality estimate hatalı | `default_statistics_target = 500` |
| `effective_io_concurrency` | 16 | 200 (SSD) | Async I/O yetersiz | `effective_io_concurrency = 200` |
| `jit` | on | on | OK | — |
| `max_wal_size` | 1GB | 2-4GB | Bulk insert checkpoint pressure | `max_wal_size = 4GB` |

**Verify komutu:**
```bash
PGPASSWORD=1470 psql -p 5434 -d kiro2 -c "
SELECT name, setting, unit FROM pg_settings
WHERE name IN ('shared_buffers','work_mem','random_page_cost',...);"
```

**Cache hit hesabı (kanıt):**
```
blks_hit:  284,417,813
blks_read: 222,178,708 (disk)
cache_hit = 284M / (284M+222M) = 56.14%
```

**Disk pressure kanıtı:**
- 222M block × 8KB = **1.78 TB cumulative disk read** since DB start
- 60 temp files, 1.7GB temp_bytes → **work_mem disk spill** (production'da sort/hash sürekli disk'e döküyor)
- Rollback rate: **18%** (1082/5945) — transaction error pattern

---

## 2. Missing Indexes — KANIT EDİLMİŞ EXPLAIN ANALYZE İLE

### 🔴 F-DB-1: `idx_qb_review_status_active` EKSİK — Curator queue 156ms tam tarama

**Endpoint:** `GET /api/v1/curator/queue` (Session 178 hot path, daily curator tool)

**Actual SQL:**
```sql
SELECT id, subject_area, exam_type, quality_review_status
FROM question_bank
WHERE is_active = TRUE AND quality_review_status = 'bronze_clean'
ORDER BY md5(id::text) LIMIT 50;
```

**EXPLAIN ANALYZE actual output:**
```
Limit  (cost=65381.37..65387.19 rows=50)
  (actual time=148.796..156.771 rows=50.00 loops=1)
  Buffers: shared hit=15646 read=47833
  ->  Gather Merge  (Workers Planned: 2, Launched: 2)
    ->  Sort  Sort Key: (md5((id)::text)) [Memory: 36kB]
      ->  Parallel Seq Scan on question_bank
            (cost=0.00..64379.46 rows=63 width=91)
            (actual time=7.124..121.703 rows=65.67 loops=3)
          Filter: (is_active AND quality_review_status = 'bronze_clean')
          Rows Removed by Filter: 62,546
          Buffers: shared hit=15568 read=47833
Planning Time: 10.086 ms
Execution Time: 156.809 ms
```

**Numerical evidence:**
- 192K row table → **62,546 filter eliminated** per parallel worker × 3 workers = 187K rows scanned
- 47,833 disk block read = **~370 MB I/O per query**
- Cache hit per query: 15,646 / 63,479 = **24.6%** (terrible)
- Execution: **156.8ms** (P95'te muhtemelen >500ms)

**Production scenarios:**
- 100 curator load (gelecek 1K student senaryo): 156ms × 100 = **15.6s aggregate queue load**
- Daily curator throughput (30-50/gün × 5 saniye refresh): 200-300 queue calls/day
- Beta için marjinal acceptable; **100+ curator için P0**

**Fix:**
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_review_status_active
ON question_bank (quality_review_status, is_active)
WHERE is_active = TRUE;
```

**Expected after fix:**
- Plan: `Index Range Scan on idx_qb_review_status_active`
- Execution: **<5ms** (bronze_clean = 197 rows, direkt yakalanır)
- Buffers: ~50 read (HOT cache)
- Speedup: **~30x**

**Reproduction verify:**
```bash
# Before:
EXPLAIN (ANALYZE) ... WHERE quality_review_status = 'bronze_clean' AND is_active = TRUE LIMIT 50;
# After:
CREATE INDEX ...
ANALYZE question_bank;
EXPLAIN (ANALYZE) ...  # → Index Scan, <5ms
```

---

### 🔴 F-DB-2: `idx_qb_beta_filter_rule` EKSİK — JSONB extract seq scan (R1 / Gold filter)

**Endpoint:** R1 restore script + Curator stats endpoint + her gold pool sorgusu

**Actual SQL:**
```sql
SELECT id FROM question_bank
WHERE is_active = TRUE
  AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R4_rule_based_gold'
LIMIT 100;
```

**EXPLAIN ANALYZE actual:**
```
Limit  (cost=0.00..8070.08 rows=100) (actual time=1.778..9.786 rows=100)
  Buffers: shared hit=407 read=409
  ->  Seq Scan on question_bank  (cost=0.00..67627.26 rows=838)
        Filter: (is_active AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R4_rule_based_gold')
        Rows Removed by Filter: 129
        Buffers: shared hit=407 read=409
Planning Time: 11.802 ms
Execution Time: 9.903 ms
```

**Numerical evidence:**
- LIMIT 100 erken çıkıyor → 9.9ms
- LIMIT olmadan full scan = ~67,627 cost = **estimated ~700ms** for 81K row result
- Cardinality estimate: 838 rows (gerçek 81,776) → **97x underestimate**
- Statistics target çok düşük JSONB için

**Production scenarios:**
- R1 restore --apply: tüm gold pool tarar → 700ms × 1 = 700ms (OK)
- v_safe_for_beta view query: aynı pattern, sık çağrılır
- Curator stats: aynı pattern
- Phase 6 kNN pre-filter: aynı pattern

**Fix:**
```sql
-- Expression index for JSONB rule field
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_beta_filter_rule
ON question_bank ((pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule'))
WHERE is_active = TRUE;

-- Veya GIN index for general JSONB query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_pipeline_metadata_gin
ON question_bank USING gin ((pipeline_metadata::jsonb))
WHERE is_active = TRUE;
```

**Expected after fix:** Execution <50ms for full gold pool scan (vs 700ms estimated)

---

### ⚠️ F-DB-3: `idx_qbank_embedding_hnsw` İŞ GÖRÜYOR — Pre-filter inefficiency

**EXPLAIN ANALYZE:**
```
Limit  (cost=1090.15..1131.32 rows=10) (actual time=12.806..13.729 rows=10)
  Buffers: shared hit=242 read=1120
  InitPlan 1: Seq Scan (LIMIT 1)
  InitPlan 2: Seq Scan (LIMIT 1)
  ->  Index Scan using idx_qbank_embedding_hnsw on question_bank
        Order By: (embedding <=> (InitPlan 2).col1)
        Filter: (embedding IS NOT NULL AND is_active)
        Index Searches: 1
Execution Time: 13.986 ms
```

**Bulgu:** HNSW kendisi 14ms harika ama 2 ayrı `InitPlan` `Seq Scan` her InitPlan 0.01ms (negligible). Production'da bilinen `embedding` parameter pass edilirse 14ms tek query.

**Status:** ✅ NO FIX NEEDED (Phase 6 production ready)

---

## 3. Duplicate / Redundant Indexes — WRITE OVERHEAD

**`question_bank` üzerinde 23 index. 6 tanesi duplicate/subset:**

| Drop adayı | Sebep | Boyut tasarrufu |
|---|---|---|
| `idx_qbank_topic` | `idx_qb_primary_topic` (WHERE NOT NULL) daha optimal | 5.9MB |
| `idx_qbank_calibrated` | `idx_qbank_calibrated_active` superset (is_calibrated dahil) | 4MB |
| `idx_qbank_subject` | `idx_qb_cat_subject_active` (functional + partial) daha optimal | ~6MB |
| `idx_qb_soru_hash` | `uq_qb_soru_hash_active` (unique partial) yeterli | 17MB |
| `idx_qbank_grade` | 0 scan, kullanılmıyor | 4.7MB |
| `idx_qbank_text_gin` | 0 scan, full-text search aktif değil | **62MB** |

**Toplam tasarruf:** **~100MB index footprint + her INSERT/UPDATE'te 6 daha az index sync**

**`questions` (LEGACY BOŞ) tablo üzerinde 4 index, hepsi 0 scan:**
- `idx_questions_text_search` 23MB
- `idx_questions_text_gin` 6.5MB
- `idx_questions_topic_search` 6.2MB
- `questions_pkey` 5.7MB
- **Toplam 41.4MB israf, tablo boş — TABLO + indeksleri DROP**

**Fix script:**
```sql
BEGIN;
-- Verify low impact first
DROP INDEX IF EXISTS idx_qbank_topic;
DROP INDEX IF EXISTS idx_qbank_calibrated;
DROP INDEX IF EXISTS idx_qbank_subject;
DROP INDEX IF EXISTS idx_qb_soru_hash;
DROP INDEX IF EXISTS idx_qbank_grade;
DROP INDEX IF EXISTS idx_qbank_text_gin;  -- 62MB!

-- Legacy questions table cleanup
DROP TABLE IF EXISTS questions CASCADE;
COMMIT;
```

**Write performance impact (estimated):**
- Each `INSERT` into `question_bank`: 23 → 17 indexes = **26% faster** insert
- Each `UPDATE` (curator verdict, R1 restore): aynı oran

---

## 4. Sequential Scan Damage — RUNTIME EVIDENCE

```sql
SELECT relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables WHERE n_live_tup > 5000
ORDER BY seq_tup_read DESC;
```

| Table | seq_scan | seq_tup_read | idx_scan | Damage |
|---|---|---|---|---|
| `question_bank` | 654 | **46,226,499** | 245,973 | 70K avg per seq scan! |
| `question_option_rationales` | 42 | 2,123,685 | 2,227,090 | 50K avg per seq scan |
| `question_math` | 8 | 91,101 | 30,587 | 11K avg per seq scan |

**Yorum:**
- `question_bank` 192K row × 654 seq scan = **125M row scan equivalent** (~6.5x table size)
- Çoğu sorgu index kullanıyor (`idx_scan = 245K`) ama 654 query tam tarama yapmış
- Bu 654 query muhtemelen `quality_review_status` / `pipeline_metadata::jsonb` filter'ları (F-DB-1, F-DB-2 ile çözülür)

---

## 5. pg_stat_statements EKSİK — Slow Query Tracking PASİF

**Bulgu:**
```bash
$ psql -c "SELECT * FROM pg_stat_statements LIMIT 1"
ERROR: pg_stat_statements must be loaded via "shared_preload_libraries"
```

Extension install edilmiş (`extversion = 1.12`) ama `postgresql.conf`'ta yüklenmemiş. Slow query analysis imkansız.

**Fix:** `postgresql.conf`:
```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 5000
```
+ PostgreSQL restart.

---

## 6. Vacuum & Bloat — RUNTIME

| Table | live_rows | dead_rows | dead_pct | Last autovacuum |
|---|---|---|---|---|
| `question_bank` | 192,389 | 12,188 | 6.3% | 2026-05-21 14:16 (1 saat önce) |

**Status:** ✅ Vacuum sağlıklı çalışıyor. R1 restore 15K UPDATE sonrası autovacuum 3 kez çalışmış.

**Öneri:** Hot tables için tuning:
```sql
ALTER TABLE question_bank SET (
  autovacuum_vacuum_scale_factor = 0.05,  -- default 0.2
  autovacuum_analyze_scale_factor = 0.02  -- default 0.1
);
```

---

## 7. Production Scenarios — CONCRETE LATENCY MODEL

### Senaryo A: 100 concurrent curator (gelecek)
- Queue call 156ms × 100 = aggregate **15.6s/s queue load**
- F-DB-1 fix sonrası: 5ms × 100 = **500ms/s** (31x improvement)

### Senaryo B: 1 öğrenci quiz submit (BKT + IRT + FSRS write)
**Şu an (tahmin, EXPLAIN gerek):**
- BKTState UPDATE: 5-10ms (PK update, OK)
- IRT theta UPDATE: 5-10ms (PK update, OK)
- FSRSCard UPDATE: 5-10ms
- Question recent_responses SELECT: ~50ms (eğer index varsa, kontrol gerek)
- Total: **~75-100ms per submit** (acceptable)

### Senaryo C: R1 restore --apply (Session 178 oldu)
- WHERE clause F-DB-2 olmadan: 700ms scan
- Sonrası bulk UPDATE 15,321 row: 692.6s actual (~22 row/s — slow)
- F-DB-2 fix sonrası: aynı, çünkü UPDATE WHERE clause performansı dominant değil

### Senaryo D: Daily learning_path/today (her öğrenci açılışta)
**Bilinmeyen — EXPLAIN ANALYZE yapılmadı (next session)**

### Senaryo E: pgvector kNN (Phase 6, similar_questions)
- **14ms 10-NN** — beta-ready ve scaleable
- HNSW index ef_construction=200 m=16 — uygun

---

## 8. Connection Pool Risk — KANITLI

**Mevcut state:**
- PG `max_connections = 100`
- Backend `database.py:153` → `pool_size=50, max_overflow=100` (max 150 ask)
- Şu an `numbackends = 3` (idle)

**Production scenario (100 öğrenci concurrent):**
1. Backend her request başına 1 connection acquire
2. 100 concurrent → 100 connection talep
3. Pool 50 normal, 100 overflow → 150 ask
4. PG sadece 100 → **50 talep timeout veya queue**
5. Frontend 30s timeout sonrası 503

**Critical math:**
- Backend pool * uvicorn worker count = 50 * 4 = 200 (production Dockerfile)
- Şu an Dockerfile.minimal = 1 worker = 50 pool yeterli ama overflow 100 hala overflows PG

**Fix (Day 1):**
```ini
# .env.mvp
db_pool_size=15
db_pool_max_overflow=30
```

**Fix (Production):**
- PG max_connections=200
- veya PgBouncer transaction-mode pooler

---

## 9. Top 10 Audit Findings (Severity Sorted)

| # | Finding | Severity | Fix complexity | ETA |
|---|---|---|---|---|
| F-DB-1 | Curator queue 156ms tam tarama, index yok | 🔴 P0 | Single CREATE INDEX | 5dk + ANALYZE |
| F-DB-2 | JSONB extract seq scan (gold filter) | 🔴 P0 | Expression index | 5dk + ANALYZE |
| F-DB-3 | shared_buffers 128MB → cache hit %56 | 🔴 P0 | postgresql.conf + restart | 15dk |
| F-DB-4 | work_mem 4MB → 1.7GB temp files | 🔴 P0 | postgresql.conf | 15dk |
| F-DB-5 | max_connections 100 < pool 150 | 🔴 P0 | postgresql.conf veya .env.mvp pool reduce | 5dk |
| F-DB-6 | random_page_cost 4 (HDD) on SSD | 🟡 P1 | postgresql.conf | 5dk |
| F-DB-7 | pg_stat_statements installed but not loaded | 🟡 P1 | shared_preload_libraries | 15dk |
| F-DB-8 | 6 duplicate/unused index in question_bank (~100MB+) | 🟡 P1 | DROP INDEX | 5dk |
| F-DB-9 | Legacy `questions` table 40MB index, 0 scan | 🟡 P1 | DROP TABLE | 5dk |
| F-DB-10 | default_statistics_target 100 (JSONB cardinality off) | 🟢 P2 | ALTER COLUMN STATISTICS | 10dk |

---

## 10. Hızlı Çözüm Planı (Day 1, ~1 saat)

```sql
-- Step 1: Missing index (5dk + ANALYZE)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_review_status_active
ON question_bank (quality_review_status, is_active)
WHERE is_active = TRUE;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_beta_filter_rule
ON question_bank ((pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule'))
WHERE is_active = TRUE;

ANALYZE question_bank;
```

```sql
-- Step 2: Drop redundant indexes (15dk, write performance ↑)
DROP INDEX IF EXISTS idx_qbank_topic;          -- subset of idx_qb_primary_topic
DROP INDEX IF EXISTS idx_qbank_calibrated;      -- subset of idx_qbank_calibrated_active
DROP INDEX IF EXISTS idx_qbank_subject;         -- subset of idx_qb_cat_subject_active
DROP INDEX IF EXISTS idx_qb_soru_hash;          -- duplicate of uq_qb_soru_hash_active
DROP INDEX IF EXISTS idx_qbank_grade;           -- 0 scan
DROP INDEX IF EXISTS idx_qbank_text_gin;        -- 0 scan, full-text not used

-- Legacy cleanup
DROP TABLE IF EXISTS questions CASCADE;
```

```ini
# Step 3: postgresql.conf (15dk + restart)
shared_buffers = 2GB                       # 128MB → 2GB
effective_cache_size = 6GB                 # 4GB → 6GB
work_mem = 32MB                            # 4MB → 32MB
maintenance_work_mem = 512MB               # 64MB → 512MB
max_connections = 200                      # 100 → 200
random_page_cost = 1.1                     # 4 → 1.1 (SSD)
default_statistics_target = 500            # 100 → 500
effective_io_concurrency = 200             # 16 → 200
max_wal_size = 4GB                         # 1GB → 4GB
shared_preload_libraries = 'pg_stat_statements'  # enable slow query tracking
pg_stat_statements.track = all
```

**Beklenen sonuçlar:**
- Curator queue 156ms → **<5ms** (30x)
- JSONB extract seq scan → **<50ms** for full scan
- Cache hit %56 → **%92+** (3.5GB shared_buffers cover edebilir)
- Temp file spill %95+ azalır
- Connection exhaustion riski biter
- Slow query tracking aktif → daha fazla optimization data

---

## 11. Diğer Eksiklikler (Sonraki Sprint İçin)

- **Backend hot query EXPLAIN ANALYZE batch** — `/api/v1/auth/me`, `/learning-path/today`, `/fsrs/due`, `/exam-configs`, `/admin/content/questions`, BKT/IRT/FSRS update path (separate session)
- **N+1 query grep audit** — backend kodunda lazy-load pattern
- **Migration history multi-head check** — `alembic heads` actual output (agent 3 üretti)
- **PgBouncer deployment plan** — 100+ student için
- **Read replica strategy** — 1K+ student için
- **Backup automation** — pg_dump cron (Faz 0.4 rollback poligonu)

---

## 12. Audit Yöntemi Notları

**Çalıştırılan komutlar (reproducible):**

```bash
# PG config
PGPASSWORD=1470 psql -p 5434 -d kiro2 -c "SELECT name, setting FROM pg_settings WHERE ..."

# Cache hit + I/O stats
psql -c "SELECT * FROM pg_stat_database WHERE datname='kiro2'"

# Sequential scan damage
psql -c "SELECT relname, seq_scan, seq_tup_read FROM pg_stat_user_tables ORDER BY seq_tup_read DESC LIMIT 15"

# Unused indexes
psql -c "SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0 AND pg_relation_size > 1MB"

# Bloat / vacuum
psql -c "SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables WHERE n_dead_tup > 1000"

# EXPLAIN ANALYZE per hot query
psql -c "EXPLAIN (ANALYZE, BUFFERS) <query>"
```

**Read-only zorunluluk:** Tüm sorgular sadece `SELECT` ve `EXPLAIN`. Hiçbir `CREATE INDEX`, `DROP`, `ALTER` çalıştırılmadı. Fix önerileri kullanıcının onayına kaldı.

---

**Session 178 sonrası DB performance audit tamamlandı.** Production'da P0 fix'ler için ~1 saat sprint, beklenen **30x curator queue speedup + cache hit %56 → %92+**.
