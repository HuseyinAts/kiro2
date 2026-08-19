\encoding UTF8
-- KUSUR KONTROLU: mukerrer tespiti yalniz question_text'e bakiyordu.
-- Ayni govde + FARKLI SIKLAR olan gruplar "mukerrer" gorunup yanlislikla silinebilir.
-- Bu sorgu govde+SIKLAR birlikte normalize edilince ne degistigini olcer.
WITH kapi AS (
    SELECT id, subject_area, correct_answer, question_text,
           lower(regexp_replace(btrim(question_text), '\s+', ' ', 'g')) AS n_govde,
           lower(regexp_replace(btrim(
               coalesce(option_a,'') || '|' || coalesce(option_b,'') || '|' ||
               coalesce(option_c,'') || '|' || coalesce(option_d,'') || '|' ||
               coalesce(option_e,'')), '\s+', ' ', 'g')) AS n_sik
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
)
SELECT '== YALNIZ GOVDE ile (onceki olcum) =='
UNION ALL SELECT '  benzersiz govde : ' || count(DISTINCT n_govde)
       || '   fazlalik: ' || (count(*) - count(DISTINCT n_govde)) FROM kapi
UNION ALL SELECT ''
UNION ALL SELECT '== GOVDE + SIKLAR birlikte (DOGRU olcum) =='
UNION ALL SELECT '  benzersiz kayit : ' || count(DISTINCT (n_govde || '###' || n_sik))
       || '   fazlalik: ' || (count(*) - count(DISTINCT (n_govde || '###' || n_sik))) FROM kapi
UNION ALL SELECT ''
UNION ALL SELECT '== FARK — "ayni govde, FARKLI sik" (yanlislikla mukerrer sanilan) =='
UNION ALL SELECT '  bu kadar satir YANLIS silinecekti: '
       || ((SELECT count(*) - count(DISTINCT n_govde) FROM kapi)
         - (SELECT count(*) - count(DISTINCT (n_govde || '###' || n_sik)) FROM kapi))
UNION ALL SELECT ''
UNION ALL SELECT '== GERCEK MUKERRER (govde+sik ayni) sinif dagilimi =='
UNION ALL SELECT '  grup=' || n || ' olan grup sayisi: ' || adet FROM (
    SELECT n, count(*) AS adet FROM (
        SELECT n_govde || '###' || n_sik AS anahtar, count(*) AS n
        FROM kapi GROUP BY 1 HAVING count(*) > 1
    ) g GROUP BY n ORDER BY n
) x
UNION ALL SELECT ''
UNION ALL SELECT '  ⚠ gercek mukerrerlerde FARKLI anahtar tasiyan grup: ' || count(*) FROM (
    SELECT n_govde || '###' || n_sik AS a FROM kapi
    GROUP BY 1 HAVING count(*) > 1 AND count(DISTINCT correct_answer) > 1
) z;
