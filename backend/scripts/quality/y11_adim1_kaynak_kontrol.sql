\encoding UTF8
-- ADIM 1 kaynak kontrolu (kiro2_temp'te kosulur). SALT OKUNUR.
-- NOT: `th.*` KULLANMA — topic_hierarchy'de json kolon var ve UNION onu
-- karsilastiramiyor ("could not identify an equality operator for type json").
-- Acik kolon listesi zorunlu.
WITH RECURSIVE kk AS (
    SELECT DISTINCT primary_topic_id AS id
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true AND subject_area = 'KIMYA'
),
z AS (
    SELECT th.id, th.parent_id, th.code, th.name_tr, th.level,
           th.osym_relevance, th.osym_frequency, th.total_questions,
           th.average_difficulty, th.is_active, th.subject_area
    FROM topic_hierarchy th JOIN kk ON kk.id = th.id
    UNION
    SELECT p.id, p.parent_id, p.code, p.name_tr, p.level,
           p.osym_relevance, p.osym_frequency, p.total_questions,
           p.average_difficulty, p.is_active, p.subject_area
    FROM z JOIN topic_hierarchy p ON p.id = z.parent_id
)
SELECT 'tasinacak konu = ' || count(*) FROM z
UNION ALL SELECT '== canlinin 9 ZORUNLU kolonu kaynakta NULL mu =='
UNION ALL SELECT '  id                 NULL = ' || count(*) FILTER (WHERE id IS NULL) FROM z
UNION ALL SELECT '  code               NULL = ' || count(*) FILTER (WHERE code IS NULL) FROM z
UNION ALL SELECT '  name_tr            NULL = ' || count(*) FILTER (WHERE name_tr IS NULL) FROM z
UNION ALL SELECT '  level              NULL = ' || count(*) FILTER (WHERE level IS NULL) FROM z
UNION ALL SELECT '  is_active          NULL = ' || count(*) FILTER (WHERE is_active IS NULL) FROM z
UNION ALL SELECT '  osym_relevance     NULL = ' || count(*) FILTER (WHERE osym_relevance IS NULL) FROM z
UNION ALL SELECT '  osym_frequency     NULL = ' || count(*) FILTER (WHERE osym_frequency IS NULL) FROM z
UNION ALL SELECT '  total_questions    NULL = ' || count(*) FILTER (WHERE total_questions IS NULL) FROM z
UNION ALL SELECT '  average_difficulty NULL = ' || count(*) FILTER (WHERE average_difficulty IS NULL) FROM z
UNION ALL SELECT '== code degerleri (canli ile cakisma kontrolu icin) =='
UNION ALL SELECT '  ' || string_agg(code, ', ' ORDER BY code) FROM z;
