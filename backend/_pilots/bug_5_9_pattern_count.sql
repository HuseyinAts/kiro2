-- Bug #5+#9 pattern counts for auto_judged_high pool
\echo === Truncation (cut-off) patterns ===
SELECT
  COUNT(*) AS total_pool,
  COUNT(*) FILTER (WHERE question_text ~ '[^\.\?\!\»"''\)\]]\s*$') AS truncation_no_terminal,
  COUNT(*) FILTER (WHERE LENGTH(question_text) < 30) AS too_short_30,
  COUNT(*) FILTER (WHERE LENGTH(question_text) < 50) AS too_short_50,
  COUNT(*) FILTER (WHERE question_text !~ '\?') AS no_question_mark,
  COUNT(*) FILTER (WHERE question_text ~ '(.)\1{6,}') AS repeated_char_7plus,
  COUNT(*) FILTER (WHERE question_text ~ '\.\.\.\s*$') AS ends_with_ellipsis
FROM question_bank
WHERE is_active=true AND quality_review_status='auto_judged_high';

\echo
\echo === Sample truncated rows ===
SELECT id, source_book, LEFT(question_text, 120) AS preview, LENGTH(question_text) AS len
FROM question_bank
WHERE is_active=true AND quality_review_status='auto_judged_high'
  AND question_text ~ '[^\.\?\!\»"''\)\]]\s*$'
ORDER BY md5(id::text)
LIMIT 5;

\echo
\echo === Sample short rows ===
SELECT id, source_book, question_text, LENGTH(question_text) AS len
FROM question_bank
WHERE is_active=true AND quality_review_status='auto_judged_high'
  AND LENGTH(question_text) < 50
ORDER BY md5(id::text)
LIMIT 5;
