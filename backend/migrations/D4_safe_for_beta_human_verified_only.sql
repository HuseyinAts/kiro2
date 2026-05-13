-- D4_safe_for_beta_human_verified_only.sql
-- Date: 2026-05-15
-- Author: Claude session (Session 156)
-- Purpose: v_safe_for_beta view'unu Convention v2 ile uyumlu hale getir.
--   'approved' ve 'legacy_v3_unaudited' artık beta-safe değil; sadece
--   gerçek manuel onay (`human_verified`) ve geleceğe `auto_judged_high`.
--
-- Önkoşul: D2 + Alembic migration qrs_v2_20260515 çalıştırılmış olmalı.
--
-- View chain (sonrası):
--   v_safe_for_beta (wrapper, post-D4):
--     WHERE quality_review_status IN ('human_verified', 'auto_judged_high')
--       AND NOT demoted_at
--       AND NOT fallback topic_match
--   v_safe_for_beta_unfiltered (base, unchanged):
--     pending exclude + word_count + regex + parity
--   question_bank (source)
--
-- Pre-deploy expected counts:
--   v_safe_for_beta (current, pre-D4):      81,760
--   v_safe_for_beta (post-D4, expected):    0  <-- doğru bir sıfır
--
-- Beklenen 0 satır: Şu anda hiç 'human_verified' satır yok. Manuel
--   curator workflow kurulana kadar bu doğal durum. Pool yeniden
--   inşa edilmeli.
--
-- ROLLBACK (önceki state — fallback exclude dahil):
--   CREATE OR REPLACE VIEW v_safe_for_beta AS
--   SELECT ... FROM v_safe_for_beta_unfiltered
--   WHERE quality_review_status::text = ANY (ARRAY['approved', 'unverified']::text[])
--     AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'))
--     AND (
--       pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'ai_extras')
--       OR NOT (pipeline_metadata::jsonb -> 'ai_extras' ? 'topic_match_quality')
--       OR pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' != 'fallback'
--     );

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
WHERE quality_review_status IN ('human_verified', 'auto_judged_high')
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'))
  AND (
    pipeline_metadata IS NULL
    OR NOT (pipeline_metadata::jsonb ? 'ai_extras')
    OR NOT (pipeline_metadata::jsonb -> 'ai_extras' ? 'topic_match_quality')
    OR pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' != 'fallback'
  );

COMMENT ON VIEW v_safe_for_beta IS
'Beta-safe questions. Convention v2 (2026-05-15): yalnızca human_verified veya auto_judged_high kabul. Eski approved (hardcoded literal) %87 hatalı çıktığı için yasaklandı. Bkz: backend/migrations/D4_safe_for_beta_human_verified_only.sql, docs/quality_review_status_convention.md';
