\encoding UTF8
-- ④ GOC RISK OLCUMU — kiro2_temp tarafinda kosulur.
-- S225'te `toplu_soru_ekle` bu dort sinifin ucunde seri olarak dusmustu.
--
-- R1 difficulty_level enum ETIKETLERI    (S225 kusur 4: 'medium' vs PG 'MEDIUM')
-- R2 primary_topic_id FK karsiligi       (canli topic_hierarchy'de var mi?)
-- R3 soru_hash carpismasi                (uq_qb_soru_hash_active kismi indeksi)
-- R4 id carpismasi                       (temp UUIDv5 vs canli UUIDv4)
SELECT '== R1: difficulty_level DEGERLERI (kaynak) =='
UNION ALL SELECT '  ' || coalesce(difficulty_level::text,'<NULL>') || ' : ' || count(*)
  FROM question_bank
 WHERE quality_review_status IN ('human_verified','auto_judged_high')
   AND is_active = true AND subject_area = 'KIMYA'
 GROUP BY difficulty_level
UNION ALL SELECT ''
UNION ALL SELECT '== R2: primary_topic_id — kac FARKLI deger (kaynak, KIMYA) =='
UNION ALL SELECT '  distinct = ' || count(DISTINCT primary_topic_id)
       || '   NULL = ' || count(*) FILTER (WHERE primary_topic_id IS NULL)
  FROM question_bank
 WHERE quality_review_status IN ('human_verified','auto_judged_high')
   AND is_active = true AND subject_area = 'KIMYA'
UNION ALL SELECT ''
UNION ALL SELECT '== R3: soru_hash — kaynak ici benzersizlik (KIMYA) =='
UNION ALL SELECT '  satir = ' || count(*) || '   distinct hash = ' || count(DISTINCT soru_hash)
       || '   NULL = ' || count(*) FILTER (WHERE soru_hash IS NULL)
  FROM question_bank
 WHERE quality_review_status IN ('human_verified','auto_judged_high')
   AND is_active = true AND subject_area = 'KIMYA'
UNION ALL SELECT ''
UNION ALL SELECT '== R4: id surumu (kaynak, KIMYA) =='
UNION ALL SELECT '  UUIDv5 = ' || count(*) FILTER (WHERE substring(id::text, 15, 1) = '5')
       || '   UUIDv4 = ' || count(*) FILTER (WHERE substring(id::text, 15, 1) = '4')
       || '   diger = ' || count(*) FILTER (WHERE substring(id::text, 15, 1) NOT IN ('4','5'))
  FROM question_bank
 WHERE quality_review_status IN ('human_verified','auto_judged_high')
   AND is_active = true AND subject_area = 'KIMYA';
