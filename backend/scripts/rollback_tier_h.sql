-- Tier H ROLLBACK (qip 0-index bug)
-- 49,468 satırın image_url=NULL'a geri çekilmesi + has_diagram restore

-- 1) image_url NULL + tier_h_match → tier_h_rollback flag
UPDATE question_bank
SET question_image_url = NULL,
    pipeline_metadata = jsonb_set(
        pipeline_metadata::jsonb - 'tier_h_match',
        '{tier_h_rollback}',
        jsonb_build_object(
            'reason', 'qip 0-index vs filename 1-index offset bug',
            'date', '2026-05-15',
            'original_crop_file', pipeline_metadata::jsonb -> 'tier_h_match' ->> 'crop_file',
            'hd_pre', pipeline_metadata::jsonb -> 'tier_h_match' ->> 'hd_pre',
            'sayfa_etkilenen', 22383,
            'audit_method', 'page_min_qip + sample text overlap'
        ),
        TRUE
    )::json
WHERE pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL;

-- 2) has_diagram restore: hd_pre=NULL olanlar → has_diagram=NULL (Tier H bunları true yaptı)
UPDATE question_bank
SET pipeline_metadata = pipeline_metadata::jsonb #- '{ai_extras,has_diagram}'
                        || jsonb_build_object('ai_extras',
                            (pipeline_metadata::jsonb -> 'ai_extras')
                            - 'has_diagram')
WHERE pipeline_metadata::jsonb -> 'tier_h_rollback' ->> 'hd_pre' IS NULL
  AND pipeline_metadata::jsonb -> 'tier_h_rollback' IS NOT NULL;

-- 3) Sonuç doğrulama
SELECT
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'tier_h_rollback' IS NOT NULL) AS rolled_back,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL) AS still_have_h_match
FROM question_bank;
