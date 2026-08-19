\encoding UTF8
-- ④ ADIM 0 — YEDEK. Canli kiro2'de kosulur. ADDITIVE: mevcut hicbir satira dokunmaz.
-- Once ON-KONTROL: yedek zaten varsa GURULTULU dur (sessizce ezme -> geri alma yolu kaybolur).
\set ON_ERROR_STOP on

SELECT '== ON-KONTROL: mevcut yedek tablolari =='
UNION ALL
SELECT '  ' || table_name || '  (VAR — ADIM 0 ATLANMALI ya da once elle temizlenmeli)'
  FROM information_schema.tables
 WHERE table_schema = 'public' AND table_name LIKE '%\_y11\_oncesi';

SELECT '== KAYNAK SATIR SAYILARI (yedek oncesi) =='
UNION ALL SELECT '  question_bank       : ' || count(*) FROM question_bank
UNION ALL SELECT '  question_content    : ' || count(*) FROM question_content
UNION ALL SELECT '  question_metadata   : ' || count(*) FROM question_metadata
UNION ALL SELECT '  question_statistics : ' || count(*) FROM question_statistics
UNION ALL SELECT '  topic_hierarchy     : ' || count(*) FROM topic_hierarchy;
