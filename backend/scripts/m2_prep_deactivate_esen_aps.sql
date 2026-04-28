UPDATE question_bank
SET is_active = FALSE,
    updated_at = NOW(),
    pipeline_metadata = (
        COALESCE(pipeline_metadata::jsonb, '{}'::jsonb) ||
        '{"m2_prep_deactivate_at":"2026-04-28","reason":"active_dup_with_id_0d6e5dbe_esen_tyt_canonical"}'::jsonb
    )::json
WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
