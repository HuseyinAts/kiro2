-- migrations/create_response_log_view.sql
-- Birleşik yanıt logu: kiro2_learning_events + student_answers
-- IRT kalibrasyon pipeline bu view'u kullanır

CREATE OR REPLACE VIEW v_response_log AS

-- CAT yanıtları
SELECT
    user_id::text          AS student_id,
    question_id::text      AS question_id,
    is_correct,
    response_ms::float / 1000.0 AS response_time_sec,
    occurred_at            AS answered_at,
    'cat'                  AS source
FROM kiro2_learning_events
WHERE event_type = 'cat_answer'
  AND is_correct IS NOT NULL

UNION ALL

-- Sınav yanıtları
SELECT
    es.student_id::text    AS student_id,
    sa.question_id::text   AS question_id,
    sa.is_correct,
    sa.response_time_seconds AS response_time_sec,
    sa.answered_at,
    'exam'                 AS source
FROM student_answers sa
JOIN exam_sessions es ON es.id = sa.exam_session_id
WHERE sa.is_correct IS NOT NULL;

-- Kaç yanıt var?
-- SELECT source, COUNT(*) FROM v_response_log GROUP BY source;

-- Kalibrasyon adayları: >=50 yanıtı olan sorular
CREATE OR REPLACE VIEW v_calibration_candidates AS
SELECT
    question_id,
    COUNT(*)                           AS n_responses,
    ROUND(AVG(is_correct::int)::numeric, 4) AS p_value,
    SUM(CASE WHEN source='cat' THEN 1 ELSE 0 END)  AS cat_responses,
    SUM(CASE WHEN source='exam' THEN 1 ELSE 0 END) AS exam_responses
FROM v_response_log
GROUP BY question_id
HAVING COUNT(*) >= 50
ORDER BY n_responses DESC;
