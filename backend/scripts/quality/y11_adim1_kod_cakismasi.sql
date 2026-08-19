\encoding UTF8
-- ADIM 1 — KOD CAKISMASI olcumu (canli kiro2'de kosulur). SALT OKUNUR.
-- Kaynaktaki 18 konunun 4'unun kodu canlida zaten var: FIZ, GEN, KIM, MAT.
-- Kopyalamak yerine ESLEME gerekiyor -> sorularin primary_topic_id'si YENIDEN
-- HARITALANMALI. Bu sorgu esleme tablosunun canli ayagini verir.
SELECT '== code UNIQUE mi (kisit var mi) =='
UNION ALL
SELECT '  ' || conname || ' : ' || pg_get_constraintdef(oid)
  FROM pg_constraint
 WHERE conrelid = 'topic_hierarchy'::regclass AND contype IN ('u','p')
UNION ALL SELECT '  (kisit listesi yukarida; bos ise code UNIQUE DEGIL)'
UNION ALL SELECT ''
UNION ALL SELECT '== CANLIDAKI cakisan 4 kodun id/ad/level bilgisi =='
UNION ALL SELECT '  ' || rpad(code, 6) || ' id=' || id
       || '  L' || level || '  ' || coalesce(name_tr, '-')
  FROM topic_hierarchy
 WHERE code IN ('FIZ','GEN','KIM','MAT')
 ORDER BY 1;
