BEGIN;

CREATE TEMP TABLE has_response AS
  SELECT DISTINCT question_id::text AS qid
  FROM kiro2_learning_events WHERE is_correct IS NOT NULL
  UNION
  SELECT DISTINCT question_id::text
  FROM student_answers WHERE is_correct IS NOT NULL;

CREATE INDEX ON has_response(qid);

UPDATE question_bank
SET is_calibrated=FALSE,
    calibration_sample_size=0,
    calibration_quality_score=0
WHERE is_calibrated=TRUE
  AND id::text NOT IN (SELECT qid FROM has_response);

COMMIT;

SELECT
  'After reset' AS label,
  COUNT(*) FILTER (WHERE is_calibrated=TRUE)  AS still_true,
  COUNT(*) FILTER (WHERE is_calibrated=FALSE) AS now_false
FROM question_bank WHERE is_active=TRUE;
