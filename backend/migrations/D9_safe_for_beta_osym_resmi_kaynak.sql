-- D9_safe_for_beta_osym_resmi_kaynak.sql
-- Date: 2026-09-10
-- Author: Claude session (OSYM kitapcik aktiflestirme)
--
-- NUMARALANDIRMA NOTU: D6/D7/D8 bu dizinde YOK -- gate2b/wave1 kampanyalari
-- sirasinda scripts/quality/_gate2b/D6_part2_view.sql,
-- scripts/quality/_wave1/D7_part2_view.sql, D8_part2_view.sql adlariyla
-- CANLIYA UYGULANDI ama backend/migrations/ altina hic tasinmadi (repo'da
-- izi yalniz scratch dizinlerinde var). Canli view su an D5 + o uc dalganin
-- toplam etkisini tasiyor (asagidaki "ONCEKI (canli, 10 Eyl 2026 olcumu)"
-- bloguyla dogrulandi). Bu dosya o gap'i devam ettirmemek icin D9 aldi;
-- D6-D8 numaralari kasitli bos birakildi (tarihi carpitmamak icin).
--
-- AMAC
-- ----
-- v_safe_for_beta'nin "coherence signal" dalina (D5 + wave1) yeni bir
-- imza ekle: `osym_resmi_kaynak`. OSYM'nin resmi 2025 TYT/AYT
-- kitapciklarindan (backend/scripts/osym/kitapcik_cikar.py +
-- kitapcik_ithal.py) ithal edilen 291 soru bu imzayi tasiyor
-- (pipeline_metadata->>'osym_resmi_kaynak' = 'true').
--
-- NEDEN AYRI IMZA, MEVCUTLARDAN BIRI DEGIL
-- -----------------------------------------
-- student_coherent / verified_provisional / consensus_2signal_run /
-- math_promote_run / verbal_promote_run -- hepsi AI-uretilmis/OCR
-- icerigin dogrulugunu olcen sinyaller (blind-solve, coklu-cozucu
-- konsensus, vb.). OSYM ithalati bunlarin HICBIRINDEN gecmedi -- farkli
-- ve daha guclu bir kaynaktan geliyor: OSYM'nin kendi yayinladigi resmi
-- cevap anahtari + kolon-farkinda PDF cikarici (tests/fast/test_osym_kitapcik.py,
-- 125/125 TYT + 166/166 AYT tam eslesme). Var olan bir imzayi odunc almak
-- (orn. "consensus_2signal_run" yazmak) provenance'i yanlis temsil eder;
-- ileride "bu soru neden guvenli" sorusuna yanlis cevap verir.
--
-- ONCEKI (canli, 10 Eyl 2026 olcumu, pg_get_viewdef) -- ilgili dal:
--   AND pipeline_metadata IS NOT NULL AND (
--         (pipeline_metadata::jsonb ->> 'student_coherent') = 'true'
--      OR pipeline_metadata::jsonb ? 'verified_provisional'
--      OR pipeline_metadata::jsonb ? 'consensus_2signal_run'
--      OR pipeline_metadata::jsonb ? 'math_promote_run'
--      OR pipeline_metadata::jsonb ? 'verbal_promote_run'
--   )
--   AND (is_ai_generated = false OR review_status = 'APPROVED')
--
-- SONRA: yukaridaki parantezin icine `OR pipeline_metadata::jsonb ?
-- 'osym_resmi_kaynak'` eklendi. is_ai_generated=false zaten OSYM
-- satirlari icin true (kitapcik_ithal.py::_QB is_ai_generated=FALSE
-- yazar) -- o dal zaten OSYM'yi tutuyordu; degisen yalniz coherence dali.
--
-- OLCUM (uygulamadan once, 10 Eyl 2026): v_safe_for_beta = 4.959 satir.
-- Beklenen etki: +291 (OSYM 2025 TYT 125 + AYT 166), digeri degismez
-- (yeni dal yalniz `osym_resmi_kaynak` anahtarini tasiyan satirlari
-- ekler, mevcut hicbir satiri disarida birakmaz -- OR eklemek, ustundeki
-- AND'lerle birlikte, kumeyi yalniz genisletir).
--
-- ROLLBACK: D9_safe_for_beta_osym_resmi_kaynak_ROLLBACK.sql (bu dosyanin
-- calistirilmadan onceki canli tanimin birebir kopyasi).

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
