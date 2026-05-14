-- audit_task01_db_snapshot.sql
\echo '=== TASK 01: DB INTEGRITY SNAPSHOT ==='

-- 1.1 Toplam/aktif sayım
SELECT
  COUNT(*) AS toplam,
  COUNT(*) FILTER (WHERE is_active=TRUE) AS aktif,
  COUNT(*) FILTER (WHERE is_active=FALSE) AS pasif,
  COUNT(DISTINCT source_book) AS kitap_sayisi
FROM question_bank;

-- 1.2 Image URL Tier dağılımı (aktif satırlar)
SELECT
  CASE
    WHEN pipeline_metadata::jsonb -> 'tier_c_match' IS NOT NULL THEN 'C'
    WHEN pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL THEN 'D'
    WHEN pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL THEN 'E'
    WHEN pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL THEN 'F'
    WHEN pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL THEN 'G'
    WHEN pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL THEN 'H'
    WHEN question_image_url IS NOT NULL THEN 'AB_legacy'
    ELSE 'NULL'
  END AS tier,
  COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1 ORDER BY 2 DESC;

-- 1.3 has_diagram x image_url crosstab
SELECT
  pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS hd,
  CASE WHEN question_image_url IS NULL THEN 'NULL' ELSE 'VAR' END AS img,
  COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1, 2 ORDER BY 1, 2;
