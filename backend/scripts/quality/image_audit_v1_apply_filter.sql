-- Bug #11 Phase 5 — Beta pool filter rebuild (image_audit_v1 sonrası)
--
-- Çalıştırma sırası:
--   1. image_audit_v1.py --full bitsin (84K audit complete)
--   2. Bu script ile v_safe_for_beta ve frontend filter güncellemeleri
--
-- AUDIT VERDICT MATRIX:
--   "clean"   = Image temiz (sadece şekil/grafik, options yok) → BETA ELIGIBLE
--   "salvage" = Image içinde options var ama content_match=true → re-crop adayı (Phase 6)
--   "reject"  = Content mismatch veya kalitesiz → POOL DIŞI
--   "error"   = Audit başarısız (image missing, Gemini error vb.) → POOL DIŞI

-- ============================================================
-- Pre-check: audit ne kadar kapsadı?
-- ============================================================
SELECT
    'AUDIT COVERAGE' AS phase,
    COUNT(*) FILTER (WHERE pipeline_metadata::jsonb ? 'image_audit_v1') AS audited,
    COUNT(*) FILTER (WHERE NOT (pipeline_metadata::jsonb ? 'image_audit_v1')) AS not_audited,
    COUNT(*) AS total
FROM question_bank
WHERE is_active = TRUE
  AND quality_review_status IN ('human_verified', 'auto_judged_high')
  AND question_image_url IS NOT NULL
  AND question_image_url != '';

-- ============================================================
-- Verdict distribution
-- ============================================================
SELECT
    pipeline_metadata::jsonb -> 'image_audit_v1' ->> 'verdict' AS verdict,
    COUNT(*) AS count
FROM question_bank
WHERE pipeline_metadata::jsonb ? 'image_audit_v1'
GROUP BY 1
ORDER BY 2 DESC;

-- ============================================================
-- v_safe_for_beta — vision audit filter (Phase 5 apply)
-- ============================================================
CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT *
FROM v_safe_for_beta_unfiltered
WHERE (quality_review_status::text = ANY (ARRAY['human_verified'::character varying, 'auto_judged_high'::character varying]::text[]))
  AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'demoted_at'::text)
  AND (pipeline_metadata IS NULL
       OR NOT pipeline_metadata::jsonb ? 'ai_extras'::text
       OR NOT (pipeline_metadata::jsonb -> 'ai_extras'::text) ? 'topic_match_quality'::text
       OR ((pipeline_metadata::jsonb -> 'ai_extras'::text) ->> 'topic_match_quality'::text) <> 'fallback'::text)
  -- Bug #8 (17 May 2026): page-level tier'lar
  AND (pipeline_metadata IS NULL
       OR NOT pipeline_metadata::jsonb ? 'match_tier'::text
       OR (pipeline_metadata::jsonb ->> 'match_tier'::text) NOT IN
           ('tier1_page_inline', 'tier1b_position_page_inline'))
  -- Bug #11 (18 May 2026): Vision audit — sadece "clean" verdict
  -- Image-bound sample'lar audit-passed olmalı; image_url yok ise zaten geçer
  AND (
       question_image_url IS NULL
       OR question_image_url = ''
       OR (
           pipeline_metadata::jsonb ? 'image_audit_v1'
           AND (pipeline_metadata::jsonb -> 'image_audit_v1' ->> 'verdict') = 'clean'
       )
  );

-- ============================================================
-- Post-state: yeni pool boyutu
-- ============================================================
SELECT 'POST-STATE v_safe_for_beta' AS phase, COUNT(*) FROM v_safe_for_beta;

-- ============================================================
-- Per-subject pool (control)
-- ============================================================
SELECT subject_area, COUNT(*)
FROM v_safe_for_beta
GROUP BY 1
ORDER BY 2 DESC;
