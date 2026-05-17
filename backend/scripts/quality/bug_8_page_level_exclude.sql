-- Bug #8 fix: v_safe_for_beta'dan page-level crop sample'ları çıkar
--
-- Sebep (17 May 2026):
-- Hüseyin ekran görüntüleri (hata/hata 2/) 8/8 sample audit:
--   - 4/8 sample'da image içinde original options görünüyor (solution leak)
--   - 4/8 sample'da text↔image content mismatch (page-level crop'larda)
-- DB audit:
--   - auto_judged_high pool'un %44.5'i page-level crop (37,490 sample)
--   - tier1_page_inline: 20,307
--   - tier1b_position_page_inline: 17,183
--
-- Bu sample'lar beta için BLOCKER:
--   - Solution leak: öğrenci cevabı image'dan görür
--   - Content mismatch: image yanlış soruyu gösterir (Bug #7 ile bağlantılı)
--
-- Fix: v_safe_for_beta WHERE clause'a match_tier exclusion ekle.
-- Trade-off: pool ~23,497 → ~12,000 (yarıya iner) ama kaliteli sorular kalır.
--
-- Geri alma: orijinal view tanımı dosyada (alttaki ROLLBACK bölümü)

-- Pre-state
SELECT 'PRE-STATE' AS phase, COUNT(*) AS count FROM v_safe_for_beta;

-- Drop & recreate (CREATE OR REPLACE değil, çünkü kolonlar değişmiyor ama WHERE değişiyor)
CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT *
FROM v_safe_for_beta_unfiltered
WHERE (quality_review_status::text = ANY (ARRAY['human_verified'::character varying, 'auto_judged_high'::character varying]::text[]))
  AND (pipeline_metadata IS NULL OR NOT pipeline_metadata::jsonb ? 'demoted_at'::text)
  AND (pipeline_metadata IS NULL
       OR NOT pipeline_metadata::jsonb ? 'ai_extras'::text
       OR NOT (pipeline_metadata::jsonb -> 'ai_extras'::text) ? 'topic_match_quality'::text
       OR ((pipeline_metadata::jsonb -> 'ai_extras'::text) ->> 'topic_match_quality'::text) <> 'fallback'::text)
  -- Bug #8 fix (17 May 2026): page-level crop sample'ları HARIÇ
  -- (image içinde original options görünüyor — solution leak + content mismatch)
  AND (pipeline_metadata IS NULL
       OR NOT pipeline_metadata::jsonb ? 'match_tier'::text
       OR (pipeline_metadata::jsonb ->> 'match_tier'::text) NOT IN
           ('tier1_page_inline', 'tier1b_position_page_inline'));

-- Post-state
SELECT 'POST-STATE' AS phase, COUNT(*) AS count FROM v_safe_for_beta;

-- Detay: ne kadar düştü, hangi konularda
SELECT subject_area, COUNT(*) AS count
FROM v_safe_for_beta
GROUP BY 1
ORDER BY 2 DESC;
