-- v_response_log güncelle: synthetic_response + exam_answer event tiplerini dahil et
-- Kalibrasyon pipeline tüm kaynaklardan beslenecek

CREATE OR REPLACE VIEW v_response_log AS

-- CAT yanıtları
SELECT
    user_id::text        AS student_id,
    question_id::text    AS question_id,
    is_correct,
    response_ms::float / 1000.0 AS response_time_sec,
    occurred_at          AS answered_at,
    'cat'                AS source
FROM kiro2_learning_events
WHERE event_type = 'cat_answer'
  AND is_correct IS NOT NULL

UNION ALL

-- Sınav yanıtları (learning_events'e köprülenmiş)
SELECT
    user_id::text        AS student_id,
    question_id::text    AS question_id,
    is_correct,
    response_ms::float / 1000.0 AS response_time_sec,
    occurred_at          AS answered_at,
    'exam'               AS source
FROM kiro2_learning_events
WHERE event_type = 'exam_answer'
  AND is_correct IS NOT NULL

UNION ALL

-- Sentetik yanıtlar (pipeline testi için)
SELECT
    user_id::text        AS student_id,
    question_id::text    AS question_id,
    is_correct,
    response_ms::float / 1000.0 AS response_time_sec,
    occurred_at          AS answered_at,
    'synthetic'          AS source
FROM kiro2_learning_events
WHERE event_type = 'synthetic_response'
  AND is_correct IS NOT NULL;

-- Kalibrasyon adayları: >=50 yanıtı olan sorular (tüm kaynaklardan)
CREATE OR REPLACE VIEW v_calibration_candidates AS
SELECT
    question_id,
    COUNT(*)                                           AS n_responses,
    ROUND(AVG(is_correct::int)::numeric, 4)            AS p_value,
    SUM(CASE WHEN source='cat'       THEN 1 ELSE 0 END) AS cat_responses,
    SUM(CASE WHEN source='exam'      THEN 1 ELSE 0 END) AS exam_responses,
    SUM(CASE WHEN source='synthetic' THEN 1 ELSE 0 END) AS synthetic_responses
FROM v_response_log
GROUP BY question_id
HAVING COUNT(*) >= 50
ORDER BY n_responses DESC;

-- Kontrol
SELECT source, COUNT(*) FROM v_response_log GROUP BY source;
SELECT COUNT(*) AS kalibre_adayi FROM v_calibration_candidates;
