\encoding UTF8
-- "118 celiski" iddiasini CURUT: ayni govde + farkli anahtar tasiyan bir grubu
-- SIKLARIYLA birlikte goster. Hipotez: sikler karistirilmis, dogru HARF degismis
-- -> celiski YOK, benim olcum aletim govdeye bakip sikleri gormemis.
WITH kapi AS (
    SELECT id, correct_answer, question_text, option_a, option_b, option_c,
           option_d, option_e,
           lower(regexp_replace(btrim(question_text), '\s+', ' ', 'g')) AS norm
    FROM question_bank
    WHERE quality_review_status IN ('human_verified','auto_judged_high')
      AND is_active = true
),
hedef AS (
    SELECT norm FROM kapi
    WHERE norm LIKE '%bir kenar uzunluğu 10 cm%'
    GROUP BY norm HAVING count(*) > 1 AND count(DISTINCT correct_answer) > 1
    LIMIT 1
)
SELECT '--- id=' || k.id || '   DB_ANAHTAR=' || k.correct_answer
       || E'\n  A) ' || coalesce(k.option_a,'-') || '   B) ' || coalesce(k.option_b,'-')
       || '   C) ' || coalesce(k.option_c,'-') || '   D) ' || coalesce(k.option_d,'-')
       || '   E) ' || coalesce(k.option_e,'-')
       || E'\n  -> DB anahtarinin isaret ettigi DEGER: '
       || coalesce(CASE k.correct_answer
            WHEN 'A' THEN k.option_a WHEN 'B' THEN k.option_b WHEN 'C' THEN k.option_c
            WHEN 'D' THEN k.option_d WHEN 'E' THEN k.option_e END, '<BOS>')
FROM kapi k JOIN hedef h ON h.norm = k.norm
ORDER BY k.id;
