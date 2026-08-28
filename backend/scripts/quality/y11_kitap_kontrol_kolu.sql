\encoding UTF8
-- KONTROL KOLU: mekanik kitap siralamasi, INSAN yargisiyla bozuk bulunan
-- kitaplari yakaliyor mu? Yakalamiyorsa "kitap duzeyinde eleme" hipotezi CURUR.
WITH kapi AS (
    SELECT source_book, question_text, option_a, option_b, option_c,
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
       OR (question_text LIKE '%A)%' AND question_text LIKE '%B)%' AND question_text LIKE '%C)%')
       OR (length(question_text) < 40)
       OR (correct_answer IS NULL OR correct_answer NOT IN ('A','B','C','D','E'))
       OR ((SELECT count(*) FROM unnest(ARRAY[option_a,option_b,option_c,option_d,option_e]) x
              WHERE length(btrim(x))>=15 AND position(btrim(x) in question_text)>0) >= 3)
      ) AS f
    FROM kapi
),
k AS (
    SELECT source_book, count(*) AS n, count(*) FILTER (WHERE f) AS bay,
           round(100.0*count(*) FILTER (WHERE f)/count(*), 1) AS oran
    FROM b GROUP BY source_book
),
r AS (SELECT *, rank() OVER (ORDER BY oran DESC) AS sira,
             (SELECT count(*) FROM k) AS toplam FROM k)
SELECT '== KONTROL KOLU: insan-bozuk bulunan kitaplarin MEKANIK sirasi =='
UNION ALL
SELECT '  %' || oran || '   n=' || n || '   sira ' || sira || '/' || toplam
       || '   ' || left(source_book, 48)
  FROM r
 WHERE source_book LIKE 'Neofizik%'
    OR source_book LIKE 'Esen Aps Tyt Ayt Tarih%'
    OR source_book LIKE 'Aramot Tyt 2023 Fen%'
    OR source_book LIKE 'Aktif Ogrenme 0 Baslayanlara Kimya%'
    OR source_book LIKE 'Bilgi Sarmal%2024%Tyt%Matematik%'
UNION ALL SELECT ''
UNION ALL SELECT '== YOGUNLASMA OZETI =='
UNION ALL SELECT '  bayrak >%20 : ' || count(*) || ' kitap / ' || sum(n) || ' soru' FROM k WHERE oran > 20
UNION ALL SELECT '  bayrak >%10 : ' || count(*) || ' kitap / ' || sum(n) || ' soru' FROM k WHERE oran > 10
UNION ALL SELECT '  bayrak <=%3 : ' || count(*) || ' kitap / ' || sum(n) || ' soru' FROM k WHERE oran <= 3
UNION ALL SELECT '  TOPLAM      : ' || count(*) || ' kitap / ' || sum(n) || ' soru / genel bayrak %'
       || round(100.0*sum(bay)/sum(n), 2) FROM k;
