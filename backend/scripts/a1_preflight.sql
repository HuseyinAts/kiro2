\echo '=== Pre-flight 1: index name collision check ==='
SELECT indexname FROM pg_indexes
WHERE tablename = 'question_bank'
  AND indexname IN (
    'idx_qbank_status_active', 'idx_qbank_active_created',
    'idx_qbank_beta_filter_rule', 'idx_qbank_quality_subject_exam',
    'idx_qbank_created_by'
  );

\echo ''
\echo '=== Pre-flight 2: EXPLAIN curator queue (BEFORE) ==='
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT id, quality_review_status FROM question_bank
WHERE quality_review_status = 'bronze_clean' AND is_active = TRUE
LIMIT 50;

\echo ''
\echo '=== Pre-flight 3: gold pool random picker (BEFORE) ==='
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT id FROM question_bank
WHERE is_active = TRUE
  AND quality_review_status IN ('auto_judged_high', 'human_verified')
  AND subject_area = 'MATEMATIK' AND exam_type = 'TYT'
LIMIT 20;
