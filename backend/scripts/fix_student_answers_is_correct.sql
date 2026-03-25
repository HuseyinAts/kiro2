-- student_answers.is_correct güncelle
-- correct_answer ile selected_answer karşılaştır

UPDATE student_answers sa
SET is_correct = (
    SELECT sa.selected_answer = qb.correct_answer
    FROM question_bank qb
    WHERE qb.id::text = sa.question_id
    LIMIT 1
)
WHERE sa.is_correct IS NULL
  AND sa.selected_answer IS NOT NULL;

SELECT
  is_correct,
  COUNT(*)
FROM student_answers
GROUP BY is_correct;
