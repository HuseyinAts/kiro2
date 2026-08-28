\encoding UTF8
-- ADIM 1 son kapi: canli topic_hierarchy'nin ZORUNLU kolonlari neler?
-- (bu dosya CANLI kiro2'de kosulur)
SELECT '== canli topic_hierarchy ZORUNLU kolonlar (NOT NULL, defaultsuz) =='
UNION ALL
SELECT '  ' || rpad(column_name, 22) || data_type
  FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'topic_hierarchy'
   AND is_nullable = 'NO' AND column_default IS NULL
 ORDER BY 1;
