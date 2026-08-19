\encoding UTF8
-- Y11 sayisal-ders yargi turu — MALIYET + KESINLIK pilotu (240 soru).
-- Evren: kiro2_temp kapi esdegeri, yalniz MATEMATIK/GEOMETRI/KIMYA/FIZIK = 24.954
-- Tahsis orantili: MAT 136 / KIM 42 / FIZ 33 / GEO 29 = 240
-- Salt 'y11pilot' — onceki iki cekimin (y12salt, y11s232) tuzlarindan FARKLI.
-- Cikti KOR: cevap anahtari YAZILMAZ.
WITH kapi AS (
    SELECT id, subject_area, exam_type, source_book, question_text,
           option_a, option_b, option_c, option_d, option_e
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
      AND subject_area IN ('MATEMATIK','GEOMETRI','KIMYA','FIZIK')
),
kota(ders, n) AS (VALUES
    ('MATEMATIK',136), ('KIMYA',42), ('FIZIK',33), ('GEOMETRI',29)
),
sirali AS (
    SELECT k.*, row_number() OVER (PARTITION BY k.subject_area
                                   ORDER BY md5(k.id::text || 'y11pilot')) AS sira
    FROM kapi k
)
SELECT '--- [' || s.subject_area || '-' || s.sira || ']  id=' || s.id
       || '  sinav=' || coalesce(s.exam_type,'-')
       || E'\nSORU: ' || s.question_text
       || E'\n  A) ' || coalesce(s.option_a,'<BOS>')
       || E'\n  B) ' || coalesce(s.option_b,'<BOS>')
       || E'\n  C) ' || coalesce(s.option_c,'<BOS>')
       || E'\n  D) ' || coalesce(s.option_d,'<BOS>')
       || E'\n  E) ' || coalesce(s.option_e,'<BOS>')
       || E'\n'
FROM sirali s JOIN kota q ON q.ders = s.subject_area
WHERE s.sira <= q.n
ORDER BY s.subject_area, s.sira;
