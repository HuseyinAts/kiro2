\encoding UTF8
-- Y11 — cop KITAP DUZEYINDE mi yogunlasiyor? (kiro2_temp, kapi esdegeri 34.982)
-- Y12'nin dogrulanmis 6 kurali (0 dogrulanmis FP) kitap basina uygulanir.
WITH kapi AS (
    SELECT id, source_book, question_text, option_a, option_b, option_c,
           option_d, option_e, correct_answer
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
),
b AS (
    SELECT source_book,
      ((SELECT count(DISTINCT lower(btrim(regexp_replace(x,'^\s*[A-Ea-e][).]\s*',''))))
          FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
         WHERE x IS NOT NULL AND btrim(x)<>'') < 5
       OR ((SELECT count(*) FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
              WHERE btrim(x) ~ '^1[0]*$')=5
           AND (SELECT count(DISTINCT length(btrim(x)))
                  FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x)=5)
       OR (question_text LIKE '%A)%' AND question_text LIKE '%B)%' AND question_text LIKE '%C)%')
       OR (length(question_text) < 40)
       OR (correct_answer IS NULL OR correct_answer NOT IN ('A','B','C','D','E')
           OR btrim(coalesce(CASE correct_answer WHEN 'A' THEN option_a WHEN 'B' THEN option_b
                WHEN 'C' THEN option_c WHEN 'D' THEN option_d
                WHEN 'E' THEN option_e END,''))='')
       OR ((SELECT count(*) FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
              WHERE length(btrim(x))>=15 AND position(btrim(x) in question_text)>0) >= 3)
      ) AS bayrak
    FROM kapi
),
kitap AS (
    SELECT source_book, count(*) AS n,
           count(*) FILTER (WHERE bayrak) AS bayrakli,
           round(100.0*count(*) FILTER (WHERE bayrak)/count(*), 2) AS oran
    FROM b GROUP BY source_book
)
SELECT '== EVREN ==  kitap=' || count(*) || '  soru=' || sum(n)
       || '  bayrakli=' || sum(bayrakli)
       || '  genel_oran=%' || round(100.0*sum(bayrakli)/sum(n), 2) FROM kitap
UNION ALL SELECT ''
UNION ALL SELECT '== YOGUNLASMA =='
UNION ALL SELECT '  bayrak orani >%20 olan kitap: ' || count(*) || ' kitap / '
       || sum(n) || ' soru / ' || sum(bayrakli) || ' bayrak'
  FROM kitap WHERE oran > 20
UNION ALL SELECT '  bayrak orani >%10 olan kitap: ' || count(*) || ' kitap / '
       || sum(n) || ' soru / ' || sum(bayrakli) || ' bayrak'
  FROM kitap WHERE oran > 10
UNION ALL SELECT '  bayrak orani <=%3 olan kitap: ' || count(*) || ' kitap / '
       || sum(n) || ' soru / ' || sum(bayrakli) || ' bayrak'
  FROM kitap WHERE oran <= 3
UNION ALL SELECT ''
UNION ALL SELECT '== EN KIRLI 15 KITAP =='
UNION ALL SELECT '  %' || lpad(oran::text, 6) || '  n=' || lpad(n::text, 5)
                 || '  ' || left(source_book, 62)
  FROM kitap WHERE n >= 20 ORDER BY 1;
