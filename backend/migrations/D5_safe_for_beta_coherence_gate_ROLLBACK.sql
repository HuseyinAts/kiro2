-- ROLLBACK for D5 coherence gate. Restores v_safe_for_beta to the pre-D5 (status-only) definition.
-- Apply this to undo D5_safe_for_beta_coherence_gate.sql.
CREATE OR REPLACE VIEW v_safe_for_beta AS
 SELECT id, question_text, question_html, question_latex, question_image_url, question_audio_url,
    option_a, option_b, option_c, option_d, option_e, correct_answer, explanation, explanation_video_url,
    alternative_solutions, primary_topic_id, secondary_topics, bloom_level, bloom_category, difficulty_level,
    irt_based_difficulty, student_success_rate, last_difficulty_update, difficulty_update_count,
    irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote, is_calibrated,
    calibration_sample_size, last_calibration_date, calibration_quality_score, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, times_asked, times_correct,
    times_wrong, times_skipped, average_response_time, median_response_time, exposure_rate, last_used_date,
    exam_type, subject_area, grade_level, osym_format_compliant, osym_year, quality_score,
    quality_review_status, source_book, source_page, pipeline_metadata, created_by, reviewed_by, is_active,
    is_public, created_at, updated_at, embedding, image_ocr_text, image_width, image_height, irt_a, irt_b,
    irt_c, irt_calibrated, irt_method, irt_calibrated_at, irt_n_responses, is_calib_pool, soru_hash
   FROM v_safe_for_beta_unfiltered
  WHERE (quality_review_status::text = ANY (ARRAY['human_verified'::character varying::text, 'auto_judged_high'::character varying::text]))
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'demoted_at'::text)
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'ai_extras'::text OR NOT (pipeline_metadata::jsonb -> 'ai_extras'::text) ? 'topic_match_quality'::text OR ((pipeline_metadata::jsonb -> 'ai_extras'::text) ->> 'topic_match_quality'::text) <> 'fallback'::text)
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'match_tier'::text OR ((pipeline_metadata::jsonb ->> 'match_tier'::text) <> ALL (ARRAY['tier1_page_inline'::text, 'tier1b_position_page_inline'::text])));
