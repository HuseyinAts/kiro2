\encoding UTF8
-- ④ ADIM 1 ON-OLCUMU — kiro2_temp'te kosulur. SALT OKUNUR.
-- KIMYA'nin 17 konusu + PARENT ZINCIRI (gecisli kapanis) ne kadar tutuyor?
WITH RECURSIVE kimya_konu AS (
    SELECT DISTINCT primary_topic_id AS id
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true AND subject_area = 'KIMYA'
),
zincir AS (
    -- taban: 17 konu
    SELECT th.id, th.parent_id, th.code, th.name_tr, th.level, 0 AS derinlik
    FROM topic_hierarchy th JOIN kimya_konu k ON k.id = th.id
    UNION
    -- yukari dogru: ebeveynler
    SELECT p.id, p.parent_id, p.code, p.name_tr, p.level, z.derinlik + 1
    FROM zincir z JOIN topic_hierarchy p ON p.id = z.parent_id
)
SELECT '== ZINCIR OZETI =='
UNION ALL SELECT '  taban konu (KIMYA sorularinin dogrudan bagli oldugu) : '
       || (SELECT count(*) FROM kimya_konu)
UNION ALL SELECT '  zincirle birlikte TOPLAM tasinacak konu             : '
       || (SELECT count(DISTINCT id) FROM zincir)
UNION ALL SELECT '  bunun ebeveyn olarak EKLENEN                        : '
       || ((SELECT count(DISTINCT id) FROM zincir) - (SELECT count(*) FROM kimya_konu))
UNION ALL SELECT '  en derin zincir adimi                               : '
       || (SELECT max(derinlik) FROM zincir)
UNION ALL SELECT ''
UNION ALL SELECT '== KOKSUZ KALAN VAR MI (parent_id dolu ama ebeveyn zincirde yok) =='
UNION ALL SELECT '  yetim ebeveyn referansi : ' || count(*)
  FROM zincir z
 WHERE z.parent_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM zincir p WHERE p.id = z.parent_id)
UNION ALL SELECT ''
UNION ALL SELECT '== TASINACAK KONULAR (level sirasi = INSERT sirasi) =='
UNION ALL SELECT '  L' || level || '  ' || rpad(coalesce(code,'-'), 14)
       || left(coalesce(name_tr,'-'), 38)
       || CASE WHEN parent_id IS NULL THEN '   [kok]' ELSE '' END
  FROM (SELECT DISTINCT id, parent_id, code, name_tr, level FROM zincir) x
 ORDER BY 1;
