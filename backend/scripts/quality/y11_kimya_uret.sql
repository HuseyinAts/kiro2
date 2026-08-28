\encoding UTF8
-- Y11 tam tur — KIMYA (kiro2_temp kapi esdegeri, 4.419 soru).
-- Deterministik sira: md5(id || 'y11kimya'). Cikti KOR: cevap anahtari YAZILMAZ.
SELECT '--- [KIMYA-' || sira || ']  id=' || id
       || '  sinav=' || coalesce(exam_type,'-')
       || E'\nSORU: ' || question_text
       || E'\n  A) ' || coalesce(option_a,'<BOS>')
       || E'\n  B) ' || coalesce(option_b,'<BOS>')
       || E'\n  C) ' || coalesce(option_c,'<BOS>')
       || E'\n  D) ' || coalesce(option_d,'<BOS>')
       || E'\n  E) ' || coalesce(option_e,'<BOS>')
       || E'\n'
FROM (
    SELECT id, exam_type, question_text, option_a, option_b, option_c,
           option_d, option_e,
           row_number() OVER (ORDER BY md5(id::text || 'y11kimya')) AS sira
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
      AND subject_area = 'KIMYA'
) t
ORDER BY sira;
