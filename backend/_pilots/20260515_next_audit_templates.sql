-- =============================================================================
-- 20260515_next_audit_templates.sql
-- Date: 2026-05-15
-- Author: Claude session (Session 156)
-- Purpose: C1-C3 audit'leri için sample TSV üretici.
--
-- Önkoşul: Convention v2 deploy edilmiş (D2+D3+D4).
--
-- \copy (client-side) tek satır olmalı — psql multi-line parse etmiyor.
-- Bu yüzden SELECT'ler ZORUNLU OLARAK tek satıra sıkıştırıldı.
-- Okunabilirlik için CTE/yorumsuz versiyon; orijinal multi-line plan:
-- backend/_pilots/20260515_next_audit_templates_VERBOSE.sql (referans için)
--
-- Reproducible seed: md5(id::text || '<audit_label>')
--
-- Kullanım: psql -p 5434 -U postgres -d kiro2 -f bu_dosya.sql
-- =============================================================================


-- Türkçe soru metinleri için UTF-8 client encoding (yoksa WIN1254 default crash eder)
SET client_encoding = 'UTF8';


-- C1: missing_diagram flag güvenilirliği (30 örnek)
\copy (SELECT id::text AS id, source_book, source_page, LEFT(question_text, 200) AS question_text, question_image_url, pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS has_diagram_flag FROM question_bank WHERE is_active = TRUE AND quality_review_status = 'unverified' AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram')::boolean = TRUE AND question_image_url IS NULL ORDER BY md5(id::text || 'audit-C1-missing-diagram') LIMIT 30) TO 'C:/Users/husey/kiro2/backend/_pilots/20260515_audit_C1_RAW.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true);


-- C2: wrong_answer Mat/Geometri konsantrasyonu (50 örnek)
\copy (SELECT id::text AS id, subject_area, source_book, source_page, LEFT(question_text, 200) AS question_text, option_a, option_b, option_c, option_d, option_e, correct_answer, pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' AS topic_quality, pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS has_diagram FROM question_bank WHERE is_active = TRUE AND quality_review_status = 'unverified' AND subject_area IN ('MATEMATIK', 'GEOMETRI') AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram')::boolean = FALSE ORDER BY md5(id::text || 'audit-C2-wrong-answer-math') LIMIT 50) TO 'C:/Users/husey/kiro2/backend/_pilots/20260515_audit_C2_RAW.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true);


-- C3: legacy_v3_unaudited 30-örnek tekrar audit
\copy (SELECT id::text AS id, subject_area, source_book, source_page, LEFT(question_text, 200) AS question_text, option_a, option_b, option_c, option_d, option_e, correct_answer FROM question_bank WHERE is_active = TRUE AND quality_review_status = 'legacy_v3_unaudited' ORDER BY md5(id::text || 'audit-C3-legacy-retest') LIMIT 30) TO 'C:/Users/husey/kiro2/backend/_pilots/20260515_audit_C3_RAW.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true);


-- Pre-flight sayım kontrolü (audit öncesi)
SELECT quality_review_status, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct FROM question_bank WHERE is_active = TRUE GROUP BY quality_review_status ORDER BY n DESC;


-- Audit sonrası: scoring şablonu (Hüseyin elle dolduracak)
-- _RAW.tsv dosyalarına şu kolonlar eklenecek manuel:
--   verdict        : 'pass' | 'fail' | 'unclear'
--   error_type     : 'missing_diagram' | 'ocr' | 'wrong_answer' | 'topic' | 'other' | NULL
--   notes          : serbest metin
-- Sonra _SCORING.tsv olarak kaydet, RESULT artifact'ı yaz.
