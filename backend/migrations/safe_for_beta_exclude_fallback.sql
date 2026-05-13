-- safe_for_beta_exclude_fallback.sql
-- Date: 2026-05-13
-- Author: Claude session (Asama 2a)
-- Purpose: Exclude v4.14e Gemini Flash rows with topic_match_quality='fallback' from v_safe_for_beta
--
-- Context: L1-L3 analiz (13 May 2026) gosterdi:
--   - v4.14e batch'i 107,516 satir, hepsi Gemini 2.5 Flash uretimi
--   - Topic match dagilimi: %39.3 fallback, %37.4 fuzzy, %23.3 exact
--   - Fallback = konu eslestirmesi BASARISIZ, default'a dustu
--   - View'da fallback: 41,473 (33.7% of beta pool)
--
-- Sebep:
--   1) Gemini Flash yapisal zayifligi (STRATEJI_B_KARAR.md): %15-17 DLQ + duplicate option
--   2) Konu yanlis etiketli sorular IRT calibration ve student feedback'i bozar
--   3) Defansif: bu grup hic kalite review'dan gecmedi
--
-- DIKKAT - Varsayim:
--   "Konu etiketi yanlis = cevap muhtemelen yanlis" hipotezi DOGRUDAN test EDILMEDI.
--   Spot ornek audit Asama 1'deki demoted grup icin yapildi, fallback icin yapilmadi.
--   Eger sonradan fallback cevap dogrulugu yuksek cikarsa (>90%), bu filter ROLLBACK
--   edilebilir. Migration dosyasinin sonundaki rollback komutu hazirdir.
--
-- View layer chain (post-deploy):
--   v_safe_for_beta  --> wrapper: pending exclude + demoted exclude + fallback exclude
--   v_safe_for_beta_unfiltered  --> base: pending + word_count + regex + parity
--   question_bank  --> source
--
-- Pre-deploy counts (verified 2026-05-13 22:45 UTC):
--   v_safe_for_beta total:        123,233
--   fallback in view:              41,473
--   Expected after deploy:         81,760
--
-- NULL handling rationale:
--   `ai_extras->>'topic_match_quality'` NULL doner approved satirlari icin
--   (cunku approved'lar v4.14e degil, ai_extras key'i yok). NULL satirlari TUTUYORUZ
--   defansif olarak: "key yok = fallback degil".
--
-- ROLLBACK (paste into psql to revert to Asama 1 state):
--   CREATE OR REPLACE VIEW v_safe_for_beta AS
--   SELECT * FROM v_safe_for_beta_unfiltered
--   WHERE quality_review_status::text = ANY (ARRAY['approved'::character varying, 'unverified'::character varying]::text[])
--     AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'));

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
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'))
  AND (
    pipeline_metadata IS NULL
    OR NOT (pipeline_metadata::jsonb ? 'ai_extras')
    OR NOT (pipeline_metadata::jsonb -> 'ai_extras' ? 'topic_match_quality')
    OR pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' != 'fallback'
  );

COMMENT ON VIEW v_safe_for_beta IS
'Beta-safe questions. Excludes: pending status, demoted tier_f, v4.14e Gemini fallback topic match (2026-05-13). See backend/migrations/safe_for_beta_exclude_fallback.sql.';
