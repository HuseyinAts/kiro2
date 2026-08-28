\encoding UTF8
-- ADIM 1 GERCEK — canli kiro2'de kosulur, ISLEM COMMIT EDILIR.
-- Amac: gercek yazimdan ONCE her kisiti (NOT NULL, UNIQUE code, FK parent_id)
-- fiilen sinamak. Prova yazimdan ucuzdur.
\set ON_ERROR_STOP off

SELECT 'ONCE: topic_hierarchy = ' || count(*) FROM topic_hierarchy;

BEGIN;

\copy topic_hierarchy (id, parent_id, code, name_tr, name_en, description, meb_code, osym_relevance, osym_frequency, total_questions, average_difficulty, difficulty_level, subject_area, is_active, level) FROM 'backend/scripts/quality/y11_adim1_konular.csv' WITH (FORMAT csv, HEADER true)

SELECT 'INSERT SONRASI: topic_hierarchy = ' || count(*) || '   (26 bekleniyor: 12 + 14)'
  FROM topic_hierarchy;

-- KAPI 1: kod benzersizligi bozulmadi mi
SELECT 'KAPI-1 mukerrer kod: ' || count(*) || '  (0 olmali)'
  FROM (SELECT code FROM topic_hierarchy GROUP BY code HAVING count(*) > 1) x;

-- KAPI 2: her parent_id gercekten var mi (FK butunlugu)
SELECT 'KAPI-2 yetim parent_id: ' || count(*) || '  (0 olmali)'
  FROM topic_hierarchy c
 WHERE c.parent_id IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM topic_hierarchy p WHERE p.id = c.parent_id);

-- KAPI 3: MAT.TRV'nin ebeveyni CANLI MAT'a mi bagli (remap calisti mi)
SELECT 'KAPI-3 MAT.TRV ebeveyni: ' || coalesce(p.code, '<YOK>')
       || '  (MAT olmali)'
  FROM topic_hierarchy c LEFT JOIN topic_hierarchy p ON p.id = c.parent_id
 WHERE c.code = 'MAT.TRV';

-- KAPI 4: yeni konularin hepsi eklendi mi
SELECT 'KAPI-4 eklenen 14 kodun bulunani: ' || count(*) || '  (14 olmali)'
  FROM topic_hierarchy
 WHERE code IN ('FEN','TYT-KIM-01','TYT-KIM-09','TYT-KIM-10','TYT-KIM-11',
                'TYT-KIM-12','KIM.ASI','KIM.DEN','KIM.ORG','KIM.TER','MAT.TRV',
                'TYT-KIM-02','TYT-KIM-03','TYT-KIM-04');

COMMIT;

SELECT 'COMMIT SONRASI: topic_hierarchy = ' || count(*) || '   (26 olmali)'
  FROM topic_hierarchy;
