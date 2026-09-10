-- D10_safe_for_beta_exclude_sik_bos_ROLLBACK.sql
-- Geri alma: D10'un ekledigi sik_bos disari-atmasini kaldirir, view'i D9'un
-- birakti hale (osym_resmi_kaynak imzasi VAR, sik_bos disari-atmasi YOK)
-- dondurur. Bu dosya calistirilmadan once alembic/versions/
-- 0012_osym_sikki_bos_pasif.py'nin downgrade()'i cagrilmis olmali (aksi
-- halde is_active=false birakilan 28 soru view'e donerken is_active hala
-- false kalir -- tutarsizlik).

CREATE OR REPLACE VIEW v_safe_for_beta AS
 SELECT id,
    soru_hash,
    primary_topic_id,
    is_active,
    is_public,
    created_by,
    reviewed_by,
    created_at,
    updated_at,
    is_ai_generated,
    review_status,
    question_text,
    question_html,
    question_latex,
    question_image_url,
    image_ocr_text,
    image_width,
    image_height,
    question_audio_url,
    option_a,
    option_b,
    option_c,
    option_d,
    option_e,
    correct_answer,
    explanation,
    explanation_video_url,
    alternative_solutions,
    secondary_topics,
    bloom_level,
    bloom_category,
    exam_type,
    subject_area,
    grade_level,
    osym_format_compliant,
    osym_year,
    source_book,
    source_page,
    pipeline_metadata,
    misconception_tags,
    solution_steps,
    similar_question_ids,
    morphology_complexity,
    word_count,
    unique_word_count,
    average_word_length,
    readability_score,
    difficulty_level,
    irt_based_difficulty,
    student_success_rate,
    last_difficulty_update,
    difficulty_update_count,
    irt_discrimination,
    irt_difficulty,
    irt_guessing,
    irt_upper_asymptote,
    is_calibrated,
    calibration_sample_size,
    last_calibration_date,
    calibration_quality_score,
    irt_a,
    irt_b,
    irt_c,
    irt_calibrated,
    irt_calibrated_at,
    irt_n_responses,
    irt_method,
    is_calib_pool,
    embedding,
    times_asked,
    times_correct,
    times_wrong,
    times_skipped,
    average_response_time,
    median_response_time,
    exposure_rate,
    last_used_date,
    quality_score,
    quality_review_status,
    reviewed_at
   FROM v_safe_for_beta_unfiltered
  WHERE (quality_review_status::text = ANY (ARRAY['human_verified'::character varying::text, 'auto_judged_high'::character varying::text]))
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'demoted_at'::text)
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'ai_extras'::text OR NOT (pipeline_metadata::jsonb -> 'ai_extras'::text) ? 'topic_match_quality'::text OR ((pipeline_metadata::jsonb -> 'ai_extras'::text) ->> 'topic_match_quality'::text) <> 'fallback'::text)
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'match_tier'::text OR ((pipeline_metadata::jsonb ->> 'match_tier'::text) <> ALL (ARRAY['tier1_page_inline'::text, 'tier1b_position_page_inline'::text])))
    AND (pipeline_metadata IS NOT NULL AND (
           (pipeline_metadata::jsonb ->> 'student_coherent'::text) = 'true'::text
        OR pipeline_metadata::jsonb ? 'verified_provisional'::text
        OR pipeline_metadata::jsonb ? 'consensus_2signal_run'::text
        OR pipeline_metadata::jsonb ? 'math_promote_run'::text
        OR pipeline_metadata::jsonb ? 'verbal_promote_run'::text
        OR pipeline_metadata::jsonb ? 'osym_resmi_kaynak'::text
    ))
    AND (is_ai_generated = false OR review_status::text = 'APPROVED'::text);

COMMENT ON VIEW v_safe_for_beta IS
'Beta-safe questions. D5 (13 Haz 2026) + gate2b/wave1 dalgalari (D6-D8, yalniz scratch''ta) + D9 (10 Eyl 2026): OSYM resmi kitapcik kaynakli sorular icin osym_resmi_kaynak imzasi eklendi. Bkz: backend/migrations/D9_safe_for_beta_osym_resmi_kaynak.sql, backend/scripts/osym/kitapcik_ithal.py, backend/alembic/versions/0011_osym_aktiflestirme.py.';
