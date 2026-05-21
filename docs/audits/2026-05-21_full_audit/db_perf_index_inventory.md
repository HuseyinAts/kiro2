# DB Performance + Index Inventory Audit

**Tarih:** 2026-05-21
**DB:** PostgreSQL **18.1** (Windows native, port 5434, db `kiro2`)
**NOT:** MEMORY.md "PostgreSQL 15" yazıyor — gerçek sürüm 18.1. Sürüm kaydı düzeltilmeli.
**Toplam tablo (public):** 245 (`pg_stat_user_tables` 8 tabloda n_live_tup>0 gösteriyor, **ama `questions` 36,381 row içeriyor — yalnızca ANALYZE edilmemiş**. `last_analyze` ve `last_autoanalyze` NULL → autovacuum hiç ziyaret etmemiş. Real table size: **79 MB** (29 MB heap + 50 MB index). MEMORY.md "BOŞ legacy" yanlış.)
**Toplam unused non-pkey index ağırlığı:** **250 MB** wasted
**Methodology:** Read-only audit. Sadece `EXPLAIN ANALYZE` + `pg_stat_*` sorguları. Hiçbir `CREATE/DROP INDEX` çalıştırılmadı.

---

## Executive Summary

| Severity | Finding | Detay |
|---|---|---|
| P0 | **JSONB filter 1.5s seq scan** | `pipeline_metadata->beta_filter_v1->>'rule' = 'R4_rule_based_gold'` (81K row hit) tüm 192K tabloyu parallel seq scan ediyor. Beta queue endpoint için kritik. |
| P0 | **quality_review_status 261ms seq scan** | Bu kolon üzerinde index yok. 15K `auto_judged_high` row için tüm tablo (495MB heap) seq scan. |
| P1 | **250 MB unused (non-pkey) index** | Toplam 100+ index, sadece ~18'i kullanımda. En büyükleri: `idx_qbank_text_gin` (62MB), `idx_questions_text_search` (23MB), `idx_qb_soru_hash` (17MB). |
| P1 | **35 duplicate index çifti** | En büyüğü `kiro2_learning_events.user_id` (11MB, 2x), `question_bank.primary_topic_id` (10MB, 2x), `users.email`/`users.username` (her biri 2x). |
| P1 | **`questions` table 36K row, ANALYZE edilmemiş** | `pg_stat` 0 row diyor ama gerçek 36,381 row. Planner stats yok → tüm sorgular suboptimal. Hemen `ANALYZE questions` çalıştır. |
| P2 | **99 FK without index** | Çoğu boş tabloda (theoretical). Gerçek risk: `question_bank.created_by` + `reviewed_by` (192K rows, NULL-heavy ama parent DELETE cascade tehlikesi). |
| P3 | **0 bloat issue** | `question_bank` %6.3 dead tup, autovacuum sağlıklı. |
| INFO | **Tüm session/event/response tabloları boş** | Beta traffic henüz başlamadı; perf bulgusu workload simulation ile değil, yapısal analizden. |

---

## Tablo 0: Genel Tablo + Boyut (`pg_stat_user_tables`)

**Query:**
```sql
SELECT schemaname, relname AS tablename, n_live_tup AS row_count,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS total_size,
       pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) AS table_size,
       pg_size_pretty(pg_indexes_size(schemaname||'.'||relname)) AS index_size
FROM pg_stat_user_tables WHERE schemaname='public'
ORDER BY n_live_tup DESC LIMIT 30;
```

**Actual output (top tables with data):**
```
          tablename          | row_count | total_size | table_size | index_size
-----------------------------+-----------+------------+------------+------------
 question_option_rationales  |    408720 | 137 MB     | 89 MB      | 48 MB
 question_bank               |    192389 | 1951 MB    | 495 MB     | 789 MB   <-- 789MB index!
 question_math               |     31034 | 5064 kB    | 2672 kB    | 2352 kB
 topic_prerequisites         |       106 | 176 kB     | 24 kB      | 120 kB
 users                       |        75 | 176 kB     | 24 kB      | 120 kB
 refresh_tokens              |         4 | 3728 kB    | 1072 kB    | 2616 kB
 coaching_events             |         2 | 128 kB     | 16 kB      | 80 kB
 audit_logs                  |         1 | 160 kB     | 8192 bytes | 144 kB
(remaining 237 tables empty)
```

**Insight:** `question_bank` 789MB index size vs 495MB heap → **index/heap ratio 1.59x** (sağlıklı oran <0.5). Sebep: 23 index, çoğu 0 scan.

**question_bank storage breakdown:**
```
 total  |  heap  | toast (vector+jsonb)
---------+--------+----------------------
 1951 MB | 495 MB | 667 MB
```
TOAST 667MB = embedding (HNSW 551MB indexed) + pipeline_metadata JSONB + question_text uzun değerler.

---

## Finding F-1 (P0): JSONB Path Filter — 1.5 saniye Seq Scan

**Query:**
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM question_bank
WHERE is_active = TRUE
  AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R4_rule_based_gold';
```

**Actual output:**
```
 Finalize Aggregate  (cost=66163.03..66163.04 rows=1 width=8) (actual time=1531.011..1534.707 rows=1.00 loops=1)
   Buffers: shared hit=419392 read=142032 written=29
   ->  Gather  (cost=66162.82..66163.03 rows=2 width=8) (actual time=1531.003..1534.703 rows=3.00 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         ->  Partial Aggregate
               ->  Parallel Seq Scan on question_bank
                     Filter: (is_active AND ((((pipeline_metadata)::jsonb -> 'beta_filter_v1'::text) ->> 'rule'::text) = 'R4_rule_based_gold'::text))
                     Rows Removed by Filter: 35353
 Planning Time: 8.687 ms
 Execution Time: 1534.742 ms
```

**Numerical evidence:**
- Execution time: **1534.7 ms** (1.5 saniye)
- Buffers: hit=419392 read=142032 (561K buffers ≈ 4.5GB scanned)
- Workers: 2 parallel + leader (still 1.5s)
- Matching rows: 81,776 (43% of `is_active=TRUE`)
- LIMIT 100 variant: 8.5ms (still seq scan ama early exit)

**Impact:**
- `v_safe_for_beta` view'i bu pattern'i kullanıyor (CLAUDE.md `quality_review_status` ve `pipeline_metadata` üzerinden filter).
- Beta queue endpoint'leri (`backend/api/quality_review.py`, beta filter pipeline): her sayfada bu sorgu çalışıyorsa P95 ≥ 2s.
- 1K concurrent student için tüm worker'lar bu sorgu üstünde sürekli takılır.

**Fix (apply etmedim, sadece öneri):**
```sql
-- Beta filter R4 için partial expression index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_beta_filter_rule
  ON question_bank ((pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule'))
  WHERE is_active = TRUE;

-- Veya genel JSONB GIN (geniş kapsam, 60-80MB tahmini):
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_pipeline_meta_gin
  ON question_bank USING gin (pipeline_metadata jsonb_path_ops)
  WHERE is_active = TRUE;
```

**Re-test EXPLAIN ANALYZE expected:**
- Bitmap Index Scan on `idx_qbank_beta_filter_rule` + Bitmap Heap Scan
- Tahmini execution time: **<50ms** (30x speedup)
- Buffer access: shared hit ~3000 (200x azalma)
- Trade-off: index ~5-10MB partial, INSERT/UPDATE üzerinde minor overhead

---

## Finding F-2 (P0): `quality_review_status` Filter — 261ms Seq Scan

**Query:**
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM question_bank
WHERE is_active = TRUE AND quality_review_status = 'auto_judged_high';
```

**Actual output:**
```
 Aggregate  (cost=65748.93..65748.94 rows=1 width=8) (actual time=261.029..261.029 rows=1.00 loops=1)
   Buffers: shared hit=13754 read=49647
   ->  Seq Scan on question_bank
         Filter: (is_active AND ((quality_review_status)::text = 'auto_judged_high'::text))
         Rows Removed by Filter: 172513
 Planning Time: 10.466 ms
 Execution Time: 261.063 ms
```

**Numerical evidence:**
- Execution time: **261 ms**
- Buffers: hit=13754 read=49647 (63K buffers, ~500MB)
- Matching rows: 15,321 (8% of active)
- LIMIT 100 variant: 2.1ms (lucky locality)

**Distribution evidence:**
```sql
SELECT quality_review_status, COUNT(*) FROM question_bank WHERE is_active=true GROUP BY 1;
 unverified       | 61482
 rejected         | 54126
 pending          | 36433
 auto_judged_high | 15321
 bronze_clean     |   197
```

5 distinct values × selective enough → ideal index candidate.

**Impact:**
- Bronze tier manual review queue (CLAUDE.md mentions `bronze_clean` curator workflow).
- Admin `/quality_review` endpoint (`backend/api/quality_review.py` muhtemelen).
- Beta launch sırasında her admin dashboard refresh bu sorguyu vurur.

**Fix:**
```sql
-- Single column index (15K row → ~120kB)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_review_status_active
  ON question_bank (quality_review_status)
  WHERE is_active = TRUE;

-- Veya composite (subject_area + status + is_active için multi-dim filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_status_subject_active
  ON question_bank (quality_review_status, subject_area)
  WHERE is_active = TRUE;
```

**Re-test expected:**
- Bitmap Index Scan + Bitmap Heap Scan
- Tahmini execution time: **<20ms** (13x speedup)
- Buffer reads: ~200

---

## Finding F-3 (P1): Unused Indexes — 250 MB Total

**Query:**
```sql
SELECT schemaname, relname AS tablename, indexrelname AS indexname,
       idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname='public' AND idx_scan = 0 AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC LIMIT 20;
```

**Actual output (top 20):**
```
            tablename            |         indexname          | idx_scan |  size
---------------------------------+----------------------------+----------+---------
 question_bank                   | idx_qbank_text_gin         |        0 | 62 MB   <-- BÜYÜK GIN, 0 scan
 questions                       | idx_questions_text_search  |        0 | 23 MB
 question_bank                   | idx_qb_soru_hash           |        0 | 17 MB
 question_bank                   | idx_qbank_quality          |        0 | 17 MB
 question_kc_mapping             | idx_qkc_question           |        0 | 13 MB
 question_bank                   | uq_qb_soru_hash_active     |        0 | 13 MB
 question_bank                   | idx_qbank_irt_difficulty   |        0 | 12 MB
 questions                       | idx_questions_text_gin     |        0 | 6.5 MB
 question_bank                   | idx_qbank_topic_difficulty |        0 | 6.2 MB
 questions                       | idx_questions_topic_search |        0 | 6.2 MB
 kiro2_learning_events           | idx_kiro2_le_user          |        0 | 6.1 MB
 kiro2_learning_events_synthetic | idx_synthetic_events_user  |        0 | 6.0 MB
 question_bank                   | idx_qbank_topic            |        0 | 6.0 MB
 question_bank                   | idx_qbank_source_book      |        0 | 5.0 MB
 question_bank                   | idx_qbank_grade            |        0 | 4.7 MB
 ... (35 more rows)
```

**Numerical evidence:**
- Total unused non-pkey index size: **250.14 MB**
- `pg_stat_database.stats_reset` = NULL → istatistikler hiç sıfırlanmamış → 0 scan = gerçek "never used"
- Tablolarda data var (question_bank 192K, questions ise legacy/empty per MEMORY.md)

**Risk degerlendirme:**
- **`idx_qbank_text_gin` (62MB):** Full-text search için tasarlanmış, ama kod base text search'i muhtemelen başka yoldan yapıyor (embedding HNSW kullanılıyor). **Aday: DROP.**
- **`questions.*` indexes (50MB+):** MEMORY.md "BOŞ legacy" diyordu ama **gerçek count: 36,381 row** (audit sırasında doğrulandı). Tablo aktif kullanımda olabilir — indexes silmeden önce kullanım analizi gerek.
- **`idx_qbank_quality` (17MB), `idx_qbank_irt_difficulty` (12MB), `idx_qbank_topic_difficulty` (6MB):** Algoritma pipeline'da (IRT/BKT/ZPD) kullanılması beklenir ama 0 scan → ya kod bu indexes'i kullanmıyor, ya stats hiç oluşmadan production'a hiç yük gelmedi. Beta sonrası 2 hafta tekrar bak.
- **`idx_qbank_topic` + `idx_qb_primary_topic`:** Aynı kolon (`primary_topic_id`), bir tanesi silinmeli — duplicate.

**Fix önerisi (DROP candidates) — ÖNEMLİ: silmeden önce kullanım analizi şart:**
```sql
-- questions tablosu 36,381 row var (legacy DEĞİL, sadece eski model).
-- Eğer hiç sorgulama yapmıyorsa (idx_scan=0 değer gerçek), önce code grep:
--   grep -r "from models.questions import" backend/  veya benzeri
-- Eğer kod questions'a hala referans veriyorsa indexes'i bırak.
-- Tablonun kendisi silinmiyorsa, salt index drop yarardan çok zarar verebilir.

-- BETA SONRASI 2 hafta gözle (pg_stat_statements ile workload izle):
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_text_gin;            -- 62 MB
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_quality;             -- 17 MB
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_irt_difficulty;      -- 12 MB
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_topic;               -- 6 MB (duplicate of idx_qb_primary_topic)
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_source_book;         -- 5 MB
-- DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_grade;               -- 4.7 MB
```

---

## Finding F-4 (P1): Duplicate Indexes — 35 Pair

**Query:**
```sql
WITH idx_cols AS (
  SELECT i.indrelid::regclass AS table_name,
         i.indexrelid::regclass AS idx_name,
         array_to_string(i.indkey::int[], ',') AS col_keys,
         pg_relation_size(i.indexrelid) AS size_bytes
  FROM pg_index i
  WHERE i.indisvalid AND NOT i.indisunique)
SELECT table_name, col_keys, count(*) AS dup_count,
       string_agg(idx_name::text, ', ') AS index_names,
       pg_size_pretty(SUM(size_bytes)) AS total_size
FROM idx_cols
GROUP BY table_name, col_keys
HAVING count(*) > 1
ORDER BY SUM(size_bytes) DESC;
```

**Actual output (top duplicates):**
```
          table_name          | col_keys |                   index_names                          | total_size
------------------------------+----------+--------------------------------------------------------+------------
 kiro2_learning_events        | 2,9      | idx_kiro2_le_user, idx_learning_events_user            | 11 MB
 question_bank                | 16       | idx_qbank_topic, idx_qb_primary_topic                  | 10 MB
 questions                    | 13       | idx_question_topic, idx_questions_topic_search         | 7 MB
 refresh_tokens               | 10       | idx_refresh_token_expires, ix_refresh_tokens_expires_at| 176 kB
 refresh_tokens               | 2        | idx_refresh_token_user, ix_refresh_tokens_user_id      | 160 kB
 refresh_tokens               | 11       | idx_refresh_token_revoked, ix_refresh_tokens_revoked   | 112 kB
 audit_logs                   | 10       | (3 dup!) idx_audit_logs_created_brin, ...              | 56 kB
 user_item_fsrs               | 1,5      | (3 dup) idx_fsrs_due, idx_uif_due, idx_uif_user_due    | 48 kB
 ... (27 more pairs/triples)
```

**Numerical evidence:**
- 35 distinct (table, col_keys) groups have 2+ indexes
- 3 groups have **triple** indexes (audit_logs, user_item_fsrs, notifications)
- Total wasted: **~30 MB** (most on small/empty tables)
- Pattern: `idx_xxx` (manual migration) vs `ix_xxx` (alembic autogenerate) — schema drift

**Bilinen sebep:** `.claude/rules/case-convention.md` ve Session 154 schema drift baseline'ı bunu işaret ediyor. Çift naming convention.

**Fix önerisi (sample):**
```sql
-- question_bank.primary_topic_id (10MB)
DROP INDEX CONCURRENTLY IF EXISTS idx_qbank_topic;
-- Keep: idx_qb_primary_topic (partial: WHERE primary_topic_id IS NOT NULL)

-- kiro2_learning_events.user_id (11MB)
DROP INDEX CONCURRENTLY IF EXISTS idx_kiro2_le_user;
-- Keep: idx_learning_events_user

-- users (small but pattern-y)
DROP INDEX CONCURRENTLY IF EXISTS idx_user_email;
-- Keep: ix_users_email (unique)
DROP INDEX CONCURRENTLY IF EXISTS idx_user_username;
-- Keep: ix_users_username (unique)
```

---

## Finding F-5 (P2): FK without Index — 99 toplam, 2 risk

**Query:**
```sql
SELECT c.conrelid::regclass AS table_name,
       string_agg(a.attname, ', ') AS columns,
       c.conname AS fk_name
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
    SELECT 1 FROM pg_index i
    WHERE i.indrelid = c.conrelid
      AND (c.conkey::int[] <@ (i.indkey::int[])::int[]))
GROUP BY c.conrelid, c.conname
ORDER BY c.conrelid::regclass::text;
```

**Output (filtered by table with rows):**
```
  table_name   |   columns   |            fk_name             | n_live_tup
---------------+-------------+--------------------------------+------------
 question_bank | created_by  | question_bank_created_by_fkey  |     192389
 question_bank | reviewed_by | question_bank_reviewed_by_fkey |     192389
```

**Fill rate:**
```
 created_by_filled | reviewed_by_filled | total
-------------------+--------------------+--------
                64 |                  0 | 187834
```

**Numerical evidence:**
- 99 FK without index totalde
- 97'si boş tabloda → şu an pratik etki yok
- `question_bank.created_by` 64/192389 (%0.03) NULL değil
- `reviewed_by` tamamen NULL (0 fill)

**Impact:**
- **Düşük şu an.** Curator/admin workflow başlayınca DELETE FROM users WHERE id=X CASCADE çağrılırsa, question_bank seq scan + lock 261ms+ sürer.
- 97 boş tabloda: data eklenince hemen FK lookup yavaş olacak.

**Fix (sadece risk olan ikisi):**
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_created_by
  ON question_bank (created_by)
  WHERE created_by IS NOT NULL;  -- partial: 64 rows, ~16kB

-- reviewed_by 0 satır filled → şimdilik gerek yok, beta sonrası tekrar bak.
```

---

## Finding F-5b (P1): `questions` Tablosu Statistics Stale — 36K Row Unanalyzed

**Query:**
```sql
SELECT relname, n_live_tup, n_dead_tup, last_analyze, last_autoanalyze,
       (SELECT COUNT(*) FROM questions) AS real_count
FROM pg_stat_user_tables WHERE relname='questions';
```

**Actual output:**
```
 relname  | n_live_tup | n_dead_tup | last_analyze | last_autoanalyze | real_count
-----------+------------+------------+--------------+------------------+------------
 questions |          0 |          0 |              |                  |      36381
```

**Numerical evidence:**
- `pg_stat_user_tables.n_live_tup` raporu: **0**
- Gerçek `SELECT COUNT(*)`: **36,381 row**
- Tablo boyutu: **79 MB** (29 MB heap + 50 MB index)
- Autovacuum/autoanalyze hiç çalışmamış (her iki kolon NULL)

**Impact:**
- Planner row estimate'leri tamamen yanlış → her sorgu için suboptimal plan
- 36K row "0 row" zannedildiği için indexes 0 scan görünüyor (gerçekte kullanılmıyor olabilir veya planner kullanmayı bilmiyor)
- MEMORY.md "BOŞ legacy" cümlesi yanlış; veri var, sadece istatistik yok

**Fix:**
```sql
-- İlk önce stats topla
ANALYZE questions;

-- Sonra plan refresh edilmiş halde gerçek index kullanımını gör:
-- (24-48 saat workload sonra pg_stat_user_indexes tekrar bak)

-- Eğer hala 0 scan ise: kod base ya bu tabloyu hiç sorgulamıyor
-- veya question_bank'a tam migrate olmuş — index'leri silebiliriz
```

**Aksiyon:** Önce `ANALYZE questions`, sonra 24h workload izle, sonra DROP kararı ver.

---

## Finding F-6 (P3): Bloat — Healthy

**Query:**
```sql
SELECT relname, n_live_tup, n_dead_tup,
       ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup, 0), 1) AS dead_tup_pct,
       last_autovacuum, last_analyze
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY dead_tup_pct DESC LIMIT 20;
```

**Actual output:**
```
          relname           | n_live_tup | n_dead_tup | dead_tup_pct |        last_autovacuum        |         last_analyze
----------------------------+------------+------------+--------------+-------------------------------+-------------------------------
 question_bank              |     192389 |      12188 |          6.3 | 2026-05-21 14:16:17           | 2026-05-21 14:06:33
 question_option_rationales |     408720 |          0 |          0.0 | 2026-05-21 04:19:32           |
 question_math              |      31034 |          0 |          0.0 | 2026-05-21 04:19:34           |
```

**Verdict:** Sağlıklı, autovacuum bugün çalıştı. Aksiyon yok.

---

## Finding F-7 (INFO): Composite Subject+Exam Index Mevcut, Plan Tercih Etmiyor

**Query:**
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM question_bank
WHERE is_active = TRUE AND subject_area = 'MATEMATIK' AND exam_type = 'TYT';
```

**Output (default planner):**
```
 Parallel Seq Scan on question_bank
   Filter: (is_active AND ((subject_area)::text = 'MATEMATIK'::text) AND ((exam_type)::text = 'TYT'::text))
   Rows Removed by Filter: 45955
 Execution Time: 183.658 ms
```

**Forced index scan (SET enable_seqscan = OFF):**
```
 Bitmap Heap Scan on question_bank
   Recheck Cond: ((subject_area)::text = 'MATEMATIK'::text)
   ->  Bitmap Index Scan on idx_qbank_subject
 Execution Time: 171.944 ms
```

**Numerical evidence:**
- Matching: 49,970 rows (26% of active)
- Existing index `idx_qbank_exam_subject_difficulty` mevcut, ama planner low selectivity nedeniyle seq scan'i tercih ediyor — **doğru karar**.
- LIMIT 100 versiyonu: 0.9ms (early exit). Production queries genelde paginated/limited olduğu için bu kabul edilebilir.

**Impact:** **Hiçbiri.** Seq scan burada doğru plan. COUNT(*) over 50K row her zaman buffer-bound olur. Endpoint paginated query'leri zaten LIMIT kullanıyor.

**Fix:** Yok. (Yanıltıcı pre-mature optimization olur.)

---

## question_bank Index Detayı (23 index)

**Full inventory (`pg_indexes`):**
```
                indexname              | size    | idx_scan | indexdef özet
---------------------------------------+---------+----------+------------------------------
 question_bank_pkey                    | 16 MB   |   244995 | UNIQUE id (kullanımda)
 idx_qbank_embedding_hnsw              | 551 MB  |      929 | HNSW vector(768) (semantic search, kullanımda)
 idx_qbank_exam_subject_difficulty     | 32 MB   |       34 | (exam_type, subject_area, irt_difficulty)
 idx_qbank_calibrated_active           | 20 MB   |        2 | (is_calibrated, is_active, quality_score)
 idx_qb_cat_subject_active             | 3.8 MB  |        5 | (lower(subject_area), is_active) WHERE is_active
 idx_qbank_subject                     | 5.0 MB  |        6 | (subject_area)
 idx_qbank_active                      | 3.1 MB  |        5 | (is_active)
 idx_qbank_calibrated                  | 3.0 MB  |        1 | (is_calibrated)
 -- ↓ UNUSED (idx_scan = 0)
 idx_qbank_text_gin                    | 62 MB   |        0 | gin(to_tsvector(question_text))   <-- silinebilir
 idx_qb_soru_hash                      | 17 MB   |        0 | (soru_hash)                       <-- soru_hash dedup için
 uq_qb_soru_hash_active                | 13 MB   |        0 | UNIQUE (soru_hash) WHERE is_active <-- duplicate hash check, INSERT'te kullanılıyor olabilir
 idx_qbank_quality                     | 17 MB   |        0 | (quality_score)
 idx_qbank_irt_difficulty              | 12 MB   |        0 | (irt_difficulty)
 idx_qbank_topic_difficulty            | 6.2 MB  |        0 | (primary_topic_id, difficulty_level)
 idx_qbank_topic                       | 6.0 MB  |        0 | (primary_topic_id)                <-- DUPLICATE
 idx_qb_primary_topic                  | 4.3 MB  |        0 | (primary_topic_id) WHERE NOT NULL  <-- DUPLICATE (partial)
 idx_qbank_source_book                 | 5.0 MB  |        0 | (source_book)
 idx_qbank_grade                       | 4.7 MB  |        0 | (grade_level)
 idx_qbank_difficulty                  | 4.0 MB  |        0 | (difficulty_level)
 idx_qbank_exam_type                   | 3.4 MB  |        0 | (exam_type)
 idx_qb_calib_pool                     | (n/a)   |        0 | (is_calib_pool) WHERE is_calib_pool=true
 idx_qbank_calib_pool                  | (n/a)   |        0 | (subject_area, is_calib_pool) WHERE ...
 idx_question_bank_reviewed_at         | (n/a)   |        0 | (reviewed_at) WHERE NOT NULL
```

**Eksik olan:** `quality_review_status` ve `pipeline_metadata` üzerinde index yok (F-1, F-2 root cause).

---

## Toplam Index Wasted Space

```sql
SELECT SUM(pg_relation_size(indexrelid)) / 1024 / 1024 AS unused_idx_mb
FROM pg_stat_user_indexes
WHERE schemaname='public' AND idx_scan = 0 AND indexrelname NOT LIKE '%_pkey';
-- Output: 250.14 MB
```

**Aksiyon Önerisi Önceliği:**

| Öncelik | Aksiyon | Etki |
|---|---|---|
| P0 | F-1: JSONB pipeline_metadata partial expression index | 1.5s → <50ms (30x) |
| P0 | F-2: quality_review_status partial index | 261ms → <20ms (13x) |
| P1 | F-4 duplicate index drop (top 4): kiro2_learning_events + question_bank + questions duplicates | 27 MB serbest + INSERT/UPDATE hızlanma |
| P1 | F-3 questions.* legacy index drop (boş tablo) | ~50 MB serbest |
| P2 | F-5 question_bank.created_by partial index | DELETE cascade kilit süresi |
| P3 | Beta sonrası 2 hafta wait: F-3 question_bank unused (text_gin, quality, irt_difficulty) reassess | ~90+ MB potansiyel |

---

## Notlar / Kaveat

1. **Tüm session/event tabloları boş** — bu audit yalnızca *statik* yapı analizi. Beta launch sonrası 2 hafta `pg_stat_statements` extension açıp gerçek workload pattern'i ölçülmeli.
2. **`stats_reset = NULL`** — istatistikler hiç sıfırlanmamış → 0 scan değerleri uzun gözlem süresine ait. Yine de upgrade sonrası istatistikler kaybolur, bir kez stats reset edilirse 24h beklemek lazım.
3. **HNSW index (551MB)** — bu sağlıklı, vector search için kritik. Toplam DB boyutunun büyük bölümünü açıklıyor.
4. **`questions` legacy tablosu** — MEMORY.md "BOŞ legacy" iddia ediyor ama gerçek `COUNT(*) = 36,381 row`. **MEMORY.md güncellenmeli.** Tabloya bağlı kod kullanımı kontrol edilmeden index/table drop tehlikeli.
5. **Read-only audit:** Bu rapor sadece öneri içerir. Hiçbir `CREATE INDEX` / `DROP INDEX` çalıştırılmadı. Production CONCURRENTLY clause ile uygulanmalı.

---

*Audit duration: ~25 dk. Tüm sorgu çıktıları `/tmp/q*.txt` altında ham olarak tutuluyor.*
