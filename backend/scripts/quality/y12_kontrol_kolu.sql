\encoding UTF8
-- Y12 KONTROL KOLU (duzeltilmis kurallar) — kiro2_temp, pre-split sema, ESDEGER sorgu.
WITH kapi AS (SELECT * FROM question_bank
  WHERE quality_review_status IN ('human_verified','auto_judged_high') AND is_active = true),
b AS (SELECT
  (SELECT count(DISTINCT lower(btrim(regexp_replace(x,'^\s*[A-Ea-e][).]\s*',''))))
     FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
    WHERE x IS NOT NULL AND btrim(x)<>'') < 5 AS r1b,
  ((SELECT count(*) FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
      WHERE btrim(x) ~ '^1[0]*$')=5 AND (SELECT count(DISTINCT length(btrim(x)))
      FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x)=5) AS r2,
  (question_text LIKE '%A)%' AND question_text LIKE '%B)%' AND question_text LIKE '%C)%') AS r3,
  (length(question_text) < 40) AS r4,
  (correct_answer IS NULL OR correct_answer NOT IN ('A','B','C','D','E')
   OR btrim(coalesce(CASE correct_answer WHEN 'A' THEN option_a WHEN 'B' THEN option_b
        WHEN 'C' THEN option_c WHEN 'D' THEN option_d WHEN 'E' THEN option_e END,''))='') AS r5,
  ((SELECT count(*) FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
     WHERE length(btrim(x))>=15 AND position(btrim(x) in question_text)>0) >= 3) AS r6
  FROM kapi)
SELECT 'I1 pipeline_metadata distinct <>1 ve >1  : ' ||
       (SELECT count(DISTINCT pipeline_metadata::text) FROM kapi) ||
       CASE WHEN (SELECT count(DISTINCT pipeline_metadata::text) FROM kapi) > 1
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'I2 source_book orani >=0.50              : ' ||
       round((SELECT count(source_book)::numeric/nullif(count(*),0) FROM kapi),4) ||
       CASE WHEN (SELECT count(source_book)::numeric/nullif(count(*),0) FROM kapi) >= 0.50
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'I3 primary_topic_id distinct >1          : ' ||
       (SELECT count(DISTINCT primary_topic_id) FROM kapi) ||
       CASE WHEN (SELECT count(DISTINCT primary_topic_id) FROM kapi) > 1
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'I4 reviewed_at distinct <> 1             : ' ||
       (SELECT count(DISTINCT reviewed_at) FROM kapi) ||
       CASE WHEN (SELECT count(DISTINCT reviewed_at) FROM kapi) <> 1
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'I5 zorluk>1 ve irt>1                     : ' ||
       (SELECT count(DISTINCT difficulty_level) FROM kapi) || ' / ' ||
       (SELECT count(DISTINCT irt_difficulty) FROM kapi) ||
       CASE WHEN (SELECT count(DISTINCT difficulty_level) FROM kapi) > 1
             AND (SELECT count(DISTINCT irt_difficulty) FROM kapi) > 1
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'K2 birlesim bayrak orani <=0.05          : ' ||
       (SELECT round(count(*) FILTER (WHERE r1b OR r2 OR r3 OR r4 OR r5 OR r6)::numeric
                     /nullif(count(*),0),4) FROM b) ||
       CASE WHEN (SELECT count(*) FILTER (WHERE r1b OR r2 OR r3 OR r4 OR r5 OR r6)::numeric
                     /nullif(count(*),0) FROM b) <= 0.05
            THEN '  -> GECTI' ELSE '  -> DUSTU' END
UNION ALL SELECT 'K2 gecersiz anahtar (R5) = 0             : ' ||
       (SELECT count(*) FILTER (WHERE r5) FROM b) ||
       CASE WHEN (SELECT count(*) FILTER (WHERE r5) FROM b) = 0
            THEN '  -> GECTI' ELSE '  -> DUSTU' END;
