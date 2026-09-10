-- D10_safe_for_beta_exclude_sik_bos.sql
-- Date: 2026-09-10
-- Author: Claude session (OSYM kitapcik aktiflestirme, D9'un devami)
--
-- BULUS
-- -----
-- D9 push oncesi yerel dogrulama sirasinda ders-zorlayici pre-push hook'u
-- (tests/integration/test_icerik_gecerliligi.py::
-- test_k2_anahtar_dolu_bir_sikka_isaret_ediyor) 28 satirin cevap anahtarinin
-- GECERSIZ oldugunu buldu: dogru sikkin metni BOS. Teshis (bkz.
-- backend/_ci_art/_r5_teshis.py, _bayrak_analiz.py):
--   * 28/28 satir OSYM 2025 TYT/AYT ithalati (source_book), hepsi MATEMATIK.
--   * 28/28 satir kitapcik_ithal.py'nin IMPORT ANINDA kendi koydugu
--     pipeline_metadata->'bayraklar' isaretinde 'sik_bos' tasiyor.
--   * BIREBIR ORTUSME: havuzdaki (5250 satir) TUM R5 (anahtar-gecersiz)
--     hatalari bu 28 satirdan geliyor, sik_bos disinda R5 veren SIFIR satir
--     var; sik_bos tasiyip R5 vermeyen de SIFIR satir var.
--
-- KOK NEDEN: bu sorularin dogru sikki bir GORSEL/GRAFIK (orn. "hangi grafik
-- ... gosterir" tipi sorularda sik metni degil bir sekil) -- import script'i
-- bunu ithalat aninda saptayip bayrakladi ama D9 (osym_resmi_kaynak imzasi)
-- bu 28 satiri elemeden butun 291'i tek imzayla ice aldi. KUSUR GERCEK:
-- bu 28 soru mevcut metin-tabanli sunum katmaninda hicbir ogrenci
-- tarafindan yanitlanamaz (bos sik metnine tiklamak anlamsiz) -- test
-- bayat degil, D9'un kapsam hatasi.
--
-- DUZELTME
-- --------
-- Coherence-signal dalina DOKUNMUYORUM (osym_resmi_kaynak imzasi hala
-- gecerli -- bu 28 sorunun cevap HARFI hala resmi kaynaktan dogrulanmis,
-- sorun harfin dogrulugu degil sikkin metninin eksikligi). Bunun yerine
-- kapiya YENI, bagimsiz bir disari-atma ekleniyor (mevcut match_tier/
-- ai_extras disari-atmalariyla ayni desende): pipeline_metadata->'bayraklar'
-- icinde 'sik_bos' tasiyan hicbir satir kapidan gecemez -- kaynagi ne
-- olursa olsun (yalniz OSYM'e ozel degil, ileride ayni bayragi tasiyan
-- baska icerik icin de gecerli genel bir kural).
--
-- is_active AYRICA duzeltiliyor (bkz. alembic/versions/0012_osym_sikki_bos_pasif.py)
-- -- kapi zaten disliyor ama is_active=true birakmak DB'yi okuyan baska
-- araclara (admin panel, gelecek migration) yanlis bilgi verir.
--
-- OLCUM (uygulamadan once, dogrulama sorgusu backend/_ci_art/_d10_dogrula.py):
--   simdiki toplam=5250 -> beklenen=5222 (-28)
--   OSYM kalan: 291 -> 263 (28'i disarida, geri kalan 263 etkilenmiyor)
--
-- ROLLBACK: D10_safe_for_beta_exclude_sik_bos_ROLLBACK.sql (D9'un canli
-- tanimininin birebir kopyasi -- bu dosya calistirilmadan onceki durum).

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
    AND (is_ai_generated = false OR review_status::text = 'APPROVED'::text)
    AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'bayraklar'::text OR NOT (pipeline_metadata::jsonb -> 'bayraklar'::text) ? 'sik_bos'::text);

COMMENT ON VIEW v_safe_for_beta IS
'Beta-safe questions. D5 (13 Haz 2026) + gate2b/wave1 dalgalari (D6-D8, yalniz scratch''ta) + D9 (10 Eyl 2026, osym_resmi_kaynak imzasi) + D10 (10 Eyl 2026, sik_bos disari-atma -- bos sik metnine sahip sorular kapiyi gecemez). Bkz: backend/migrations/D9_safe_for_beta_osym_resmi_kaynak.sql, D10_safe_for_beta_exclude_sik_bos.sql, backend/alembic/versions/0012_osym_sikki_bos_pasif.py.';
