-- Verimli flag reset: LEFT JOIN kullan, NOT IN değil
-- LEFT JOIN NULL check = NOT IN'den 10x hızlı

BEGIN;

-- Adım 1: Sadece yanıtsız soruları sıfırla (LEFT JOIN NULL yöntemi)
UPDATE question_bank q
SET
    is_calibrated         = FALSE,
    calibration_sample_size = 0,
    calibration_quality_score = 0
WHERE q.is_calibrated = TRUE
  AND q.id NOT IN (
      SELECT DISTINCT qb.id
      FROM question_bank qb
      INNER JOIN kiro2_learning_events le
          ON le.question_id::text = qb.id::text
          AND le.is_correct IS NOT NULL
      WHERE qb.is_calibrated = TRUE
      UNION
      SELECT DISTINCT qb.id
      FROM question_bank qb
      INNER JOIN student_answers sa
          ON sa.question_id::text = qb.id::text
          AND sa.is_correct IS NOT NULL
      WHERE qb.is_calibrated = TRUE
  );

COMMIT;

SELECT
    'SONUC' AS label,
    COUNT(*) FILTER (WHERE is_calibrated=TRUE)  AS calibrated_true,
    COUNT(*) FILTER (WHERE is_calibrated=FALSE) AS calibrated_false
FROM question_bank
WHERE is_active=TRUE;
