-- NUKE auto_judged_high → pending (manuel review queue)
-- Goal: 'görseli eksik soru hiç kalmayana kadar' literal satisfaction
BEGIN;

\echo Pre-state:
SELECT quality_review_status, COUNT(*) FROM question_bank
WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

\echo
\echo Performing NUKE...

UPDATE question_bank
SET quality_review_status = 'pending',
    pipeline_metadata = jsonb_set(
        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
        '{beta_pool_nuke_v1}',
        '{"date":"2026-05-19","source":"beta_pool_nuke_v1","reason":"8-wave saturation, manuel review queue"}'::jsonb,
        TRUE
    )::json,
    updated_at = NOW()
WHERE is_active=true AND quality_review_status='auto_judged_high';

\echo
\echo Post-state:
SELECT quality_review_status, COUNT(*) FROM question_bank
WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

SELECT 'v_safe_for_beta' AS metric, COUNT(*) AS count FROM v_safe_for_beta;

COMMIT;
