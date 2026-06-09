-- =====================================================================
-- KIRO2 FULL DATABASE AUDIT  (schema + data-quality, READ-ONLY)
-- Target: host PostgreSQL 18, port 5434, db "kiro2", schema "public"
-- Run:
--   "C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 ^
--     -f "C:/Users/husey/kiro2/db_audit_full.sql" > "C:/Users/husey/kiro2/db_audit_output.txt" 2>&1
-- Then paste / share db_audit_output.txt back.
--
-- NOTES
--  * 100% read-only: only SELECT + \gexec-generated SELECT. No DDL/DML.
--  * Catalog-driven: discovers EVERY table & column itself (no hardcoded names).
--  * Section I (null counts) does one seq-scan per table -> may take minutes.
--  * KIRO2-specific checks (Section J) are guarded by to_regclass/column-exists,
--    so they silently skip if a table/column is absent (no errors).
-- =====================================================================

\set ON_ERROR_STOP off
\pset pager off
\pset footer off
\timing on
\echo '############################################################'
\echo '# KIRO2 FULL DB AUDIT'
\echo '############################################################'
SELECT now() AS audit_started, current_database() AS db, current_user AS run_as;
SELECT version();

-- =====================================================================
\echo ''
\echo '=== A. DATABASE OVERVIEW ==='
-- =====================================================================
SELECT current_database()                                   AS db,
       pg_size_pretty(pg_database_size(current_database()))  AS db_size,
       (SELECT count(*) FROM pg_tables  WHERE schemaname='public') AS public_tables,
       (SELECT count(*) FROM pg_views   WHERE schemaname='public') AS public_views,
       (SELECT count(*) FROM pg_matviews WHERE schemaname='public') AS public_matviews;

SELECT pg_encoding_to_char(encoding) AS server_encoding, datcollate, datctype
FROM pg_database WHERE datname = current_database();

\echo 'Non-system schemas:'
SELECT nspname FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%' AND nspname <> 'information_schema'
ORDER BY 1;

-- =====================================================================
\echo ''
\echo '=== B. TABLE INVENTORY (size, estimated/live/dead rows, last analyze) ==='
-- =====================================================================
SELECT n.nspname                                   AS schema,
       c.relname                                   AS table_name,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
       pg_size_pretty(pg_relation_size(c.oid))       AS table_size,
       pg_size_pretty(pg_indexes_size(c.oid))        AS index_size,
       c.reltuples::bigint                          AS est_rows,
       s.n_live_tup                                 AS live_rows,
       s.n_dead_tup                                 AS dead_rows,
       s.last_analyze,
       s.last_autoanalyze
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind = 'r' AND n.nspname = 'public'
ORDER BY pg_total_relation_size(c.oid) DESC;

-- =====================================================================
\echo ''
\echo '=== C. EXACT ROW COUNTS (every public table) ==='
-- =====================================================================
SELECT string_agg(
         format('SELECT %L::text AS table_name, count(*)::bigint AS exact_rows FROM %I.%I',
                tablename, schemaname, tablename),
         E'\nUNION ALL '
         ORDER BY tablename)
       || E'\nORDER BY exact_rows DESC'
FROM pg_tables
WHERE schemaname = 'public'
\gexec

-- =====================================================================
\echo ''
\echo '=== D. ALL COLUMNS (every table, every column: type/len/null/default) ==='
-- =====================================================================
SELECT table_name,
       ordinal_position AS pos,
       column_name,
       data_type,
       COALESCE(character_maximum_length::text,
                NULLIF(numeric_precision::text,'') ||
                  COALESCE(','||numeric_scale::text,''),
                '') AS len_or_precision,
       is_nullable,
       column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- =====================================================================
\echo ''
\echo '=== E. CONSTRAINTS (PK / FK / UNIQUE / CHECK / EXCLUDE) ==='
-- =====================================================================
SELECT rel.relname AS table_name,
       c.conname    AS constraint_name,
       CASE c.contype
            WHEN 'p' THEN 'PRIMARY KEY'
            WHEN 'f' THEN 'FOREIGN KEY'
            WHEN 'u' THEN 'UNIQUE'
            WHEN 'c' THEN 'CHECK'
            WHEN 'x' THEN 'EXCLUDE'
            ELSE c.contype::text END AS type,
       pg_get_constraintdef(c.oid)  AS definition
FROM pg_constraint c
JOIN pg_class rel     ON rel.oid = c.conrelid
JOIN pg_namespace n   ON n.oid   = rel.relnamespace
WHERE n.nspname = 'public'
ORDER BY rel.relname, type, c.conname;

-- =====================================================================
\echo ''
\echo '=== F. GAP: TABLES WITHOUT PRIMARY KEY ==='
-- =====================================================================
SELECT n.nspname AS schema, c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND n.nspname = 'public'
  AND NOT EXISTS (SELECT 1 FROM pg_constraint k
                  WHERE k.conrelid = c.oid AND k.contype = 'p')
ORDER BY 2;

-- =====================================================================
\echo ''
\echo '=== G. INDEXES (all) ==='
-- =====================================================================
SELECT tablename AS table_name, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- =====================================================================
\echo ''
\echo '=== H. GAP: FOREIGN KEYS WITHOUT A SUPPORTING INDEX (perf risk) ==='
-- =====================================================================
SELECT rel.relname AS table_name,
       c.conname    AS fk_name,
       pg_get_constraintdef(c.oid) AS fk_def
FROM pg_constraint c
JOIN pg_class rel   ON rel.oid = c.conrelid
JOIN pg_namespace n ON n.oid   = rel.relnamespace
WHERE c.contype = 'f' AND n.nspname = 'public'
  AND NOT EXISTS (
        SELECT 1 FROM pg_index i
        WHERE i.indrelid = c.conrelid
          AND (c.conkey[1]) = i.indkey[0])
ORDER BY rel.relname, c.conname;

-- =====================================================================
\echo ''
\echo '=== L. ENUM TYPES + labels ==='
-- =====================================================================
SELECT t.typname AS enum_type,
       string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder) AS labels
FROM pg_type t
JOIN pg_enum e      ON e.enumtypid = t.oid
JOIN pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname = 'public'
GROUP BY t.typname
ORDER BY t.typname;

-- =====================================================================
\echo ''
\echo '=== M. ALEMBIC MIGRATION HEAD ==='
-- =====================================================================
SELECT 'SELECT version_num AS alembic_head FROM alembic_version'
WHERE to_regclass('public.alembic_version') IS NOT NULL
\gexec

-- =====================================================================
\echo ''
\echo '=== I. NULL COUNTS per column (per table; one scan each) ==='
\echo '    (wide output: one result row per table, *_n = null count for that column)'
-- =====================================================================
SELECT 'SELECT ' || quote_literal(table_name) || ' AS table_name, count(*) AS total_rows, '
       || string_agg(
             format('count(*) FILTER (WHERE %I IS NULL) AS %I',
                    column_name, left(column_name, 58) || '_n'),
             ', ' ORDER BY ordinal_position)
       || ' FROM ' || quote_ident(table_schema) || '.' || quote_ident(table_name)
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_schema, table_name
ORDER BY table_name
\gexec

-- =====================================================================
\echo ''
\echo '=== K. FK ORPHAN CHECK (referential integrity violations) ==='
-- =====================================================================
WITH fk AS (
  SELECT c.oid AS conoid, c.conname, c.conrelid, c.confrelid, c.conkey, c.confkey,
         ns.nspname  AS sch,  rel.relname  AS tbl,
         fns.nspname AS fsch, frel.relname AS ftbl
  FROM pg_constraint c
  JOIN pg_class rel     ON rel.oid  = c.conrelid
  JOIN pg_namespace ns  ON ns.oid   = rel.relnamespace
  JOIN pg_class frel    ON frel.oid = c.confrelid
  JOIN pg_namespace fns ON fns.oid  = frel.relnamespace
  WHERE c.contype = 'f' AND ns.nspname = 'public'
),
m AS (
  SELECT fk.conoid, fk.conname, fk.sch, fk.tbl, fk.fsch, fk.ftbl,
    string_agg('c.'||quote_ident(att.attname)||' = p.'||quote_ident(fatt.attname),
               ' AND ' ORDER BY k.ord) AS joincond,
    string_agg('c.'||quote_ident(att.attname)||' IS NOT NULL',
               ' AND ' ORDER BY k.ord) AS notnullcond
  FROM fk
  JOIN LATERAL unnest(fk.conkey)  WITH ORDINALITY AS k(attnum,  ord)  ON true
  JOIN LATERAL unnest(fk.confkey) WITH ORDINALITY AS fk2(fattnum,ford) ON fk2.ford = k.ord
  JOIN pg_attribute att  ON att.attrelid  = fk.conrelid  AND att.attnum  = k.attnum
  JOIN pg_attribute fatt ON fatt.attrelid = fk.confrelid AND fatt.attnum = fk2.fattnum
  GROUP BY fk.conoid, fk.conname, fk.sch, fk.tbl, fk.fsch, fk.ftbl
)
SELECT format(
  'SELECT %L AS fk_name, %L AS child_table, %L AS parent_table, count(*) AS orphan_rows '
  || 'FROM %I.%I c WHERE (%s) AND NOT EXISTS (SELECT 1 FROM %I.%I p WHERE %s)',
  conname, sch||'.'||tbl, fsch||'.'||ftbl, sch, tbl, notnullcond, fsch, ftbl, joincond)
FROM m
ORDER BY tbl, conname
\gexec

-- =====================================================================
\echo ''
\echo '=== J. KIRO2-SPECIFIC QUALITY CHECKS (guarded; skip if absent) ==='
-- =====================================================================

\echo '-- J1. question_bank vs legacy questions row counts + is_active breakdown'
SELECT 'SELECT count(*) AS qb_total, '
    || 'count(*) FILTER (WHERE is_active) AS qb_active, '
    || 'count(*) FILTER (WHERE NOT is_active) AS qb_inactive FROM question_bank'
WHERE to_regclass('public.question_bank') IS NOT NULL
  AND EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema='public' AND table_name='question_bank' AND column_name='is_active')
\gexec

SELECT 'SELECT count(*) AS questions_legacy_total FROM questions'
WHERE to_regclass('public.questions') IS NOT NULL
\gexec

\echo '-- J2. quality_review_status distribution + rejected-but-active LEAK (Lesson #31)'
SELECT 'SELECT quality_review_status, count(*) AS n, '
    || 'count(*) FILTER (WHERE is_active) AS still_active FROM question_bank '
    || 'GROUP BY quality_review_status ORDER BY n DESC'
WHERE to_regclass('public.question_bank') IS NOT NULL
  AND EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='quality_review_status')
  AND EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='is_active')
\gexec

\echo '-- J3. subject_area distribution (expected UPPERCASE) + non-uppercase offenders'
SELECT 'SELECT subject_area, count(*) AS n FROM question_bank GROUP BY subject_area ORDER BY 1'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='subject_area')
\gexec

SELECT 'SELECT count(*) AS subject_area_not_uppercase FROM question_bank '
    || 'WHERE subject_area IS NOT NULL AND subject_area <> upper(subject_area)'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='subject_area')
\gexec

\echo '-- J4. exam_type distribution'
SELECT 'SELECT exam_type, count(*) AS n FROM question_bank GROUP BY exam_type ORDER BY n DESC'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='exam_type')
\gexec

\echo '-- J5. question image coverage'
SELECT 'SELECT count(*) AS total, '
    || 'count(*) FILTER (WHERE question_image_url IS NULL OR question_image_url='''') AS missing_image, '
    || 'round(100.0*count(*) FILTER (WHERE question_image_url IS NULL OR question_image_url='''')/NULLIF(count(*),0),2) AS missing_pct '
    || 'FROM question_bank'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='question_image_url')
\gexec

\echo '-- J6. exact-duplicate question_text groups'
SELECT 'SELECT count(*) AS dup_text_groups, COALESCE(sum(c-1),0) AS extra_dup_rows '
    || 'FROM (SELECT md5(question_text) h, count(*) c FROM question_bank '
    || 'WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) t'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='question_text')
\gexec

\echo '-- J7. encoding red flags in question_text (U+FFFD replacement char / NUL)'
SELECT 'SELECT '
    || 'count(*) FILTER (WHERE position(chr(65533) in question_text) > 0) AS replacement_char_rows, '
    || 'count(*) FILTER (WHERE question_text ~ ''[[:cntrl:]]'' ) AS control_char_rows '
    || 'FROM question_bank WHERE question_text IS NOT NULL'
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='question_text')
\gexec

\echo '-- J8. empty-string-as-null offenders in question_text'
SELECT 'SELECT count(*) AS empty_question_text FROM question_bank '
    || 'WHERE question_text IS NOT NULL AND btrim(question_text)='''''
WHERE EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name='question_bank' AND column_name='question_text')
\gexec

\echo ''
\echo '############################################################'
\echo '# AUDIT COMPLETE'
\echo '############################################################'
SELECT now() AS audit_finished;
