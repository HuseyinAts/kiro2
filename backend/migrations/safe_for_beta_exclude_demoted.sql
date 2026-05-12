-- safe_for_beta_exclude_demoted.sql
-- Date: 2026-05-13
-- Author: Claude session
-- Purpose: Exclude unverified-demoted (tier_f_low_confidence) rows from v_safe_for_beta
--
-- Context: L1-L3 analysis (13 May 2026) revealed 38,871 demoted rows in unverified
--   group flagged with tier_f_low_confidence_unverified. Spot sample of 5 demoted
--   rows showed 2 mathematically wrong answers (40% error). These should not appear
--   in beta. Wrapper-level exclusion is reversible and non-destructive.
--
-- View layer chain (after deploy):
--   v_safe_for_beta  --> wrapper: pending exclude + demoted exclude
--   v_safe_for_beta_unfiltered  --> base: pending exclude + word_count + regex + parity
--   question_bank  --> source
--
-- Pre-deploy counts (verified 2026-05-13 22:26 UTC):
--   v_safe_for_beta total:        161,028
--   demoted in v_safe_for_beta:    37,795
--   Expected after deploy:        123,233  (NULL metadata kept defensively)
--
-- NULL handling rationale:
--   `pipeline_metadata::jsonb ? 'demoted_at'` returns NULL for NULL metadata.
--   We KEEP NULL-metadata rows because they cannot be demoted (no key = no flag).
--
-- ROLLBACK (paste into psql to revert):
--   CREATE OR REPLACE VIEW v_safe_for_beta AS
--   SELECT * FROM v_safe_for_beta_unfiltered
--   WHERE quality_review_status::text = ANY (ARRAY['approved'::character varying, 'unverified'::character varying]::text[]);

CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT
    id, question_text, question_html, question_latex, question_image_url, question_audio_url,
    option_a, option_b, option_c, option_d, option_e, correct_answer,
    explanation, explanation_video_url, alternative_solutions,
    primary_topic_id, secondary_topics, bloom_level, bloom_category,
    difficulty_level, irt_based_difficulty, student_success_rate, last_difficulty_update,
    difficulty_update_count, irt_discrimination, irt_difficulty, irt_guessing,
    irt_upper_asymptote, is_calibrated, calibration_sample_size, last_calibration_date,
    calibration_quality_score, morphology_complexity, word_count, unique_word_count,
    average_word_length, readability_score, times_asked, times_correct, times_wrong,
    times_skipped, average_response_time, median_response_time, exposure_rate, last_used_date,
    exam_type, subject_area, grade_level, osym_format_compliant, osym_year, quality_score,
    quality_review_status, source_book, source_page, pipeline_metadata,
    created_by, reviewed_by, is_active, is_public, created_at, updated_at,
    embedding, image_ocr_text, image_width, image_height,
    irt_a, irt_b, irt_c, irt_calibrated, irt_method, irt_calibrated_at,
    irt_n_responses, is_calib_pool, soru_hash
FROM v_safe_for_beta_unfiltered
WHERE quality_review_status::text = ANY (ARRAY['approved'::character varying, 'unverified'::character varying]::text[])
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'));

COMMENT ON VIEW v_safe_for_beta IS
'Beta-safe questions. Excludes: pending status, demoted tier_f rows (2026-05-13). See backend/migrations/safe_for_beta_exclude_demoted.sql.';
