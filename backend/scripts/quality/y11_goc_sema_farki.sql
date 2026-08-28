\encoding UTF8
-- ④ GOC ON-OLCUMU: hedef 4-tablo split semasinin ZORUNLU (NOT NULL, defaultsuz)
-- kolonlari neler, ve kaynakta (kiro2_temp.question_bank) karsiligi var mi?
-- Bu sorgu CANLI kiro2'de kosulur; kaynak kolon listesi disaridan verilir.
WITH hedef AS (
    SELECT c.table_name, c.column_name, c.data_type, c.is_nullable,
           c.column_default
    FROM information_schema.columns c
    WHERE c.table_schema = 'public'
      AND c.table_name IN ('question_bank','question_content',
                           'question_metadata','question_statistics')
),
zorunlu AS (
    SELECT * FROM hedef
    WHERE is_nullable = 'NO' AND column_default IS NULL
)
SELECT '== HEDEF TABLO KOLON SAYILARI =='
UNION ALL SELECT '  ' || table_name || ' : ' || count(*) || ' kolon, '
       || count(*) FILTER (WHERE is_nullable='NO') || ' NOT NULL, '
       || count(*) FILTER (WHERE is_nullable='NO' AND column_default IS NULL)
       || ' ZORUNLU (defaultsuz)'
  FROM hedef GROUP BY table_name
UNION ALL SELECT ''
UNION ALL SELECT '== ZORUNLU KOLONLAR (NOT NULL + default YOK) — goc bunlari DOLDURMALI =='
UNION ALL SELECT '  ' || rpad(table_name, 22) || rpad(column_name, 28) || data_type
  FROM zorunlu ORDER BY 1;
