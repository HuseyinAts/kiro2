-- P0.2 — A-bias kontaminasyon doğrulama · BATCH 1 (recon, salt-okunur)
-- Amaç: yol haritası P0.2 — S195+S198'de otomatik-consensus ile auto_judged_high'a
-- geri-promote edilen ~787 sorunun A-bias kontamine olup olmadığını ölçmeden ÖNCE
-- ground-truth (status dağılımı + marker'lar + backup tabloları) kur.
-- audit-methodology.md: recon ÖNCE, derin örnekleme SONRA. Truncate YOK.
-- Çalıştır: psql -p 5434 -U postgres -d kiro2 -f backend/scripts/quality/p0_2_abias_recon.sql

\echo '=== Q1: question_bank status dağılımı (canlı, MEMORY snapshot drift kontrolü) ==='
SELECT quality_review_status, COUNT(*) AS n
FROM question_bank
WHERE is_active
GROUP BY quality_review_status
ORDER BY n DESC;

\echo ''
\echo '=== Q2: auto_judged_high TÜM kohort cevap-şık dağılımı (A+E baseline) ==='
SELECT correct_answer,
       COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM question_bank
WHERE quality_review_status = 'auto_judged_high' AND is_active
GROUP BY correct_answer
ORDER BY correct_answer;

\echo ''
\echo '=== Q3: auto_judged_high pipeline_metadata marker anahtarları (denetim trail) ==='
-- pipeline_metadata tipi json → jsonb cast gerekli (S182 notu)
SELECT key, COUNT(*) AS n
FROM question_bank,
     LATERAL jsonb_object_keys(pipeline_metadata::jsonb) AS key
WHERE quality_review_status = 'auto_judged_high'
  AND is_active
  AND pipeline_metadata IS NOT NULL
GROUP BY key
ORDER BY n DESC;

\echo ''
\echo '=== Q4: v_safe_for_beta canlı sayı (docs çelişkisi 0/12,362/10,535) ==='
SELECT COUNT(*) AS v_safe_for_beta_count FROM v_safe_for_beta;

\echo ''
\echo '=== Q5: denetim backup tabloları mevcut mu (rollback + kohort kaynağı) ==='
SELECT table_name
FROM information_schema.tables
WHERE table_name LIKE 'question_bank%backup%'
ORDER BY table_name;

\echo ''
\echo '=== Q6: S198 otomatik-consensus kohortu cevap dağılımı (kontamine mi?) ==='
-- Hata verirse (tablo/kolon adı farklı) Q5 çıktısına göre Batch 2 düzeltilecek.
SELECT qb.correct_answer,
       COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM question_bank qb
JOIN question_bank_s198_curator_backup_20260527 b ON b.id = qb.id
WHERE qb.quality_review_status = 'auto_judged_high'
GROUP BY qb.correct_answer
ORDER BY qb.correct_answer;
