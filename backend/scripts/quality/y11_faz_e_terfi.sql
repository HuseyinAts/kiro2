-- FAZ E — Y11 partilerini ogrenci kapisina AC (pending -> auto_judged_high)
--
-- ONKOSUL (20 Agu 2026 olculdu): terfi TEK BASINA yetmez. `v_safe_for_beta`
-- ayrica `demoted_at` ve `tier1_page_inline` tek-sinyal eslesmeleri disliyor ve
-- bes bayraktan (student_coherent / verified_provisional / consensus_2signal_run /
-- math_promote_run / verbal_promote_run) EN AZ BIRINI sart kosuyor.
-- Simule edildi:
--     y11_kimya_20260820  3.616 -> kapiya 3.291   (elenen 325)
--     y11_mat_tyt_20260820  448 -> kapiya   406   (elenen  42)
--     TOPLAM                                3.697
-- Yani kapi 0 -> ~3.697 olmali. 4.064 DEGIL. Sayi tutmazsa DUR.
--
-- GERI ALMA: `question_statistics_terfi_yedek_20260820` onceki durumu tasir.
--     UPDATE question_statistics qs SET quality_review_status = y.eski
--     FROM question_statistics_terfi_yedek_20260820 y WHERE y.id = qs.id;
--     REFRESH MATERIALIZED VIEW mv_safe_for_beta;
--
-- ⚠️ Bu dosya `psql -f` ile kosulur (Turkce icerik: inline -c bozar).

\pset tuples_only on
\pset format unaligned

BEGIN;

-- 1) Yedek: SADECE terfi edilecek satirlarin ONCEKI durumu
DROP TABLE IF EXISTS question_statistics_terfi_yedek_20260820;
CREATE TABLE question_statistics_terfi_yedek_20260820 AS
SELECT qs.id, qs.quality_review_status AS eski
FROM question_statistics qs
JOIN question_metadata qm ON qm.id = qs.id
WHERE qm.pipeline_metadata->>'y11_batch' IN
      ('y11_kimya_20260820', 'y11_mat_tyt_20260820');

SELECT 'yedeklenen = '||count(*) FROM question_statistics_terfi_yedek_20260820;

-- 2) Terfi — id kumesi YEDEKTEN alinir, predikat yeniden degerlendirilmez.
--    "terfi edilen == yedeklenen" bir assert degil, insa ozelligi.
UPDATE question_statistics qs
SET quality_review_status = 'auto_judged_high'
FROM question_statistics_terfi_yedek_20260820 y
WHERE y.id = qs.id;

SELECT 'terfi edilen = '||count(*) FROM question_statistics qs
JOIN question_statistics_terfi_yedek_20260820 y ON y.id = qs.id
WHERE qs.quality_review_status = 'auto_judged_high';

COMMIT;

-- 3) Matview yenile — kapi ancak bundan sonra degisir
REFRESH MATERIALIZED VIEW mv_safe_for_beta;

-- 4) Bagimsiz dogrulama
SELECT '';
SELECT 'KAPI (mv_safe_for_beta) = '||count(*)||'   (beklenen ~3697)' FROM mv_safe_for_beta;
SELECT '  -> KIMYA  = '||count(*) FROM mv_safe_for_beta v
  JOIN question_metadata qm ON qm.id=v.id
  WHERE qm.pipeline_metadata->>'y11_batch'='y11_kimya_20260820';
SELECT '  -> MAT    = '||count(*) FROM mv_safe_for_beta v
  JOIN question_metadata qm ON qm.id=v.id
  WHERE qm.pipeline_metadata->>'y11_batch'='y11_mat_tyt_20260820';
SELECT '  -> DAMGASIZ (olmamali) = '||count(*) FROM mv_safe_for_beta v
  JOIN question_metadata qm ON qm.id=v.id
  WHERE qm.pipeline_metadata->>'y11_batch' IS NULL;
SELECT 'question_bank toplam    = '||count(*) FROM question_bank;
