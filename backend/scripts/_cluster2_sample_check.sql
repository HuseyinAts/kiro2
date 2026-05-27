-- Cluster 2 sample 5: verify column types in live DB
-- READ-ONLY: SELECT only
\pset border 2
\pset format aligned

SELECT
    table_name,
    column_name,
    data_type,
    udt_name,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
    'kiro2_learning_events',
    'kiro2_cat_sessions',
    'topic_prerequisites',
    'reasoning_cache',
    'universities'
  )
  AND column_name IN ('id', 'user_id', 'session_id', 'parent_step_id', 'topic_id', 'prereq_id', 'university_id')
ORDER BY table_name, column_name;

-- Row counts
SELECT
    'kiro2_learning_events' AS tbl, COUNT(*) AS rows FROM kiro2_learning_events
UNION ALL SELECT 'kiro2_cat_sessions', COUNT(*) FROM kiro2_cat_sessions
UNION ALL SELECT 'topic_prerequisites', COUNT(*) FROM topic_prerequisites
UNION ALL SELECT 'reasoning_cache', COUNT(*) FROM reasoning_cache
UNION ALL SELECT 'universities', COUNT(*) FROM universities
ORDER BY tbl;
