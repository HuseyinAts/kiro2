-- Backfill: student_answers -> kiro2_learning_events
-- student_id varchar -> uuid cast eklendi

INSERT INTO kiro2_learning_events (
    id, user_id, question_id, session_id,
    event_type, is_correct, theta_after, response_ms, occurred_at
)
SELECT
    gen_random_uuid(),
    es.student_id::uuid,
    sa.question_id::uuid,
    NULL,
    'exam_answer',
    sa.is_correct,
    NULL,
    (sa.response_time_seconds * 1000)::int,
    sa.answered_at
FROM student_answers sa
JOIN exam_sessions es ON es.id = sa.exam_session_id
WHERE sa.is_correct IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM kiro2_learning_events le
      WHERE le.question_id::text = sa.question_id
        AND le.user_id::text = es.student_id
        AND le.event_type = 'exam_answer'
  );

SELECT event_type, COUNT(*) AS adet,
       COUNT(*) FILTER (WHERE is_correct=TRUE)  AS dogru,
       COUNT(*) FILTER (WHERE is_correct=FALSE) AS yanlis
FROM kiro2_learning_events
GROUP BY event_type;
