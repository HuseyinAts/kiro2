\echo === R5a sample (repeated_char 7+) ===
SELECT id, source_book, LEFT(question_text, 200) AS preview
FROM question_bank
WHERE is_active=true AND quality_review_status='auto_judged_high'
  AND question_text ~ '(.)\1{6,}'
ORDER BY md5(id::text)
LIMIT 8;

\echo
\echo === R5b sample (ends_with_ellipsis) ===
SELECT id, source_book, LEFT(question_text, 200) AS preview
FROM question_bank
WHERE is_active=true AND quality_review_status='auto_judged_high'
  AND question_text ~ '\.\.\.\s*$'
ORDER BY md5(id::text)
LIMIT 8;
